from io import BytesIO
import logging
import random
import string
import threading
import time

from captcha.image import ImageCaptcha

from config import bot, captcha_properties

logger = logging.getLogger(__name__)

CAPTCHA_LOCK = threading.Lock()
CAPTCHA_USERS = {}
TIMER_THREAD = None
TIMER_THREAD_RUNNING = False


def generate_captcha_text(length=None):
    length = length or captcha_properties["length"]
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_captcha_image(text):
    img = ImageCaptcha()
    return BytesIO(img.generate(text).read())


def build_caption(time_left, failed_attempts):
    total_time = captcha_properties["timer"]
    attempts_left = max(0, captcha_properties["attempts"] - failed_attempts)
    elapsed = total_time - time_left
    bar_len = captcha_properties["bar_length"]
    filled = min(bar_len, int((elapsed / total_time) * bar_len))
    bar = "[" + "=" * filled + ">" + " " * (bar_len - filled - 1) + "]"
    pct = int((elapsed / total_time) * 100)
    return (
        f"\U0001f9e9 CAPTCHA Verification\n"
        f"{bar} {pct}% | {time_left}s\n"
        f"Attempts left: {attempts_left}"
    )


def update_message(user_id):
    with CAPTCHA_LOCK:
        if user_id not in CAPTCHA_USERS:
            return
        user = CAPTCHA_USERS[user_id]

    caption = build_caption(user["time_left"], user["failed_attempts"])
    with CAPTCHA_LOCK:
        if user["message_id"] is None:  # greet msg
            msg = bot.send_photo(user["chat_id"], photo=user["image"], caption=caption)
            if user_id in CAPTCHA_USERS:
                CAPTCHA_USERS[user_id]["message_id"] = msg.message_id
        else:
            bot.edit_message_caption(
                chat_id=user["chat_id"], message_id=user["message_id"], caption=caption
            )


def fail_user(user_id, reason):
    with CAPTCHA_LOCK:
        if user_id not in CAPTCHA_USERS:
            return
        user = CAPTCHA_USERS.pop(user_id)

    logger.info("Failing user %s in chat %s: %s", user_id, user["chat_id"], reason)
    final_cap = (
        build_caption(user["time_left"], user["failed_attempts"]) + f"\n❌ {reason}"
    )
    if user["message_id"] is not None:
        bot.edit_message_caption(
            chat_id=user["chat_id"], message_id=user["message_id"], caption=final_cap
        )
    bot.kick_chat_member(user["chat_id"], user_id)


def pass_user(user_id, user_input):
    with CAPTCHA_LOCK:
        if user_id not in CAPTCHA_USERS:
            return
        user = CAPTCHA_USERS.pop(user_id)

    bot.send_message(user["chat_id"], "✅ You passed!")
    bot.delete_message(user["chat_id"], user["message_id"])
    logger.info(
        "User %s passed captcha in chat %s, answer='%s'",
        user_id,
        user["chat_id"],
        user_input,
    )


def on_failed_attempt(user_id, user_input):
    with CAPTCHA_LOCK:
        if user_id not in CAPTCHA_USERS:
            return
        user = CAPTCHA_USERS[user_id]
        user["failed_attempts"] += 1
        attempts_used = user["failed_attempts"]

    logger.info(
        "User %s attempt failed: got '%s', expected '%s'",
        user_id,
        user_input,
        user["answer"],
    )
    if attempts_used >= captcha_properties["attempts"]:
        fail_user(user_id, reason="Max attempts used")
    else:
        update_message(user_id)


def timer_loop():
    global TIMER_THREAD_RUNNING
    logger.info("Timer thread started.")
    with CAPTCHA_LOCK:
        TIMER_THREAD_RUNNING = True

    while True:
        time.sleep(1)

        remove_list = []
        update_list = []

        with CAPTCHA_LOCK:
            if not CAPTCHA_USERS:
                logger.info("No users, stopping timer thread")
                TIMER_THREAD_RUNNING = False
                return

            for uid, data in list(CAPTCHA_USERS.items()):
                if data["time_left"] > 0:
                    data["time_left"] -= 1
                    if (
                        data["time_left"] > 0  # will be removed on the next tick
                        and data["time_left"] % captcha_properties["update_freq"] == 0
                    ):
                        update_list.append(uid)
                else:
                    remove_list.append(uid)

        for uid in remove_list:
            fail_user(uid, reason="Time is up")

        for uid in update_list:
            update_message(uid)


def start_timer_thread_if_needed():
    global TIMER_THREAD
    with CAPTCHA_LOCK:
        if not CAPTCHA_USERS:
            return
        if not TIMER_THREAD_RUNNING:
            TIMER_THREAD = threading.Thread(target=timer_loop, daemon=True)
            TIMER_THREAD.start()


def handle_new_user(message):
    # TODO
    # if not getattr(message, "new_chat_members", None):
    #     return
    logger.info("USERS ARE: { }", __import__("pprint").pprint(CAPTCHA_USERS))
    for new_member in message.new_chat_members:
        user_id = new_member.id
        chat_id = message.chat.id
        captcha_text = generate_captcha_text()
        img = generate_captcha_image(captcha_text)
        with CAPTCHA_LOCK:
            CAPTCHA_USERS[user_id] = {
                "chat_id": chat_id,
                "message_id": None,  # set in the update_message
                "failed_attempts": 0,
                "time_left": captcha_properties["timer"],
                "image": img,
                "answer": captcha_text,
            }
            logger.info(
                "User %s entered the chat, captcha text: %s", user_id, captcha_text
            )
        update_message(user_id)
    start_timer_thread_if_needed()


def handle_verify_captcha(message):
    user_id = message.from_user.id
    with CAPTCHA_LOCK:  # ideally never triggers?
        if user_id not in CAPTCHA_USERS:
            return
        user = CAPTCHA_USERS[user_id]
    user_input = message.text.strip().lower()
    if user_input == user["answer"].lower():
        pass_user(user_id, user_input)
    else:
        bot.delete_message(message.chat.id, message.message_id)
        on_failed_attempt(user_id, user_input)


def handle_user_left(message):
    if not getattr(message, "left_chat_member", None):
        return
    user_id = message.left_chat_member.id
    # TODO: delete the "left-over" message
    with CAPTCHA_LOCK:
        if user_id in CAPTCHA_USERS:
            CAPTCHA_USERS.pop(user_id)
            logger.info(
                "User %s left chat mid-captcha, removed from dictionary.", user_id
            )

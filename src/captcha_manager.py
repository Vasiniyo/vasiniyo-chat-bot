import logging
import random
import string
from io import BytesIO

from captcha.image import ImageCaptcha
from config import bot, captcha_properties
from event_queue import add_task, cancel_task

logger = logging.getLogger(__name__)
CAPTCHA_USERS = {}


# ==================================== CAPTHA GEN ============================================
def generate_captcha_text(length=None):
    length = length or captcha_properties["length"]
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_captcha_image(text):
    img = ImageCaptcha()
    return BytesIO(img.generate(text).read())


# ==================================== MSG UPDATES ============================================
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


def update_captcha_message(user_id):
    user = CAPTCHA_USERS.get(user_id)
    if not user or user["message_id"] is None:
        logger.info(
            f"Tried UPDATE_CAPTCHA_MESSAGE for the user {user_id}, but could not find them"
        )
        return

    user["time_left"] = max(0, user["time_left"] - captcha_properties["update_freq"])
    new_caption = build_caption(user["time_left"], user["failed_attempts"])

    if new_caption == user.get("last_caption"):
        logger.debug(f"Skipping update: caption unchanged for user {user_id}")
        return

    # WARN if buttons are added to the message, this
    # (probably) should also keep the state of those
    user["last_caption"] = new_caption
    bot.edit_message_caption(
        chat_id=user["chat_id"], message_id=user["message_id"], caption=new_caption
    )


# ================================= CAPTCHA OUTCOMES =========================================
def fail_user(user_id, reason="Time is up"):
    user = CAPTCHA_USERS.pop(user_id, None)
    if not user:
        logger.info(
            "Tried calling FAIL_USER %s for the reason %s, but counld not find them".format(
                user_id, reason
            )
        )
        return

    logger.info(
        "Failing user %s in chat %s: %s".format(user_id, user["chat_id"], reason)
    )
    caption = (
        build_caption(user["time_left"], user["failed_attempts"]) + f"\n❌ {reason}"
    )
    if user["message_id"]:
        bot.edit_message_caption(
            chat_id=user["chat_id"], message_id=user["message_id"], caption=caption
        )
    # TODO: save check for if_member
    bot.kick_chat_member(user["chat_id"], user_id)


def pass_user(user_id, user_input):
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            "Tried calling PASS_USER %s for the reason %s, but counld not find them".format(
                user_id, reason
            )
        )
        return

    task_id = user.get("eq_key")
    CAPTCHA_USERS.pop(user_id, None)
    # TODO: queue this for deletion (and user's final answer')
    bot.send_message(user["chat_id"], "✅ You passed!")
    if user["message_id"]:
        bot.delete_message(user["chat_id"], user["message_id"])
    if task_id:
        cancel_task(task_id)

    logger.info(
        "User %s passed captcha in chat %s, answer='%s'".format(
            user_id, user["chat_id"], user_input
        )
    )


def on_failed_attempt(user_id, user_input):
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            f"Tried to issue FAILED_ATTEMPT for the user {user_id}, but could not find them"
        )
        return

    user["failed_attempts"] += 1
    logger.info(
        "User %s attempt failed, got '%s', expected='%s'".format(
            user_id, user_input, user["answer"]
        )
    )
    if user["failed_attempts"] >= captcha_properties["attempts"]:
        fail_user(user_id, reason="Max attempts used")
    else:
        update_captcha_message(user_id)


# ================================= HANDLERS =========================================
def handle_new_user(message):
    if not getattr(message, "new_chat_members", None):
        return

    for member in message.new_chat_members:
        user_id = member.id
        chat_id = message.chat.id

        text = generate_captcha_text()
        image = generate_captcha_image(text)

        CAPTCHA_USERS[user_id] = {
            "chat_id": chat_id,
            "eq_key": None,  # to be filled later (down below)
            "message_id": None,  # to be filled when the message is isses
            "failed_attempts": 0,
            "time_left": captcha_properties["timer"],
            "image": image,
            "answer": text,
        }

        send_initial_captcha(user_id)
        eq_key = queue_captcha_updates(user_id)
        CAPTCHA_USERS[user_id]["eq_key"] = eq_key

        logger.info("New user %s got capcha text %s".format(user_id, text))


def handle_verify_captcha(message):
    user_id = message.from_user.id
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            f"Tried HANDLE_VERIFY_CAPTCHA for the user {user_id}, but could not find them"
        )
        return

    user_input = message.text.strip().lower()
    if user_input == user["answer"].lower():
        bot.delete_message(message.chat.id, message.message_id)
        pass_user(user_id, user_input)
    else:
        bot.delete_message(message.chat.id, message.message_id)
        on_failed_attempt(user_id, user_input)


def handle_user_left(message):
    if not getattr(message, "left_chat_member", None):
        return

    logger.info("User left mid-captcha, processing...")
    user_id = message.left_chat_member.id
    user = CAPTCHA_USERS.pop(user_id, None)
    logger.info(f"\t{user_id}, {user}")
    if user:
        eq_key = user.get("eq_key")
        if eq_key:
            cancel_task(eq_key)
        logger.info(
            f"User {user_id} left mid-captcha. Cancelled scheduled CAPTCHA task."
        )


# ================================= UTILS =========================================
def queue_captcha_updates(user_id):
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            f"Tried QUEUE_CAPTCHA_UPDATES for the user {user_id}, but could not find them"
        )
        return None

    total = captcha_properties["timer"]
    freq = captcha_properties["update_freq"]
    timestamps = list(range(freq, total + 1, freq))

    task_id = add_task(
        timestamps=timestamps,
        default={"func": update_captcha_message, "args": (user_id,)},
        conditional_funcs={
            "on_success": {"func": fail_user, "args": (user_id, "❌ Time expired")},
            "on_cancel": {"func": fail_user, "args": (user_id, "❌ CAPTCHA cancelled")},
        },
    )
    return task_id


def send_initial_captcha(user_id):
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            f"Tried SEND_INITIAL_CAPTCHA for the user {user_id}, but could not find them"
        )
        return

    caption = build_caption(user["time_left"], user["failed_attempts"])
    msg = bot.send_photo(user["chat_id"], photo=user["image"], caption=caption)
    user["message_id"] = msg.message_id
    user["last_caption"] = caption

from io import BytesIO
import logging
import random
import string

from PIL import Image, ImageOps
from captcha.image import ImageCaptcha
from telebot import types

from config import bot, captcha_properties, greeting_message, phrases
from event_queue import EVENTS, add_task, cancel_task

logger = logging.getLogger(__name__)

CAPTCHA_USERS = {}
GREETING_MESSAGE = greeting_message


# ==================================== CAPTHA GEN ============================================
_raw_banned = captcha_properties["gen"]["banned_symbols"]
_BANNED = {c.lower() for c in _raw_banned} | {c.upper() for c in _raw_banned}
_ALLOWED_SYMBOLS = [
    c for c in (string.ascii_letters + string.digits) if c not in _BANNED
]


def generate_captcha_text():
    """Return a random captcha string of the requested length."""
    length = captcha_properties["gen"]["length"]
    return "".join(random.choices(_ALLOWED_SYMBOLS, k=length))


def generate_captcha_image(text):
    props = captcha_properties["gen"]
    img = ImageCaptcha(fonts=[props["font_path"]])
    img.character_rotate = (-props["max_rotation"], props["max_rotation"])
    image = Image.open(img.generate(text))
    padded = ImageOps.expand(
        image,
        border=(0, props["margins_width"], 0, props["margins_width"]),
        fill=props["margins_color"],
    )

    buf = BytesIO()
    padded.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ==================================== MSG UPDATES ============================================
def build_caption(time_left, failed_attempts):
    total_time = captcha_properties["validate"]["timer"]
    attempts_left = max(0, captcha_properties["validate"]["attempts"] - failed_attempts)
    elapsed = total_time - time_left
    bar_len = captcha_properties["validate"]["bar_length"]
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
            "Tried UPDATE_CAPTCHA_MESSAGE for the user %s, but could not find them",
            user_id,
        )
        return

    update_captcha_time_left(user)
    new_caption = build_caption(user["time_left"], user["failed_attempts"])

    if new_caption == user.get("last_caption"):
        logger.debug("Skipping update: caption unchanged for user %s", user_id)
        return

    # WARN if buttons are added to the message, this
    # (probably) should also keep the state of those
    user["last_caption"] = new_caption
    bot.edit_message_caption(
        chat_id=user["chat_id"],
        message_id=user["message_id"],
        caption=new_caption,
        reply_markup=user["reply_markup"],
    )


# ================================= CAPTCHA OUTCOMES =========================================
def fail_user(user_id, reason="Time is up"):
    user = CAPTCHA_USERS.pop(user_id, None)
    if not user:
        logger.info(
            "Tried calling FAIL_USER %s for the reason %s, but counld not find them",
            user_id,
            reason,
        )
        return

    logger.info("Failing user %s in chat %s: %s", user_id, user["chat_id"], reason)
    user["time_left"] = max(
        0, user["time_left"] - captcha_properties["validate"]["update_freq"]
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
        logger.info("Tried calling PASS_USER %s, but counld not find them", user_id)
        return

    task_id = user.get("eq_key")
    CAPTCHA_USERS.pop(user_id, None)
    # TODO: queue this for deletion (and user's final answer')
    bot.send_message(user["chat_id"], "✅ You passed!")
    bot.send_message(user["chat_id"], GREETING_MESSAGE)

    if user["message_id"]:
        bot.delete_message(user["chat_id"], user["message_id"])
    if task_id:
        cancel_task(task_id, silently=True)

    logger.info(
        "User %s passed captcha in chat %s, answer='%s'",
        user_id,
        user["chat_id"],
        user_input,
    )


def on_failed_attempt(user_id, user_input):
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            "Tried to issue FAILED_ATTEMPT for the user %s, but could not find them",
            user_id,
        )
        return

    user["failed_attempts"] += 1
    logger.info(
        "User %s attempt failed, got '%s', expected='%s'",
        user_id,
        user_input,
        user["answer"],
    )
    if user["failed_attempts"] >= captcha_properties["validate"]["attempts"]:
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

        if member.is_bot:
            logger.info("New user %s is a bot, skipping...", user_id)
            continue

        text = generate_captcha_text()
        image = generate_captcha_image(text)

        CAPTCHA_USERS[user_id] = {
            "chat_id": chat_id,
            "eq_key": None,  # to be filled later (down below)
            "message_id": None,  # to be filled when the message is isses
            "failed_attempts": 0,
            "time_left": captcha_properties["validate"]["timer"],
            "image": image,
            "answer": text,
        }

        send_initial_captcha(user_id)
        eq_key = queue_captcha_updates(user_id)
        CAPTCHA_USERS[user_id]["eq_key"] = eq_key

        logger.info("New user %s got capcha text %s", user_id, text)


def handle_verify_captcha(message):
    user_id = message.from_user.id
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            "Tried HANDLE_VERIFY_CAPTCHA for the user %s, but could not find them",
            user_id,
        )
        return

    bot.delete_message(message.chat.id, message.message_id)

    user_input = (message.text or "").strip().lower() or None
    if user_input == user["answer"].lower():
        pass_user(user_id, user_input)
    else:
        on_failed_attempt(user_id, user_input)


def handle_user_left(message):
    if not getattr(message, "left_chat_member", None):
        return

    logger.info("User left mid-captcha, processing...")
    user_id = message.left_chat_member.id
    user = CAPTCHA_USERS.pop(user_id, None)
    logger.info("\t%s, %s", user_id, user)
    if user:
        eq_key = user.get("eq_key")
        if eq_key:
            cancel_task(eq_key)
        logger.info(
            "User %s left mid-captcha. Cancelled scheduled CAPTCHA task.", user_id
        )


def handle_captcha_button_press(call):
    user_id = call.from_user.id

    if not CAPTCHA_USERS.get(user_id):
        return bot.answer_callback_query(
            call.id, text=phrases("roll_not_yours"), cache_time=3
        )

    regenerate_captcha(user_id)
    bot.answer_callback_query(call.id, cache_time=3)


# ================================= UTILS =========================================
def queue_captcha_updates(user_id):
    user = CAPTCHA_USERS.get(user_id)
    if not user:
        logger.info(
            "Tried QUEUE_CAPTCHA_UPDATES for the user %s, but could not find them",
            user_id,
        )
        return None

    total = user["time_left"]
    freq = captcha_properties["validate"]["update_freq"]
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
            "Tried SEND_INITIAL_CAPTCHA for the user %s, but could not find them",
            user_id,
        )
        return

    button = types.InlineKeyboardButton(
        text="Update captcha 🔄", callback_data="captcha_button"
    )
    markup = types.InlineKeyboardMarkup(keyboard=[[button]])
    caption = build_caption(user["time_left"], user["failed_attempts"])
    msg = bot.send_photo(
        user["chat_id"], photo=user["image"], caption=caption, reply_markup=markup
    )
    user["message_id"] = msg.message_id
    user["last_caption"] = caption
    user["reply_markup"] = markup


def regenerate_captcha(user_id):
    captcha = CAPTCHA_USERS[user_id]
    text = generate_captcha_text()
    image = generate_captcha_image(text)

    new_data = {"image": image, "answer": text}

    captcha.update(new_data)
    update_captcha_time_left(captcha)
    caption = build_caption(captcha["time_left"], captcha["failed_attempts"])

    bot.edit_message_media(
        media=types.InputMediaPhoto(captcha["image"], caption, "HTML"),
        chat_id=captcha["chat_id"],
        message_id=captcha["message_id"],
        reply_markup=captcha["reply_markup"],
    )

    logger.info("Captcha updated for user %s, new capcha text %s", user_id, text)


def update_captcha_time_left(captcha):
    timer = captcha_properties["validate"]["timer"]
    event_offset = EVENTS.get(captcha["eq_key"], {}).get("offset", timer)
    event_time_left = timer - event_offset
    captcha["time_left"] = max(0, event_time_left)

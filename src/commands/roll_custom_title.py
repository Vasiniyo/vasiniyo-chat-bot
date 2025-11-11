import json
import random
from types import SimpleNamespace

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import config
from database.titles import (
    commit_dice_roll,
    commit_update_title,
    get_user_title,
    is_day_passed,
    is_user_has_title,
)
import safely_bot_utils as bot

random_title = (
    lambda: f"{random.choice(config.custom_titles.adjectives)} {random.choice(config.custom_titles.nouns)}"
)

already_registered = bot.reply_to(bot.phrases("roll_already_registered"))
cant_roll = lambda func: func(bot.phrases("roll_cant_roll"))
cant_change_title = lambda func: lambda t: func(
    bot.phrases("roll_cant_change_title", t)
)
guessed = lambda func: lambda t: func(bot.phrases("roll_guessed", t))
old_title = lambda func: lambda t: func(bot.phrases("roll_old_title", t))
no_guessed_d6 = lambda e, v: (
    bot.edit_message_text_later(bot.phrases("roll_no_guessed_d6", e, v))
)
no_guessed_randomD6 = lambda: (
    bot.edit_message_text_later(bot.phrases("roll_no_guessed_randomD6"))
)
not_yours = bot.answer_callback_query(bot.phrases("roll_not_yours"))

callback_d6 = lambda i, m: (
    json.dumps({"type": "d6", "value": i, "user_id": m.from_user.id})
)

callback_randomD6 = lambda m: (
    json.dumps({"type": "randomD6", "user_id": m.from_user.id})
)

parse_data = lambda call: (bot.do_action(json.loads)(call.data) or {})
validate_data = lambda call: parse_data(call).get("type") in ["d6", "randomD6"]
set_markup = lambda text: lambda markup: bot.reply_to(text, reply_markup=markup)
propose = set_markup(bot.phrases("roll_propose"))


def perms_ok(chat_id, user_id):
    admins = {a.user.id: a for a in bot.get_chat_administrators(chat_id)}
    user = admins.get(user_id)
    bot_user = admins.get(
        bot.get_me().id,
        SimpleNamespace(can_promote_members=False, can_invite_users=False),
    )
    return bot_user.can_invite_users and (
        (user is None and bot_user.can_promote_members)
        or (user is not None and user.can_be_edited)
    )


def set_title(chat_id, user_id, title, callback):
    if not perms_ok(chat_id, user_id):
        return cant_change_title

    bot.promote_chat_member(chat_id, user_id, can_invite_users=True)
    bot.set_chat_administrator_custom_title(chat_id, user_id, title)

    return callback


def set_random_title(callback, chat_id, user_id):
    title = random_title()

    handler = set_title(chat_id, user_id, title, guessed)
    commit_update_title(chat_id, user_id, title)

    return handler(callback)(title)


def set_old_title(callback, chat_id, user_id):
    user_title = get_user_title(chat_id, user_id)
    handler = set_title(chat_id, user_id, user_title, old_title)

    return handler(callback)(user_title)


def get_admin_title(chat_id, user_id):
    for admin in bot.get_chat_administrators(chat_id):
        if admin.user.id == user_id:
            return admin.custom_title
    return None


def handle_cant_roll(callback, user_id, message):
    chat_id = message.chat.id
    can_roll = is_day_passed(chat_id, user_id)
    user_admin_title = get_admin_title(chat_id, user_id)

    if can_roll and user_admin_title:
        return False

    # user is playing for the first time
    if can_roll is None:
        set_random_title(callback, chat_id, user_id)(message)
    elif user_admin_title is None:
        if is_user_has_title(chat_id, user_id):
            set_old_title(callback, chat_id, user_id)(message)
        else:
            set_random_title(callback, chat_id, user_id)(message)
    else:
        cant_roll(callback)(message)
    return True


# when user call /reg
def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_day_passed(chat_id, user_id) is not None:
        if get_admin_title(chat_id, user_id) is None:
            # there may be an error here if user does not have a title in entry
            # but according to the logic of application this should not happen
            return set_old_title(bot.reply_to, chat_id, user_id)(message)
        return already_registered(message)

    return set_random_title(bot.reply_to, chat_id, user_id)(message)


# when user call /rename
def prepare_game(msg):
    if handle_cant_roll(bot.reply_to, msg.from_user.id, msg):
        return
    number_buttons = [
        InlineKeyboardButton(i, callback_data=callback_d6(i, msg)) for i in range(1, 7)
    ]
    propose(
        InlineKeyboardMarkup()
        .row(*number_buttons)
        .row(InlineKeyboardButton("Мне повезёт", callback_data=callback_randomD6(msg)))
    )(msg)


# handle the event, when user press button in game
def handle_title_change_attempt(call):
    data = parse_data(call)
    user_id = data["user_id"]
    if user_id != call.from_user.id:
        return not_yours(call)

    message = call.message
    chat_id = message.chat.id
    if handle_cant_roll(bot.edit_message_text, user_id, message):
        return
    if data["type"] == "d6":
        number = data["value"]
        dice_message = bot.send_dice(message)
        commit_dice_roll(chat_id, user_id)
        if (dice_value := dice_message.dice.value) != number:
            return no_guessed_d6(number, dice_value)(message)
    elif data["type"] == "randomD6":
        dice_message = bot.send_random_dice(message)
        win_values = bot.dices[dice_message.dice.emoji]["win_values"]
        commit_dice_roll(chat_id, user_id)
        if dice_message.dice.value not in win_values:
            return no_guessed_randomD6()(message)
    bot.edit_message_reply_markup(message)
    return set_random_title(bot.edit_message_text_later, chat_id, user_id)(message)

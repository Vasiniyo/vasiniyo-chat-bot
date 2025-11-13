import json
import logging
import random
from types import SimpleNamespace

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions

from config import config
from database.titles import (
    commit_dice_roll,
    commit_update_title,
    get_user_title,
    get_user_titles,
    is_day_passed,
    is_user_has_title,
)
import safely_bot_utils as bot


def random_title():
    titles = config.custom_titles
    adj = random.choices(titles.adjectives, weights=titles.weights, k=1)[0]
    noun = random.choice(
        [noun for noun in titles.nouns if len(adj) + 1 + len(noun) <= 16]
    )
    return f"{adj} {noun}"


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

callback_d6 = lambda i, user_id: (
    json.dumps({"type": "d6", "value": i, "uid": user_id})
)

callback_randomD6 = lambda user_id: (json.dumps({"type": "randomD6", "uid": user_id}))


def callback_main_menu(user_id):
    return json.dumps({"type": "m", "uid": user_id})


def callback_steal(page, user_id):
    return json.dumps({"type": "s", "page": page, "uid": user_id})


def callback_steal_title(target_id, user_id):
    return json.dumps({"type": "sl", "tid": target_id, "uid": user_id})


parse_data = lambda call: (bot.do_action(json.loads)(call.data) or {})
validate_data = lambda call: parse_data(call).get("type") in [
    "d6",
    "randomD6",
    "s",
    "sl",
    "m",
]
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


def set_title_possible(chat_id, user_id, title):
    if not perms_ok(chat_id, user_id):
        return False
    bot.promote_chat_member(chat_id, user_id, can_invite_users=True)
    bot.set_chat_administrator_custom_title(chat_id, user_id, title)
    return True


def set_specific_title(callback, chat_id, user_id, title):
    commit_update_title(chat_id, user_id, title)
    if set_title_possible(chat_id, user_id, title):
        return None
    return cant_change_title(callback)(title)


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
    user_id = msg.from_user.id
    if handle_cant_roll(bot.reply_to, user_id, msg):
        return
    number_buttons = [
        InlineKeyboardButton(i, callback_data=callback_d6(i, user_id))
        for i in range(1, 7)
    ]
    propose(
        InlineKeyboardMarkup()
        .row(*number_buttons)
        .row(
            InlineKeyboardButton(
                "Мне повезёт", callback_data=callback_randomD6(user_id)
            )
        )
        .row(InlineKeyboardButton("Кража", callback_data=callback_steal(0, user_id)))
    )(msg)


def get_titles_page(chat_id, page=0, page_size=9):
    user_titles = {
        user_id: title
        for user_id, title in get_user_titles(chat_id)
        if title != "украдено"
    }
    titles = [
        (admin.user, admin.custom_title)
        for admin in bot.get_chat_administrators(chat_id)
        if user_titles.get(admin.user.id) == admin.custom_title
    ]
    start1 = page * page_size
    end = start1 + page_size
    page_titles = titles[start1:end]
    more_pages = end < (len(titles) - 1)
    return page_titles, more_pages


def handle_title_change_attempt(call):
    data = parse_data(call)
    user_id = data["uid"]
    if user_id != call.from_user.id:
        return not_yours(call)
    message = call.message
    chat_id = message.chat.id
    if handle_cant_roll(bot.edit_message_text, user_id, message):
        return
    if data["type"] == "s":
        return show_steal_menu(message, user_id, page=data.get("page", 0))
    elif data["type"] == "sl":
        bot.edit_message_reply_markup(message)
        return handle_steal(call)
    elif data["type"] == "m":
        number_buttons = [
            InlineKeyboardButton(i, callback_data=callback_d6(i, user_id))
            for i in range(1, 7)
        ]
        markup = InlineKeyboardMarkup()
        markup.row(*number_buttons)
        markup.add(
            InlineKeyboardButton(
                "Мне повезёт", callback_data=callback_randomD6(user_id)
            )
        )
        markup.add(
            InlineKeyboardButton("Кража", callback_data=callback_steal(0, user_id))
        )
        bot.edit_message_text(bot.phrases("roll_propose"), reply_markup=markup)(message)
        return
    if data["type"] == "d6":
        bot.edit_message_reply_markup(message)
        number = data["value"]
        dice_message = bot.send_dice(message)
        commit_dice_roll(chat_id, user_id)
        if (dice_value := dice_message.dice.value) != number:
            return no_guessed_d6(number, dice_value)(message)
    elif data["type"] == "randomD6":
        bot.edit_message_reply_markup(message)
        dice_message = bot.send_random_dice(message)
        win_values = bot.dices[dice_message.dice.emoji]["win_values"]
        commit_dice_roll(chat_id, user_id)
        if dice_message.dice.value not in win_values:
            return no_guessed_randomD6()(message)
    return set_random_title(bot.edit_message_text_later, chat_id, user_id)(message)


def handle_steal(call):
    data = parse_data(call)
    user_id = data["uid"]
    target_id = data["tid"]
    chat_id = call.message.chat.id
    message = call.message
    dice_message = bot.send_random_dice(message)
    win_values = bot.dices[dice_message.dice.emoji]["win_values"]
    commit_dice_roll(chat_id, user_id)
    if dice_message.dice.value not in win_values:
        bot.edit_message_text_later("Жулик, не воруй!")(message)
        return
    target_title = get_admin_title(chat_id, target_id)
    user_with_link = bot.to_link_user(call.from_user)
    target_with_link = next(
        bot.to_link_user(admin.user)
        for admin in bot.get_chat_administrators(chat_id)
        if admin.user.id == target_id
    )
    a1 = set_specific_title(lambda text: text, chat_id, target_id, "украдено")
    a2 = set_specific_title(lambda text: text, chat_id, user_id, target_title)
    b1 = f"\n\n{a1}" if a1 is not None else ""
    b2 = f"\n\n{a2}" if a2 is not None else ""
    logging.info(f"{a2}, {a1}")
    bot.edit_message_text_later(
        f"АХТУНГ, грабёж средь бела дня!!! "
        f"{user_with_link} украл у {target_with_link} лычку: {target_title}! "
        f"Соболезнуем всем чатом..."
        f"{b2}{b1}",
        parse_mode="Markdown",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )(message)


def show_steal_menu(message, user_id, page=0):
    chat_id = message.chat.id
    page_titles, more_pages = get_titles_page(chat_id, page)

    buttons = [
        InlineKeyboardButton(
            f"{title} | {target_user.username or target_user.first_name}",
            callback_data=callback_steal_title(target_user.id, user_id),
        )
        for target_user, title in page_titles
        if target_user.id != user_id
    ]
    markup = InlineKeyboardMarkup()
    for button in buttons:
        markup.add(button)

    back_button = InlineKeyboardButton(
        "◀️", callback_data=callback_steal(page - 1, user_id)
    )
    forward_button = InlineKeyboardButton(
        "▶️", callback_data=callback_steal(page + 1, user_id)
    )
    main_menu_button = InlineKeyboardButton(
        "🟣 Вернуться", callback_data=callback_main_menu(user_id)
    )

    if page > 0 and more_pages:
        markup.add(back_button, forward_button)
    else:
        if page > 0:
            markup.add(back_button)
        if more_pages:
            markup.add(forward_button)
    markup.add(main_menu_button)

    bot.edit_message_text(
        "Выбери лычку, которую хочешь украсть...", reply_markup=markup
    )(message)

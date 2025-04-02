import random
from types import SimpleNamespace

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import adjectives, nouns
from database.titles import commit_dice_roll, is_day_passed
import safely_bot_utils as bot

already_registered = bot.reply_to("Я тебя уже зарегистрировала!")
cant_roll = lambda func: func("Ты сегодня уже роллял лычку!")
no_perms = lambda func: func("У меня нет прав, чтобы изменить твою лычку!")
guessed = lambda func: lambda t: func(f"Изменила твою лычку на {t}!")
no_guessed = lambda e, v: bot.edit_message_text_later(
    f"Ты не угадал! Ты выбрал {e}, выпало {v}"
)
not_yours = bot.answer_callback_query("Эти кнопки были не для тебя!")
set_markup = lambda text: lambda markup: bot.reply_to(text, reply_markup=markup)

callback_data = lambda i, m: {"callback_data": f"number_{i}$userid_{m.from_user.id}"}
parse_callback_data = lambda c: map(lambda e: int(e.split("_")[1]), c.data.split("$"))
propose = set_markup("Я подброшу кубик и если угадаешь число, то я поменяю тебе лычку!")


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


def set_random_title(callback, chat_id, user_id):
    title = f"{random.choice(adjectives)} {random.choice(nouns)}"
    bot.promote_chat_member(chat_id, user_id, can_invite_users=True)
    bot.set_chat_administrator_custom_title(chat_id, user_id, title)
    return guessed(callback)(title)


def handle_cant_roll(callback, user_id, message):
    chat_id = message.chat.id
    can_roll = is_day_passed(chat_id, user_id)
    has_perms = perms_ok(chat_id, user_id)
    if can_roll and has_perms:
        return False
    if not has_perms:
        no_perms(callback)(message)
    elif can_roll is None:
        commit_dice_roll(chat_id, user_id)
        set_random_title(callback, chat_id, user_id)(message)
    else:
        cant_roll(callback)(message)
    return True


def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_day_passed(chat_id, user_id) is not None:
        return already_registered(message)
    if not perms_ok(chat_id, user_id):
        return no_perms(bot.reply_to)(message)
    commit_dice_roll(chat_id, user_id)
    return set_random_title(bot.reply_to, chat_id, user_id)(message)


def prepare_game(msg):
    if handle_cant_roll(bot.reply_to, msg.from_user.id, msg):
        return
    buttons = [InlineKeyboardButton(i, **callback_data(i, msg)) for i in range(1, 7)]
    propose(InlineKeyboardMarkup().row(*buttons))(msg)


def handle_title_change_attempt(call):
    number, user_id = parse_callback_data(call)
    if user_id != call.from_user.id:
        return not_yours(call)
    message = call.message
    chat_id = message.chat.id
    if handle_cant_roll(bot.edit_message_text, user_id, message):
        return
    dice_message = bot.send_dice(message)
    bot.edit_message_reply_markup(message)
    commit_dice_roll(chat_id, user_id)
    bot.delete_message_later(dice_message)
    if (dice_value := dice_message.dice.value) != number:
        return no_guessed(number, dice_value)(message)
    return set_random_title(bot.edit_message_text_later, chat_id, user_id)(message)

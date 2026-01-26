import json
import logging
import random
import time
from typing import Optional

from telebot.types import (
    CallbackQuery,
    ChatMember,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
    User,
)

from config import config
from custom_typing.typing import Action, Field, LogDetails, RolledDice, RollType
from database.titles import (
    commit_dice_roll,
    commit_reset_user,
    commit_update_title,
    commit_update_title_with_old_time,
    get_user_title,
    get_user_titles,
    is_day_passed,
)
from database.titles_bag import (
    commit_remove_title_in_bag,
    commit_save_title,
    get_title_in_bag,
    get_user_titles_bag,
)
from logger import get_json_logger
import safely_bot_utils as bot

_opened_swap_menu: dict[str, int] = {}


def validate_data(call: CallbackQuery) -> bool:
    return (
        _parse_callback_payload(call).get(Field.ACTION_TYPE.value)
        in Action._value2member_map_
    )


def log(level, msg: str, logDetails: LogDetails):
    get_json_logger().log(level, msg, extra={"details": logDetails})


def handle_title_change_attempt(call: CallbackQuery) -> None:
    def buttons_not_works(details: str) -> None:
        log_details = LogDetails(call=call, details=details)
        log(logging.WARN, "invalid_payload_state", log_details)
        bot.answer_callback_query("Извините, кнопка не работает...")(call)

    def handlers():
        menu_key = f"{message.chat.id}|{message.message_id}"
        day_passed = is_day_passed(message.chat.id, user_id)
        back_to_rename_menu_later = bot.edit_message_text_later(
            text=bot.phrases("roll_propose"),
            delay=60,
            should_edit=lambda: (
                int(time.time()) - _opened_swap_menu.get(menu_key) >= 60
            ),
            reply_markup=(
                _create_rename_menu_markups_only_bag(user_id)
                if not day_passed
                else _create_rename_menu_markups(user_id)
            ),
        )
        match action_type:
            case Action.OPEN_STEAL_MENU | Action.OPEN_TITLES_BAG:
                _opened_swap_menu[menu_key] = int(time.time())
            case _:
                _opened_swap_menu.pop(menu_key, None)
        match action_type:
            case Action.OPEN_RENAME_MENU:
                _show_rename_menu(message, user_id)
            case Action.OPEN_STEAL_MENU:
                page = _to_int(payload.get(Field.PAGE.value, 0))
                if page is not None and page >= 0:
                    _show_steal_menu(message, user_id, page)
                    back_to_rename_menu_later(message)
                else:
                    buttons_not_works("page must be non-negative integer")
            case Action.STEAL_TITLE:
                target_id = _to_int(payload.get(Field.TARGET_USER_ID.value))
                if target_id is not None:
                    _handle_steal(message, actor, target_id)
                else:
                    buttons_not_works("target_id must be integer")
            case Action.ROLL_RANDOM_D6:
                _handle_random_d6(message, user_id)
            case Action.ROLL_D6:
                dice_value = _to_int(payload.get(Field.DICE_VALUE.value))
                if 0 <= dice_value <= 6:
                    _handle_d6(message, dice_value, user_id)
                else:
                    buttons_not_works("Dice value must be between 0 and 6")
            case Action.OPEN_TITLES_BAG:
                page = _to_int(payload.get(Field.PAGE.value, 0))
                if page is not None and page >= 0:
                    _handle_show_titles_bag(message, user_id, page)
                    back_to_rename_menu_later(message)
                else:
                    buttons_not_works("page must be non-negative integer")
            case Action.SET_TITLE_BAG:
                title_bag_id = payload.get(Field.TITLE_BAG_ID.value)
                _handle_swap_title(message, user_id, title_bag_id)

    actor = call.from_user
    message = call.message
    payload = _parse_callback_payload(call)
    action_type = _to_action_type(payload.get(Field.ACTION_TYPE.value))
    user_id = _to_int(payload.get(Field.USER_ID.value))
    if user_id is None:
        buttons_not_works("user_id must be integer")
        return
    if action_type is None:
        buttons_not_works("Invalid action_type")
        return
    if actor.id != user_id:
        log_details = LogDetails(call=call, details="Permission denied")
        log(logging.INFO, "pressed_button", log_details)
        bot.answer_callback_query(bot.phrases("roll_not_yours"))(call)
        return
    log(logging.INFO, "pressed_button", LogDetails(call=call))
    if action_type in (Action.OPEN_TITLES_BAG, Action.SET_TITLE_BAG):
        _handle_roll_logic(handlers, actor.id, message, call_ready_on_wait=True)
    else:
        _handle_roll_logic(handlers, actor.id, message)


# when user call /reg
def start(message: Message) -> None:
    log(logging.INFO, "command_handling", LogDetails(message=message))
    _handle_roll_logic(
        lambda: bot.reply_to(bot.phrases("roll_already_registered"))(message),
        message.from_user.id,
        message,
        call_ready_on_wait=True,
    )


# when user call /rename
def prepare_game(message: Message) -> None:
    log(logging.INFO, "command_handling", LogDetails(message=message))
    _handle_roll_logic(
        lambda: _show_rename_menu(message, message.from_user.id),
        message.from_user.id,
        message,
    )


_wrap_swap_title = lambda callback: lambda title, error: callback(
    f"Изменила лычку на {title}" + (f"\n{error}" if error else "")
)

_wrap_new_title = lambda callback: lambda title, error: callback(
    bot.phrases("roll_guessed", title) + (f"\n{error}" if error else "")
)
_wrap_old_title = lambda callback: lambda title, error: callback(
    bot.phrases("roll_old_title", title) + (f"\n{error}" if error else "")
)
_send_d6_fail_message = lambda choice, expected: (
    bot.edit_message_text_later(bot.phrases("roll_no_guessed_d6", choice, expected))
)
_send_random_d6_fail_message = lambda: (
    bot.edit_message_text_later(bot.phrases("roll_no_guessed_randomD6"))
)


def _random_title() -> str:
    titles = config.custom_titles
    adj = random.choices(titles.adjectives, weights=titles.weights, k=1)[0]
    noun = random.choice(
        [noun for noun in titles.nouns if len(adj) + 1 + len(noun) <= 16]
    )

    return f"{adj} {noun}"


def _get_roll_status(chat_id: int, user_id: int) -> RollType:
    def log_roll_type(details, roll_type: RollType) -> None:
        log_details = LogDetails(
            chat_id=chat_id, user_id=user_id, roll_type=roll_type, details=details
        )
        log(logging.INFO, "roll_type", log_details)

    day_passed = is_day_passed(chat_id, user_id)
    if day_passed is None:
        log_roll_type("No information in db", RollType.ROLL_INSTANT)
        return RollType.ROLL_INSTANT
    if get_user_title(chat_id, user_id) != _get_admin_title(chat_id, user_id):
        log_roll_type("Title in db most priority", RollType.GIVE_OLD)
        return RollType.GIVE_OLD
    if day_passed:
        log_roll_type("Day passed", RollType.ROLL_READY)
        return RollType.ROLL_READY
    log_roll_type("Day not passed", RollType.WAIT)
    return RollType.WAIT


def _handle_roll_logic(
    roll_ready_callback,
    user_id: int,
    message: Message,
    call_ready_on_wait: bool = False,
) -> None:
    chat_id = message.chat.id
    bot_response = (
        bot.edit_message_text
        if message is not None and message.from_user.id == bot.get_me().id
        else bot.reply_to
    )
    match _get_roll_status(chat_id, user_id):
        case RollType.ROLL_INSTANT:
            _set_random_title(_wrap_new_title(bot_response), chat_id, user_id)(message)
        case RollType.GIVE_OLD:
            _set_old_title(_wrap_old_title(bot_response), chat_id, user_id)(message)
        case RollType.WAIT:
            if call_ready_on_wait:
                roll_ready_callback()
            else:
                bot_response(
                    bot.phrases("roll_cant_roll"),
                    reply_markup=_create_rename_menu_markups_only_bag(user_id),
                )(message)
        case RollType.ROLL_READY:
            roll_ready_callback()


def _set_title(callback, chat_id: int, user_id: int, title: str):
    if _can_bot_change_title(chat_id, user_id):
        log_details = LogDetails(chat_id=chat_id, user_id=user_id, details=title)
        log(logging.INFO, "set_title_in_chat", log_details)
        bot.promote_chat_member(chat_id, user_id, can_invite_users=True)
        bot.set_chat_administrator_custom_title(chat_id, user_id, title)
        return callback(title, None)
    else:
        log_details = LogDetails(
            chat_id=chat_id, user_id=user_id, details="Permission denied"
        )
        log(logging.WARN, "set_title_in_chat", log_details)
        return callback(title, bot.phrases("roll_cant_change_title", title))


def _set_random_title(callback, chat_id: int, user_id: int):
    title = _random_title()
    log(logging.INFO, "choice_random_title", LogDetails(details=title))
    return _set_specific_title(callback, chat_id, user_id, title)


def _set_old_title(callback, chat_id: int, user_id: int):
    return _set_title(callback, chat_id, user_id, get_user_title(chat_id, user_id))


def _set_specific_title(
    callback, chat_id: int, user_id: int, title: str, with_old_time=False
):
    log_details = LogDetails(chat_id=chat_id, user_id=user_id, details=title)
    log(logging.INFO, "update_title_in_db", log_details)
    if old_title := get_user_title(chat_id, user_id):
        commit_save_title(chat_id, user_id, old_title)
    if with_old_time:
        commit_update_title_with_old_time(chat_id, user_id, title)
    else:
        commit_update_title(chat_id, user_id, title)
    return _set_title(callback, chat_id, user_id, title)


def _handle_show_titles_bag(message: Message, user_id: int, page: int = 0) -> None:
    log(logging.INFO, "show_titles_bag", LogDetails(user_id=user_id, message=message))
    chat_id = message.chat.id
    page_titles, has_more_pages = _get_titles_bag_page(chat_id, user_id, page)
    markup = _create_bag_menu_markups(user_id, page, page_titles, has_more_pages)
    bot.edit_message_text(bot.phrases("roll_titles_bag"), reply_markup=markup)(message)


def _show_rename_menu(message: Message, user_id: int) -> None:
    log(logging.INFO, "show_rename_menu", LogDetails(user_id=user_id, message=message))
    markup = _create_rename_menu_markups(user_id)
    bot_response = (
        bot.edit_message_text
        if message is not None and message.from_user.id == bot.get_me().id
        else bot.reply_to
    )
    bot_response(bot.phrases("roll_propose"), reply_markup=markup)(message)


def _show_steal_menu(message: Message, user_id: int, page: int = 0) -> None:
    log_details = LogDetails(user_id=user_id, message=message, details=f"page = {page}")
    log(logging.INFO, "show_steal_menu", log_details)
    chat_id = message.chat.id
    page_titles, has_more_pages = _get_titles_page(chat_id, user_id, page)
    markup = _create_steal_menu_markups(user_id, page, page_titles, has_more_pages)
    bot.edit_message_text(bot.phrases("roll_steal_prepare"), reply_markup=markup)(
        message
    )


def _get_titles_page(
    chat_id: int, user_id: int, page: int = 0, page_size: int = 9
) -> tuple[list, bool]:
    user_titles = {user_id: title for user_id, title in get_user_titles(chat_id)}
    titles = [
        (admin.user, admin.custom_title)
        for admin in bot.get_chat_administrators(chat_id)
        if user_titles.get(admin.user.id) == admin.custom_title
        and admin.user.id != user_id
    ]
    start_page = page * page_size
    end_page = start_page + page_size
    page_titles = titles[start_page:end_page]
    has_more_pages = end_page < (len(titles))
    return page_titles, has_more_pages


def _get_titles_bag_page(
    chat_id: int, user_id: int, page: int = 0, page_size: int = 9
) -> tuple[list[int, str], bool]:
    titles = get_user_titles_bag(chat_id, user_id)
    start_page = page * page_size
    end_page = start_page + page_size
    page_titles = titles[start_page:end_page]
    has_more_pages = end_page < (len(titles))
    return page_titles, has_more_pages


def _parse_callback_payload(call: CallbackQuery) -> dict:
    try:
        data = json.loads(call.data)
        log_details = LogDetails(call=call, details=data)
        log(logging.DEBUG, "parse_callback_payload", log_details)
        return data
    except:
        log(logging.ERROR, "parse_callback_payload", LogDetails(call=call))
        return {}


def _to_int(value: str | int) -> int | None:
    return (
        int(value) if value is not None and str(value).lstrip("-").isdigit() else None
    )


def _to_action_type(value: str) -> Action | None:
    return (
        Action._value2member_map_[value] if value in Action._value2member_map_ else None
    )


def _create_titles_bag_menu_payload(page: int, user_id: int) -> str:
    return json.dumps(
        {
            Field.ACTION_TYPE.value: Action.OPEN_TITLES_BAG.value,
            Field.USER_ID.value: user_id,
            Field.PAGE.value: page,
        }
    )


def _create_set_title_payload(title_bag_id: int, user_id: int) -> str:
    return json.dumps(
        {
            Field.ACTION_TYPE.value: Action.SET_TITLE_BAG.value,
            Field.USER_ID.value: user_id,
            Field.TITLE_BAG_ID.value: title_bag_id,
        }
    )


def _create_d6_payload(i, user_id: int) -> str:
    return json.dumps(
        {
            Field.ACTION_TYPE.value: Action.ROLL_D6.value,
            Field.USER_ID.value: user_id,
            Field.DICE_VALUE.value: i,
        }
    )


def _create_random_d6_payload(user_id: int) -> str:
    return json.dumps(
        {
            Field.ACTION_TYPE.value: Action.ROLL_RANDOM_D6.value,
            Field.USER_ID.value: user_id,
        }
    )


def _create_rename_menu_payload(user_id: int) -> str:
    return json.dumps(
        {
            Field.ACTION_TYPE.value: Action.OPEN_RENAME_MENU.value,
            Field.USER_ID.value: user_id,
        }
    )


def _create_steal_menu_payload(page: int, user_id: int) -> str:
    return json.dumps(
        {
            Field.ACTION_TYPE.value: Action.OPEN_STEAL_MENU.value,
            Field.USER_ID.value: user_id,
            Field.PAGE.value: page,
        }
    )


def _create_steal_title_payload(target_id: int, user_id: int) -> str:
    return json.dumps(
        {
            Field.ACTION_TYPE.value: Action.STEAL_TITLE.value,
            Field.USER_ID.value: user_id,
            Field.TARGET_USER_ID.value: target_id,
        }
    )


def _can_bot_change_title(chat_id: int, user_id: int) -> bool:
    admins: dict[int, ChatMember] = {
        a.user.id: a for a in bot.get_chat_administrators(chat_id)
    }
    user = admins.get(user_id)
    bot_user = admins.get(bot.get_me().id)
    return (
        bot_user
        and bot_user.can_invite_users
        and (
            (user is None and bot_user.can_promote_members)
            or (user is not None and user.can_be_edited)
        )
    )


def _get_admin_title(chat_id: int, user_id: int) -> str | None:
    for admin in bot.get_chat_administrators(chat_id):
        if admin.user.id == user_id:
            return admin.custom_title
    return None


def roll_dice(
    message: Message, user_id: int, expected_value: Optional[int] = None
) -> tuple[int, bool]:
    def log_roll(msg: str) -> None:
        log_details = LogDetails(
            message=message,
            user_id=user_id,
            dice=RolledDice(
                value=dice_value,
                expected_value=expected_value,
                win_values=win_values,
                success=(expected_value or dice_value) in win_values,
            ),
        )
        log(logging.INFO, msg, log_details)

    bot.edit_message_reply_markup(message)
    if expected_value is None:
        dice_message = bot.send_random_dice(message)
        dice_value = dice_message.dice.value
        win_values = bot.DICES[dice_message.dice.emoji]["win_values"]
        log_roll("handle_random_d6")
    else:
        dice_message = bot.send_dice(message)
        dice_value = dice_message.dice.value
        win_values = [dice_value]
        log_roll("handle_d6")

    return dice_value, (expected_value or dice_value) in win_values


def _handle_d6(message: Message, value: int, user_id: int) -> None:
    dice_value, success = roll_dice(message, user_id, value)
    if success:
        response = _wrap_new_title(bot.edit_message_text_later)
        _set_random_title(response, message.chat.id, user_id)(message)
    else:
        commit_dice_roll(message.chat.id, user_id)
        _send_d6_fail_message(value, dice_value)(message)


def _handle_random_d6(message: Message, user_id: int) -> None:
    _, success = roll_dice(message, user_id)
    if success:
        response = _wrap_new_title(bot.edit_message_text_later)
        _set_random_title(response, message.chat.id, user_id)(message)
    else:
        commit_dice_roll(message.chat.id, user_id)
        _send_random_d6_fail_message()(message)


def _handle_steal(message: Message, actor: User, target_id: int) -> None:
    chat_id = message.chat.id
    user_id = actor.id

    _, success = roll_dice(message, user_id)
    if not success:
        commit_dice_roll(chat_id, user_id)
        bot.edit_message_text_later("Жулик, не воруй!")(message)
        return

    target_title = get_user_title(chat_id, target_id)
    target_user = None
    for admin in bot.get_chat_administrators(chat_id):
        if admin.user.id == target_id:
            target_user = admin.user
            break
    if (target_user is None) or (target_title is None):
        bot.edit_message_text_later(
            "Поздравляю, ты выиграл! Но лычка куда-то пропала, извини..."
        )(message)
        return
    bag = get_user_titles_bag(chat_id, target_id)
    if len(bag) > 0:
        title_bag_id, next_target_title = bag[0]
    else:
        title_bag_id, next_target_title = None, None
    if title_bag_id is not None:
        commit_remove_title_in_bag(title_bag_id)
    commit_reset_user(chat_id, target_id)
    if next_target_title is None:
        error1 = _set_title(lambda _, e: e, chat_id, target_id, "украдено")
    else:
        error1 = _set_specific_title(
            lambda _, e: e, chat_id, target_id, next_target_title
        )
    error2 = _set_specific_title(lambda _, e: e, chat_id, user_id, target_title)
    problems = "".join([f"\n\n{error}" if error else "" for error in [error1, error2]])
    bot.edit_message_text_later(
        bot.phrases(
            "roll_steal_success",
            bot.to_link_user(actor),
            bot.to_link_user(target_user),
            target_title,
            problems,
        ),
        parse_mode="Markdown",
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )(message)


def _handle_swap_title(message: Message, user_id: int, title_bag_id: int):
    log(logging.INFO, "show_swap_title", LogDetails(user_id=user_id, message=message))
    chat_id = message.chat.id
    title = get_title_in_bag(title_bag_id)
    if title is None:
        return bot.edit_message_text("У вас больше нет такой лычки в инвентаре")
    commit_remove_title_in_bag(title_bag_id)
    _set_specific_title(
        _wrap_swap_title(bot.edit_message_text),
        chat_id,
        user_id,
        title,
        with_old_time=True,
    )(message)


def _d6_option_button(option: str, user_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        option, callback_data=_create_d6_payload(option, user_id)
    )


def _create_rename_menu_markups(user_id: int) -> InlineKeyboardMarkup:
    number_buttons = [_d6_option_button(str(i), user_id) for i in range(1, 7)]
    return (
        InlineKeyboardMarkup()
        .row(*number_buttons)
        .add(_random_d6_button(user_id))
        .add(_steal_button(user_id))
        .add(_titles_bag_menu_button(user_id))
    )


def _create_rename_menu_markups_only_bag(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(_titles_bag_menu_button(user_id))


def _create_bag_menu_markups(
    user_id: int, page: int, page_titles: list, has_more_pages: bool
) -> InlineKeyboardMarkup:
    buttons = [
        _get_in_bag_title_button(title_bag_id, title, user_id)
        for title_bag_id, title in page_titles
    ]
    markup = InlineKeyboardMarkup()
    for button in buttons:
        markup.add(button)
    back_button = _back_titles_bag_button(page - 1, user_id)
    forward_button = _forward_titles_bag_button(page + 1, user_id)
    if page > 0 and has_more_pages:
        markup.add(back_button, forward_button)
    else:
        if page > 0:
            markup.add(back_button)
        if has_more_pages:
            markup.add(forward_button)
    markup.add(_rename_menu_button(user_id))
    return markup


def _create_steal_menu_markups(
    user_id: int, page: int, page_titles: list, has_more_pages: bool
) -> InlineKeyboardMarkup:
    buttons = [
        _steal_user_title_button(target_user, title, user_id)
        for target_user, title in page_titles
    ]
    markup = InlineKeyboardMarkup()
    for button in buttons:
        markup.add(button)
    back_button = _back_steal_menu_button(page - 1, user_id)
    forward_button = _forward_steal_menu_button(page + 1, user_id)
    if page > 0 and has_more_pages:
        markup.add(back_button, forward_button)
    else:
        if page > 0:
            markup.add(back_button)
        if has_more_pages:
            markup.add(forward_button)
    markup.add(_rename_menu_button(user_id))
    return markup


def _titles_bag_menu_button(user_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "Инвентарь", callback_data=_create_titles_bag_menu_payload(0, user_id)
    )


def _random_d6_button(user_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "Мне повезёт", callback_data=_create_random_d6_payload(user_id)
    )


def _steal_button(user_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "Кража", callback_data=_create_steal_menu_payload(0, user_id)
    )


def _steal_user_title_button(
    user: User, title: str, button_owner_id: int
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        f"{title} | {user.username or user.first_name}",
        callback_data=_create_steal_title_payload(user.id, button_owner_id),
    )


def _get_in_bag_title_button(
    title_bag_id: int, title: str, button_owner_id: int
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        title, callback_data=_create_set_title_payload(title_bag_id, button_owner_id)
    )


def _back_titles_bag_button(page: int, button_owner_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "⬅️", callback_data=_create_titles_bag_menu_payload(page, button_owner_id)
    )


def _forward_titles_bag_button(page: int, button_owner_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "➡️", callback_data=_create_titles_bag_menu_payload(page, button_owner_id)
    )


def _back_steal_menu_button(page: int, button_owner_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "⬅️", callback_data=_create_steal_menu_payload(page, button_owner_id)
    )


def _forward_steal_menu_button(page: int, button_owner_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "➡️", callback_data=_create_steal_menu_payload(page, button_owner_id)
    )


def _rename_menu_button(button_owner_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        "🟣 Вернуться", callback_data=_create_rename_menu_payload(button_owner_id)
    )

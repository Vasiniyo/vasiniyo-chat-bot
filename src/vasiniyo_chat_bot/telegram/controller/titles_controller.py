from dataclasses import dataclass
import logging

from telebot.types import CallbackQuery, Message

from vasiniyo_chat_bot.module.titles.dto import StealMenu, TitleChanged
from vasiniyo_chat_bot.module.titles.titles_service import TitlesService
from vasiniyo_chat_bot.safely_bot_utils import extract_field, parse_json
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import Action, Field
from vasiniyo_chat_bot.telegram.renderer.titles_renderer import TitlesRenderer


@dataclass(frozen=True)
class CallBackPayload:
    action: Action
    user_id: int
    dice_value: int | None = None
    page: int | None = None
    target_id: int | None = None
    title_bag_id: int | None = None


class TitlesController:
    _valid_payload_actions = {
        Action.ROLL_RANDOM_D6.value,
        Action.ROLL_D6.value,
        Action.OPEN_RENAME_MENU.value,
        Action.OPEN_STEAL_MENU.value,
        Action.STEAL_TITLE.value,
        Action.OPEN_TITLES_BAG.value,
        Action.SET_TITLE_BAG.value,
    }

    def __init__(
        self,
        titles_service: TitlesService,
        bot_service: BotService,
        titles_renderer: TitlesRenderer,
    ):
        self.titles_service = titles_service
        self.bot_service = bot_service
        self.titles_renderer = titles_renderer

    def _set_title(
        self, title_changed: TitleChanged, chat_id: int, message_id: int, user_id: int
    ) -> None:
        if not title_changed.changed:
            self.titles_renderer.send_title_not_changed(chat_id, message_id)
            return
        tg_title = self.bot_service.set_title(chat_id, user_id, title_changed.title)
        if tg_title == title_changed.title:
            self.titles_renderer.send_title_changed(
                title_changed.title, chat_id, message_id
            )
        else:
            self.titles_renderer.send_title_changed_failed(
                title_changed.title, chat_id, message_id
            )

    def try_sync_titles(self, chat_id: int, message_id: int, user_id: int):
        db_title = self.titles_service.get_user_title(chat_id, user_id)
        if not db_title:
            self.bot_service.set_default_title(chat_id, user_id)
            return True
        tg_title = self.bot_service.get_admin_title(chat_id, user_id)
        if tg_title == db_title:
            return True
        if db_title == self.bot_service.set_title(chat_id, user_id, db_title):
            return True
        self.titles_renderer.send_please_set_title(db_title, chat_id, message_id)
        return False

    def handle_rename(self, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        if not self.try_sync_titles(chat_id, message.id, user_id):
            return
        result = self.titles_service.rename(chat_id, user_id)
        if isinstance(result, TitleChanged):
            self._set_title(result, chat_id, message.id, user_id)
            return
        self.titles_renderer.send_rename_menu(result, chat_id, message.id, user_id)

    def handle_random_dice_roll(self, call: CallbackQuery):
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        if not self.titles_service.is_day_passed(chat_id, user_id):
            self.titles_renderer.send_already_rolled(chat_id, message.id)
            return
        self.bot_service.clear_markup(chat_id, message.id)
        success = self.bot_service.roll_random_dice(chat_id, message.id)
        title_changed = self.titles_service.handle_roll(chat_id, user_id, success)
        self._set_title(title_changed, chat_id, message.id, user_id)

    def handle_dice_roll(self, call: CallbackQuery, dice_value: int):
        message = call.message
        chat_id = message.chat.id
        user_id = call.from_user.id
        if not self.titles_service.is_day_passed(chat_id, user_id):
            self.titles_renderer.send_already_rolled(chat_id, message.id)
            return
        self.bot_service.clear_markup(chat_id, message.id)
        success = self.bot_service.roll_dice(dice_value, chat_id, message.id)
        title_changed = self.titles_service.handle_roll(chat_id, user_id, success)
        self._set_title(title_changed, chat_id, message.id, user_id)

    def handle_back_to_rename_menu(self, call: CallbackQuery):
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        menu = self.titles_service.show_rename_menu(chat_id, user_id)
        self.titles_renderer.back_to_rename_menu(menu, chat_id, message.id, user_id)

    def show_steal_menu(self, call: CallbackQuery, page: int, page_size: int = 9):
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        menu = self.titles_service.show_steal_menu(chat_id, user_id, page, page_size)
        if isinstance(menu, StealMenu):
            self.titles_renderer.send_steal_menu(menu, chat_id, message.id, user_id)
        else:
            self.titles_renderer.back_to_rename_menu(menu, chat_id, message.id, user_id)

    def handle_steal(self, call: CallbackQuery, target_id: int):
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        if not self.titles_service.is_day_passed(chat_id, user_id):
            self.titles_renderer.send_already_rolled(chat_id, message.id)
            return
        self.bot_service.clear_markup(chat_id, message.id)
        success = self.bot_service.roll_random_dice(chat_id, message.id)
        result = self.titles_service.handle_steal(chat_id, user_id, target_id, success)
        if not result:
            self.titles_renderer.send_steal_failed(chat_id, message.id)
            return
        tg_actor_title = self.bot_service.set_title(
            chat_id, result.actor_id, result.actor_title
        )
        tg_target_title = self.bot_service.set_title(
            chat_id, result.target_id, result.target_title
        )
        self.titles_renderer.send_stolen_title(
            result,
            chat_id,
            message.id,
            actor_title_are_set=tg_actor_title == result.actor_title,
            target_title_are_set=tg_target_title == result.target_title,
        )

    def handle_show_titles_bag(
        self, call: CallbackQuery, page: int, page_size: int = 9
    ):
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        titles_bag = self.titles_service.handle_show_titles_bag(
            chat_id, user_id, page, page_size
        )
        self.titles_renderer.send_titles_bag(titles_bag, chat_id, message.id, user_id)

    def handle_swap_title(self, call: CallbackQuery, title_bag_id: int):
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        result = self.titles_service.handle_swap_title(chat_id, user_id, title_bag_id)
        if not result.changed:
            self.titles_renderer.send_swap_failed(result.title, chat_id, message.id)
            return
        tg_title = self.bot_service.set_title(chat_id, user_id, result.title)
        self.titles_renderer.send_swap_success(
            result.title, chat_id, message.id, user_id, are_set=result.title == tg_title
        )

    def dispatch_titles_callback(self, call: CallbackQuery):
        payload = parse_json(call.data)
        action_value = payload.get(Field.ACTION_TYPE.value)
        action = Action._value2member_map_.get(action_value)
        callback_payload = CallBackPayload(
            action=action if isinstance(action, Action) else None,
            user_id=extract_field(payload, Field.USER_ID),
            dice_value=extract_field(payload, Field.DICE_VALUE),
            page=extract_field(payload, Field.PAGE),
            target_id=extract_field(payload, Field.TARGET_USER_ID),
            title_bag_id=extract_field(payload, Field.TITLE_BAG_ID),
        )
        message = call.message
        user_id = call.from_user.id
        chat_id = message.chat.id
        if user_id != callback_payload.user_id:
            self.bot_service.answer_callback_query(
                "Эти кнопки были не для тебя!", call.id
            )
            return
        if not self.try_sync_titles(chat_id, message.id, user_id):
            return
        match callback_payload.action:
            case Action.ROLL_RANDOM_D6:
                self.handle_random_dice_roll(call)
            case Action.ROLL_D6:
                self.handle_dice_roll(call, callback_payload.dice_value)
            case Action.OPEN_RENAME_MENU:
                self.handle_back_to_rename_menu(call)
            case Action.OPEN_STEAL_MENU:
                self.show_steal_menu(call, callback_payload.page)
            case Action.STEAL_TITLE:
                self.handle_steal(call, callback_payload.target_id)
            case Action.OPEN_TITLES_BAG:
                self.handle_show_titles_bag(call, callback_payload.page)
            case Action.SET_TITLE_BAG:
                self.handle_swap_title(call, callback_payload.title_bag_id)

    def has_titles_payload(self, call: CallbackQuery) -> bool:
        payload = parse_json(call.data)
        return payload.get(Field.ACTION_TYPE.value) in self._valid_payload_actions

import json
import logging

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from vasiniyo_chat_bot.module.titles.dto import (
    RenameMenu,
    StealMenu,
    StealSuccessResult,
    TitlesBagMenu,
)
from vasiniyo_chat_bot.telegram.bot_service import BotService, UserTemplate
from vasiniyo_chat_bot.telegram.dto import Action, Field


class TitlesRenderer:
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    def send_already_rolled(self, chat_id: int, message_id: int):
        self.bot_service.edit_message_text(
            "Ты уже роллял сегодня лычку!", chat_id, message_id
        )

    def send_please_set_title(self, title: str, chat_id: int, message_id: int):
        self.bot_service.send_message(
            f"Я не могу начать начать игру, пока ты не поможешь мне назначить твою лычку '{title}' 😳",
            chat_id,
            message_id,
        )

    def send_title_changed(self, title: str, chat_id: int, message_id: int):
        self.bot_service.send_message(
            f"Сегодня твой день! Изменила твою лычку на {title}!", chat_id, message_id
        )

    def send_title_changed_failed(self, title: str, chat_id: int, message_id: int):
        self.bot_service.edit_message_text_later(
            f"Сегодня твой день! Выпала лычка '{title}', но я не смогла её назначить. Выручай! 😳",
            chat_id,
            message_id,
        )

    def send_titles_restore(self, title: str, chat_id: int, message_id: int):
        self.bot_service.edit_message_text(
            f"Вернула твою прежнюю лычку {title}!", chat_id, message_id
        )

    def send_title_not_changed(self, chat_id: int, message_id: int):
        self.bot_service.edit_message_text_later(
            "Близко-близко! Но не совсем... Попробуй завтра! 🙂", chat_id, message_id
        )

    def _rename_menu_markup(self, rename_menu: RenameMenu, user_id: int):
        markup = InlineKeyboardMarkup()
        if rename_menu.d6:
            markup.row(
                *[
                    InlineKeyboardButton(
                        str(i), callback_data=self._create_d6_payload(str(i), user_id)
                    )
                    for i in range(1, 7)
                ]
            )
        if rename_menu.random_d6:
            markup.add(
                InlineKeyboardButton(
                    "Мне повезёт",
                    callback_data=json.dumps(
                        {
                            Field.ACTION_TYPE.value: Action.ROLL_RANDOM_D6.value,
                            Field.USER_ID.value: user_id,
                        }
                    ),
                )
            )
        if rename_menu.steal_menu:
            markup.add(
                InlineKeyboardButton(
                    "Кража", callback_data=self._create_steal_menu_payload(0, user_id)
                )
            )
        if rename_menu.titles_bag:
            markup.add(
                InlineKeyboardButton(
                    "Инвентарь",
                    callback_data=self._create_titles_bag_menu_payload(0, user_id),
                )
            )
        return markup

    def send_rename_menu(
        self, rename_menu: RenameMenu, chat_id: int, message_id: int, user_id: int
    ):
        self.bot_service.send_message(
            "Раз в день ты можешь испытать свою удачу и получить шанс поменять свою лычку!",
            chat_id,
            message_id,
            reply_markup=self._rename_menu_markup(rename_menu, user_id),
        )

    def back_to_rename_menu(
        self, rename_menu: RenameMenu, chat_id: int, message_id: int, user_id: int
    ):
        self.bot_service.edit_message_text(
            "Раз в день ты можешь испытать свою удачу и получить шанс поменять свою лычку!",
            chat_id,
            message_id,
            reply_markup=self._rename_menu_markup(rename_menu, user_id),
        )

    def send_steal_menu(
        self, steal_menu: StealMenu, chat_id: int, message_id: int, user_id: int
    ):
        page = steal_menu.page
        buttons = [
            InlineKeyboardButton(
                f"{title} | {target_username}",
                callback_data=self._create_steal_title_payload(target_user_id, user_id),
            )
            for target_username, target_user_id, title in [
                (
                    self.bot_service.get_username(chat_id, target_user_id),
                    target_user_id,
                    title,
                )
                for target_user_id, title in steal_menu.titles
                if target_user_id != user_id
            ]
        ]
        markup = InlineKeyboardMarkup()
        for button in buttons:
            markup.add(button)
        navigation = []
        if steal_menu.has_prev_pages:
            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=self._create_steal_menu_payload(page - 1, user_id),
                )
            )
        if steal_menu.has_more_pages:
            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=self._create_steal_menu_payload(page + 1, user_id),
                )
            )
        if navigation:
            markup.add(*navigation)
        markup.add(
            InlineKeyboardButton(
                "🟣 Вернуться", callback_data=self._create_rename_menu_payload(user_id)
            )
        )
        self.bot_service.edit_message_text(
            "Выбери лычку, которую хочешь украсть...",
            chat_id,
            message_id,
            reply_markup=markup,
        )

    def send_titles_bag(
        self, titles_bag: TitlesBagMenu, chat_id: int, message_id: int, user_id: int
    ):
        page = titles_bag.page
        buttons = [
            InlineKeyboardButton(
                title,
                callback_data=self._create_set_title_payload(title_bag_id, user_id),
            )
            for title_bag_id, title in titles_bag.titles
        ]
        markup = InlineKeyboardMarkup()
        for button in buttons:
            markup.add(button)
        navigation = []
        if titles_bag.has_prev_pages:
            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=self._create_titles_bag_menu_payload(
                        page - 1, user_id
                    ),
                )
            )
        if titles_bag.has_more_pages:
            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=self._create_titles_bag_menu_payload(
                        page + 1, user_id
                    ),
                )
            )
        if navigation:
            markup.add(*navigation)
        markup.add(
            InlineKeyboardButton(
                "🟣 Вернуться", callback_data=self._create_rename_menu_payload(user_id)
            )
        )
        self.bot_service.edit_message_text(
            "Лычки в инвентаре", chat_id, message_id, reply_markup=markup
        )

    def send_stolen_title(
        self,
        result: StealSuccessResult,
        chat_id: int,
        message_id: int,
        actor_title_are_set=True,
        target_title_are_set=True,
    ):
        failed = self._failed_set(
            [
                (chat_id, result.actor_id, result.actor_title, actor_title_are_set),
                (chat_id, result.target_id, result.target_title, target_title_are_set),
            ]
        )
        text_units = [
            "АХТУНГ, грабёж средь бела дня!!! ",
            UserTemplate(chat_id, result.actor_id),
            " украл у ",
            UserTemplate(chat_id, result.target_id),
            f" лычку: '{result.actor_title}'!\n",
            "Сегодня у пострадавшего будет шанс отыграться!\n",
            *failed,
        ]
        self.bot_service.edit_message_text_later(text_units, chat_id, message_id)

    @staticmethod
    def _failed_set(info: list[tuple[int, int, str, bool]]) -> list[str | UserTemplate]:
        failed_set = [
            (chat_id, user_id, title)
            for chat_id, user_id, title, are_setted in info
            if not are_setted
        ]
        if not failed_set:
            return [""]
        result = ["Я не смогла назначить лычки:"]
        for chat_id, user_id, title in failed_set:
            result.extend(["\n- ", UserTemplate(chat_id, user_id), f" | {title}"])
        return result

    def send_steal_failed(self, chat_id: int, message_id: int):
        self.bot_service.edit_message_text_later(
            "Жулик, не воруй!", chat_id, message_id
        )

    def send_swap_failed(self, title: str, chat_id: int, message_id: int):
        self.bot_service.send_message(
            f"У вас больше нет лычки '{title}'", chat_id, message_id
        )

    def send_swap_success(
        self,
        title: str,
        chat_id: int,
        message_id: int,
        user_id: int,
        are_set: bool = True,
    ):
        failed = self._failed_set([(chat_id, user_id, title, are_set)])
        self.bot_service.edit_message_text(
            [f"Изменила лычку на {title}\n", *failed], chat_id, message_id
        )

    @staticmethod
    def _create_titles_bag_menu_payload(page: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.OPEN_TITLES_BAG.value,
                Field.USER_ID.value: user_id,
                Field.PAGE.value: page,
            }
        )

    @staticmethod
    def _create_set_title_payload(title_bag_id: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.SET_TITLE_BAG.value,
                Field.USER_ID.value: user_id,
                Field.TITLE_BAG_ID.value: title_bag_id,
            }
        )

    @staticmethod
    def _create_d6_payload(i, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.ROLL_D6.value,
                Field.USER_ID.value: user_id,
                Field.DICE_VALUE.value: i,
            }
        )

    @staticmethod
    def _create_random_d6_payload(user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.ROLL_RANDOM_D6.value,
                Field.USER_ID.value: user_id,
            }
        )

    @staticmethod
    def _create_rename_menu_payload(user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.OPEN_RENAME_MENU.value,
                Field.USER_ID.value: user_id,
            }
        )

    @staticmethod
    def _create_steal_menu_payload(page: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.OPEN_STEAL_MENU.value,
                Field.USER_ID.value: user_id,
                Field.PAGE.value: page,
            }
        )

    @staticmethod
    def _create_steal_title_payload(target_id: int, user_id: int) -> str:
        return json.dumps(
            {
                Field.ACTION_TYPE.value: Action.STEAL_TITLE.value,
                Field.USER_ID.value: user_id,
                Field.TARGET_USER_ID.value: target_id,
            }
        )

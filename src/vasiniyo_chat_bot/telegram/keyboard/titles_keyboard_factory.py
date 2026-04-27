from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from vasiniyo_chat_bot.module.titles.dto import RenameMenu, StealMenu, TitleInfo
from vasiniyo_chat_bot.telegram.dto import Pageable, TitlesBagItemView
from vasiniyo_chat_bot.telegram.payload.titles_payload_factory import (
    TitlesPayloadFactory,
)


class TitlesKeyboardFactory:
    def __init__(self, payload_factory: TitlesPayloadFactory):
        self._payload_factory = payload_factory

    def rename_menu(
        self, rename_menu: RenameMenu, user_id: int
    ) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        if rename_menu.d6:
            markup.row(
                *[
                    InlineKeyboardButton(
                        str(i), callback_data=self._payload_factory.d6(str(i), user_id)
                    )
                    for i in range(1, 7)
                ]
            )
        if rename_menu.random_d6:
            markup.add(
                InlineKeyboardButton(
                    "Мне повезёт",
                    callback_data=self._payload_factory.random_d6(user_id),
                )
            )
        if rename_menu.steal_menu:
            markup.add(
                InlineKeyboardButton(
                    "Кража", callback_data=self._payload_factory.steal_menu(0, user_id)
                )
            )
        if rename_menu.titles_bag:
            markup.add(
                InlineKeyboardButton(
                    "Инвентарь",
                    callback_data=self._payload_factory.titles_bag_menu(0, user_id),
                )
            )
        return markup

    def title_steal(self, title_info: TitleInfo, user_id: int):
        username = title_info.username or "Забытый пользователь"
        icon = "" if title_info.is_inventory else "🔰"
        return InlineKeyboardButton(
            f"{icon} {title_info.title} | {username}",
            callback_data=self._payload_factory.steal_title(
                title_info.id, title_info.user_id, user_id
            ),
        )

    def inventory_title(self, item: TitlesBagItemView):
        return InlineKeyboardButton(
            item.title,
            callback_data=self._payload_factory.set_title_bag(
                item.titles_bag_id, item.user_id
            ),
        )

    def steal_menu(
        self, steal_menu: StealMenu, user_id: int, buttons: list[InlineKeyboardButton]
    ):
        markup = InlineKeyboardMarkup()
        for button in buttons:
            markup.add(button)
        navigation = self._steal_menu_navigation(steal_menu, user_id)
        if navigation:
            markup.add(*navigation)
        markup.add(self._rename_menu(user_id))
        return markup

    def titles_bag(
        self, titles_bag: Pageable, user_id: int, buttons: list[InlineKeyboardButton]
    ):
        markup = InlineKeyboardMarkup()
        for button in buttons:
            markup.add(button)
        navigation = self._bag_menu_navigation(titles_bag, user_id)
        if navigation:
            markup.add(*navigation)
        markup.add(self._rename_menu(user_id))
        return markup

    def _steal_menu_navigation(
        self, steal_menu: StealMenu, user_id: int
    ) -> list[InlineKeyboardButton]:
        navigation = []
        if steal_menu.has_prev_pages:
            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=self._payload_factory.steal_menu(
                        steal_menu.page - 1, user_id
                    ),
                )
            )
        if steal_menu.has_more_pages:
            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=self._payload_factory.steal_menu(
                        steal_menu.page + 1, user_id
                    ),
                )
            )
        return navigation

    def _bag_menu_navigation(
        self, titles_bag: Pageable, user_id: int
    ) -> list[InlineKeyboardButton]:
        navigation = []
        if titles_bag.has_prev_pages:
            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=self._payload_factory.titles_bag_menu(
                        titles_bag.page - 1, user_id
                    ),
                )
            )
        if titles_bag.has_more_pages:
            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=self._payload_factory.titles_bag_menu(
                        titles_bag.page + 1, user_id
                    ),
                )
            )
        return navigation

    def _rename_menu(self, user_id: int):
        return InlineKeyboardButton(
            "🟣 Вернуться", callback_data=self._payload_factory.rename_menu(user_id)
        )

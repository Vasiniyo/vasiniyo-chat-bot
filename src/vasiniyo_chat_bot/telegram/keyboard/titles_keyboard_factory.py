import logging

from black.trans import defaultdict
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from vasiniyo_chat_bot.module.titles.dto import (
    GiftRecipientInfo,
    GiftRecipientsMenu,
    GiftTitlesMenu,
    RenameMenu,
    StealMenu,
    TitleInfo,
)
from vasiniyo_chat_bot.telegram.dto import (
    Pageable,
    TitlesBagItemView,
    TitlesBagMenuView,
)
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
            title = f" | {rename_menu.title}" if rename_menu.title else ""
            markup.add(
                InlineKeyboardButton(
                    f"Мне повезёт{title}",
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
                    "Подарить лычку",
                    callback_data=self._payload_factory.gift_recipients_menu(
                        0, user_id
                    ),
                )
            )
            markup.add(
                InlineKeyboardButton(
                    "Инвентарь",
                    callback_data=self._payload_factory.titles_bag_menu(0, user_id),
                )
            )
        return markup

    def steal_menu(self, steal_menu: StealMenu, user_id: int):
        markup = InlineKeyboardMarkup()
        bts = defaultdict(list[TitleInfo])
        for item in steal_menu.titles:
            bts[item.user_id].append(item)
        for uid, arr in bts.items():
            groups = [arr[i : i + 2] for i in range(0, len(arr), 3)]
            if len(groups) == 1 and len(groups[0]) == 1:
                button = self._title_steal(groups[0][0], user_id, True)
                markup.add(button)
                continue
            markup.add(self._empty_button(arr[0].username or "Неизвестный"))
            for group in groups:
                buttons = [self._title_steal(item, user_id) for item in group]
                if len(buttons) == 1:
                    markup.add(*[*buttons, self._empty_button()])
                else:
                    markup.add(*buttons)
        navigation = self._steal_menu_navigation(steal_menu, user_id)
        if navigation:
            markup.add(*navigation)
        markup.add(self._rename_menu(user_id))
        return markup

    def gift_recipients_menu(self, menu: GiftRecipientsMenu, user_id: int):
        markup = InlineKeyboardMarkup()
        buttons = [self._gift_recipient(item, user_id) for item in menu.recipients]
        groups = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        for group in groups:
            markup.add(*group)
        navigation = self._gift_recipients_menu_navigation(menu, user_id)
        if navigation:
            markup.add(*navigation)
        markup.add(self._rename_menu(user_id))
        return markup

    def gift_titles_menu(self, menu: GiftTitlesMenu, user_id: int):
        markup = InlineKeyboardMarkup()
        buttons = [
            self._gift_title(item, menu.target_user_id, user_id) for item in menu.titles
        ]
        groups = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        for group in groups:
            markup.add(*group)
        navigation = self._gift_titles_menu_navigation(menu, user_id)
        if navigation:
            markup.add(*navigation)
        markup.add(self._rename_menu(user_id))
        return markup

    def titles_bag(self, titles_bag: TitlesBagMenuView, user_id: int):
        markup = InlineKeyboardMarkup()
        buttons = [self._inventory_title(item) for item in titles_bag.items]
        groups = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        for group in groups:
            markup.add(*group)
        navigation = self._bag_menu_navigation(titles_bag, user_id)
        if navigation:
            markup.add(*navigation)
        markup.add(self._rename_menu(user_id))
        return markup

    def _empty_button(self, text=" ") -> InlineKeyboardButton:
        return InlineKeyboardButton(text, callback_data=self._payload_factory.empty())

    def _title_steal(
        self, title_info: TitleInfo, user_id: int, with_username: bool = False
    ):
        icon = "" if title_info.is_inventory else " 🔰"
        if with_username:
            username = title_info.username or "Неизвестный"
            text = f"{username} |{icon} {title_info.title}"
        else:
            text = f"{icon} {title_info.title}"
        return InlineKeyboardButton(
            text,
            callback_data=self._payload_factory.steal_title(
                title_info.id, title_info.user_id, user_id
            ),
        )

    def _gift_recipient(self, recipient: GiftRecipientInfo, user_id: int):
        return InlineKeyboardButton(
            recipient.username or "Неизвестный",
            callback_data=self._payload_factory.gift_titles_menu(
                0, recipient.user_id, user_id
            ),
        )

    def _gift_title(self, title_info: TitleInfo, target_id: int, user_id: int):
        return InlineKeyboardButton(
            title_info.title,
            callback_data=self._payload_factory.give_title(
                title_info.id, target_id, user_id
            ),
        )

    def _inventory_title(self, item: TitlesBagItemView):
        return InlineKeyboardButton(
            item.title,
            callback_data=self._payload_factory.set_title_bag(
                item.titles_bag_id, item.user_id
            ),
        )

    def _gift_recipients_menu_navigation(
        self, gift_menu: GiftRecipientsMenu, user_id: int
    ) -> list[InlineKeyboardButton]:
        navigation = []
        if gift_menu.has_prev_pages:
            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=self._payload_factory.gift_recipients_menu(
                        gift_menu.page - 1, user_id
                    ),
                )
            )
        if gift_menu.has_more_pages:
            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=self._payload_factory.gift_recipients_menu(
                        gift_menu.page + 1, user_id
                    ),
                )
            )
        return navigation

    def _gift_titles_menu_navigation(
        self, menu: GiftTitlesMenu, user_id: int
    ) -> list[InlineKeyboardButton]:
        navigation = []
        if menu.has_prev_pages:
            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=self._payload_factory.gift_titles_menu(
                        menu.page - 1, menu.target_user_id, user_id
                    ),
                )
            )
        if menu.has_more_pages:
            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=self._payload_factory.gift_titles_menu(
                        menu.page + 1, menu.target_user_id, user_id
                    ),
                )
            )
        return navigation

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

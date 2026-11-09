from typing import Self

from black.trans import defaultdict
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import Pageable
from vasiniyo_chat_bot.module.payload_factory import PayloadFactory
from vasiniyo_chat_bot.module.titles.dto import ExchangeTitleMenu
from vasiniyo_chat_bot.module.titles.dto import FailedRollMenu
from vasiniyo_chat_bot.module.titles.dto import FailedStealMenu
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientInfo
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientsMenu
from vasiniyo_chat_bot.module.titles.dto import GiftTitlesMenu
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import StealMenu
from vasiniyo_chat_bot.module.titles.dto import TitleInfo
from vasiniyo_chat_bot.module.titles.dto import TitlesBagItemView
from vasiniyo_chat_bot.module.titles.dto import TitlesBagMenu


class TitlesKeyboardBuilder:
    def __init__(self, user_id: int):
        self._user_id = user_id
        self._markup = InlineKeyboardMarkup()

    def build(self) -> InlineKeyboardMarkup:
        return self._markup

    def d6(self) -> Self:
        self._markup.row(
            *[
                InlineKeyboardButton(
                    str(i),
                    callback_data=PayloadFactory.dump(
                        Action.ROLL_D6, self._user_id, dice_value=i
                    ),
                )
                for i in range(1, 7)
            ]
        )
        return self

    def random_d6(self, title: str | None) -> Self:
        title = f" | {title}" if title else ""
        self._markup.row(
            InlineKeyboardButton(
                f"Мне повезёт{title}",
                callback_data=PayloadFactory.dump(Action.ROLL_RANDOM_D6, self._user_id),
            )
        )
        return self

    def steal(self) -> Self:
        self._markup.row(
            InlineKeyboardButton(
                "Кража",
                callback_data=PayloadFactory.dump(
                    Action.OPEN_STEAL_MENU, self._user_id, page=0
                ),
            )
        )
        return self

    def gift(self) -> Self:
        self._markup.row(
            InlineKeyboardButton(
                "Подарить лычку",
                callback_data=PayloadFactory.dump(
                    Action.GIFT_RECIPIENTS_MENU, self._user_id, page=0
                ),
            )
        )
        return self

    def exchange(self) -> Self:
        self._markup.row(
            InlineKeyboardButton(
                "Распыление",
                callback_data=PayloadFactory.dump(
                    Action.OPEN_EXCHANGE_TITLE_MENU, self._user_id, page=0
                ),
            )
        )
        return self

    def inventory(self):
        self._markup.row(
            InlineKeyboardButton(
                "Инвентарь",
                callback_data=PayloadFactory.dump(
                    Action.OPEN_TITLES_BAG, self._user_id, page=0
                ),
            )
        )
        return self

    def reroll_steal(self, target_title: TitleInfo) -> Self:
        self._markup.row(
            InlineKeyboardButton(
                f"Реролл",
                callback_data=PayloadFactory.dump(
                    Action.STEAL_TITLE,
                    self._user_id,
                    title_id=target_title.id,
                    target_user_id=target_title.user_id,
                ),
            )
        )
        return self

    def reroll_dice(self, title: str) -> Self:
        self.d6().random_d6(title)
        return self

    def recipients(self, menu: GiftRecipientsMenu) -> Self:
        buttons = [self._recipient(item) for item in menu.recipients]
        for group in self._make_groups(buttons, 3):
            self._markup.add(*group)
        return self

    def navigation_recipients(self, gift_menu: GiftRecipientsMenu) -> Self:
        return self._nav_template(Action.GIFT_RECIPIENTS_MENU, gift_menu)

    def gift_menu(self, menu: GiftTitlesMenu) -> Self:
        buttons = [self._gift_item(item, menu.target_user_id) for item in menu.titles]
        for group in self._make_groups(buttons, 2):
            self._markup.add(*group)
        return self

    def navigation_gifts(self, menu: GiftTitlesMenu) -> Self:
        return self._nav_template(
            Action.GIFT_TITLE_MENU, menu, target_user_id=menu.target_user_id
        )

    def inventory_menu(self, titles_bag: TitlesBagMenu):
        buttons = [self._inventory_item(item) for item in titles_bag.items]
        for group in self._make_groups(buttons, 2):
            self._markup.add(*group)
        return self

    def navigation_inventory(self, titles_bag: TitlesBagMenu) -> Self:
        return self._nav_template(Action.OPEN_TITLES_BAG, titles_bag)

    def exchange_menu(self, titles_bag: ExchangeTitleMenu) -> Self:
        buttons = [self._exchange_title(item) for item in titles_bag.items]
        for group in self._make_groups(buttons, 2):
            self._markup.add(*group)
        return self

    def navigation_exchange(self, pageable: Pageable) -> Self:
        return self._nav_template(Action.OPEN_EXCHANGE_TITLE_MENU, pageable)

    def steal_menu(self, steal_menu: StealMenu) -> Self:
        bts = defaultdict(list[TitleInfo])
        for item in steal_menu.titles:
            bts[item.user_id].append(item)
        for uid, arr in bts.items():
            groups = self._make_groups(arr, 2)
            if len(groups) == 1 and len(groups[0]) == 1:
                button = self._steal_item(groups[0][0], self._user_id, True)
                self._markup.add(button)
                continue
            self._markup.add(self._empty_button(arr[0].username or "Неизвестный"))
            for group in groups:
                buttons = [self._steal_item(item, self._user_id) for item in group]
                if len(buttons) == 1:
                    self._markup.add(*[*buttons, self._empty_button()])
                else:
                    self._markup.add(*buttons)
        return self

    def navigation_steal(self, steal_menu: StealMenu) -> Self:
        return self._nav_template(Action.OPEN_STEAL_MENU, steal_menu)

    def _empty_button(self, text=" ") -> InlineKeyboardButton:
        return InlineKeyboardButton(text, callback_data=PayloadFactory.dump_empty())

    @staticmethod
    def _steal_item(title_info: TitleInfo, user_id: int, with_username: bool = False):
        icon = "" if title_info.is_inventory else " 🔰"
        if with_username:
            username = title_info.username or "Неизвестный"
            text = f"{username} |{icon} {title_info.title}"
        else:
            text = f"{icon} {title_info.title}"
        return InlineKeyboardButton(
            text,
            callback_data=PayloadFactory.dump(
                Action.STEAL_TITLE,
                user_id,
                title_id=title_info.id,
                target_user_id=title_info.user_id,
            ),
        )

    def _make_groups(self, buttons: list, step: int):
        return [buttons[i : i + step] for i in range(0, len(buttons), step)]

    def _nav_template(self, action: Action, pageable: Pageable, **payload) -> Self:
        navigation = []
        if pageable.has_prev_pages:
            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=PayloadFactory.dump(
                        action, self._user_id, page=pageable.page - 1, **payload
                    ),
                )
            )
        if pageable.has_more_pages:
            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=PayloadFactory.dump(
                        action, self._user_id, page=pageable.page + 1, **payload
                    ),
                )
            )
        self._markup.add(*navigation)
        if pageable.has_return_button:
            self._markup.add(
                InlineKeyboardButton(
                    "🟣 Вернуться",
                    callback_data=PayloadFactory.dump(
                        Action.OPEN_RENAME_MENU, self._user_id
                    ),
                )
            )
        return self

    @staticmethod
    def _exchange_title(item: TitlesBagItemView) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            item.title,
            callback_data=PayloadFactory.dump(
                Action.EXCHANGE_TITLE, item.user_id, title_id=item.titles_bag_id
            ),
        )

    @staticmethod
    def _inventory_item(item: TitlesBagItemView):
        return InlineKeyboardButton(
            item.title,
            callback_data=PayloadFactory.dump(
                Action.SET_TITLE_BAG, item.user_id, title_id=item.titles_bag_id
            ),
        )

    def _gift_item(self, title_info: TitleInfo, target_id: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            title_info.title,
            callback_data=PayloadFactory.dump(
                Action.GIVE_TITLE,
                self._user_id,
                target_user_id=target_id,
                title_id=title_info.id,
            ),
        )

    def _recipient(self, recipient: GiftRecipientInfo):
        return InlineKeyboardButton(
            recipient.username or "Неизвестный",
            callback_data=PayloadFactory.dump(
                Action.GIFT_TITLE_MENU,
                self._user_id,
                target_user_id=recipient.user_id,
                page=0,
            ),
        )


class TitlesKeyboardFactory:
    @staticmethod
    def rename_menu(rename_menu: RenameMenu, user_id: int) -> InlineKeyboardMarkup:
        builder = TitlesKeyboardBuilder(user_id)
        if rename_menu.has_d6_menu:
            builder = builder.d6()
        if rename_menu.has_random_d6_menu:
            builder = builder.random_d6(rename_menu.rolling_title)
        if rename_menu.has_steal_menu:
            builder = builder.steal()
        if rename_menu.has_titles_bag_menu:
            builder = builder.gift()
            if rename_menu.has_exchange_menu:
                builder = builder.exchange()
            builder = builder.inventory()
        return builder.build()

    @staticmethod
    def steal_menu(steal_menu: StealMenu, user_id: int) -> InlineKeyboardMarkup:
        return (
            TitlesKeyboardBuilder(user_id)
            .steal_menu(steal_menu)
            .navigation_steal(steal_menu)
            .build()
        )

    @staticmethod
    def failed_steal(menu: FailedStealMenu, user_id: int) -> InlineKeyboardMarkup:
        if menu.has_exchange_menu:
            return TitlesKeyboardBuilder(user_id).exchange().build()
        if menu.extra_attempts > 0:
            return (
                TitlesKeyboardBuilder(user_id).reroll_steal(menu.target_title).build()
            )
        return TitlesKeyboardBuilder(user_id).build()

    @staticmethod
    def failed_roll(menu: FailedRollMenu, user_id: int) -> InlineKeyboardMarkup:
        if menu.has_exchange_menu:
            return TitlesKeyboardBuilder(user_id).exchange().build()
        if menu.extra_attempts > 0:
            return TitlesKeyboardBuilder(user_id).reroll_dice(menu.title).build()
        return TitlesKeyboardBuilder(user_id).build()

    @staticmethod
    def recipients_menu(menu: GiftRecipientsMenu, user_id: int) -> InlineKeyboardMarkup:
        return (
            TitlesKeyboardBuilder(user_id)
            .recipients(menu)
            .navigation_recipients(menu)
            .build()
        )

    @staticmethod
    def gift_menu(menu: GiftTitlesMenu, user_id: int) -> InlineKeyboardMarkup:
        return (
            TitlesKeyboardBuilder(user_id)
            .gift_menu(menu)
            .navigation_gifts(menu)
            .build()
        )

    @staticmethod
    def inventory_menu(titles_bag: TitlesBagMenu, user_id: int) -> InlineKeyboardMarkup:
        return (
            TitlesKeyboardBuilder(user_id)
            .inventory_menu(titles_bag)
            .navigation_inventory(titles_bag)
            .build()
        )

    @staticmethod
    def exchange_menu(exchanged_title: ExchangeTitleMenu, user_id: int):
        return (
            TitlesKeyboardBuilder(user_id)
            .exchange_menu(exchanged_title)
            .navigation_exchange(exchanged_title)
            .build()
        )

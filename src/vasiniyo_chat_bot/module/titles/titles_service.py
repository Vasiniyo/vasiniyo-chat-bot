from typing import Callable

from vasiniyo_chat_bot.module.titles.dto import GiftRecipientInfo
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientsMenu
from vasiniyo_chat_bot.module.titles.dto import GiftTitlesMenu
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import StealMenu
from vasiniyo_chat_bot.module.titles.dto import StealResult
from vasiniyo_chat_bot.module.titles.dto import TitleChanged
from vasiniyo_chat_bot.module.titles.dto import TitleInfo
from vasiniyo_chat_bot.module.titles.dto import TitlesBagItemView
from vasiniyo_chat_bot.module.titles.dto import TitlesBagMenu
from vasiniyo_chat_bot.module.titles.titles_provider import TitlesProvider
from vasiniyo_chat_bot.module.titles.titles_repository import TitlesRepository
from vasiniyo_chat_bot.safely_bot_utils import daily_hash


class TitlesService:
    _rolling_titles = {}

    def __init__(
        self, titles_provider: TitlesProvider, titles_repository: TitlesRepository
    ):
        self._titles_provider = titles_provider
        self._titles_repository = titles_repository

    def get_user_title(self, chat_id, user_id):
        return self._titles_repository.find_user_title(chat_id, user_id)

    def rename(self, chat_id: int, user_id: int) -> TitleChanged | RenameMenu:
        title = self._get_next_title(chat_id, user_id)
        inited_title = self._titles_repository.init_title(chat_id, user_id, title)
        if inited_title:
            self._remove_next_title(chat_id, user_id)
            return TitleChanged(title=title, changed=True)
        return self.show_rename_menu(chat_id, user_id)

    def show_rename_menu(self, chat_id: int, user_id: int) -> RenameMenu:
        if self.is_day_passed(chat_id, user_id):
            title = self._get_next_title(chat_id, user_id)
            return RenameMenu(
                title=title, d6=True, random_d6=True, steal_menu=True, titles_bag=True
            )
        return RenameMenu(
            title=None, d6=False, random_d6=False, steal_menu=False, titles_bag=True
        )

    def show_steal_menu(
        self, chat_id: int, user_id: int, page: int, page_size: int
    ) -> StealMenu | RenameMenu:
        page = page if page > 0 else 0
        if not self.is_day_passed(chat_id, user_id):
            return RenameMenu(
                title=None, d6=False, random_d6=False, steal_menu=False, titles_bag=True
            )
        rows = list(self._titles_repository.get_user_titles(chat_id))
        counts = {}
        for r in rows:
            counts[r.user_id] = counts.get(r.user_id, 0) + 1
        titles = [
            TitleInfo(
                id=row.id,
                user_id=row.user_id,
                title=row.user_title,
                is_inventory=row.is_inventory,
            )
            for row in sorted(
                rows,
                key=lambda row: (
                    -counts[row.user_id],
                    row.user_id,
                    row.is_inventory,
                    row.user_title,
                ),
            )
            if row.user_id != user_id
        ]
        start_page = page * page_size
        end_page = start_page + page_size
        return StealMenu(
            chat_id=chat_id,
            titles=titles[start_page:end_page],
            page=page,
            has_prev_pages=page > 0,
            has_more_pages=end_page < len(titles),
        )

    def handle_steal(
        self, chat_id: int, user_id: int, title_id: int, success: bool
    ) -> StealResult:
        if success:
            result = self._titles_repository.steal_logic(chat_id, user_id, title_id)
            (actor_id, actor_title), (target_id, target_title) = result
            target_title = target_title or "украдено"
        else:
            actor_title, target_id, target_title = None, None, None
            self._titles_repository.update_last_changing(chat_id, user_id)
        return StealResult(
            actor_id=user_id,
            target_id=target_id,
            target_title=target_title,
            actor_title=actor_title,
            changed=success,
        )

    def handle_roll(self, chat_id: int, user_id: int, success: bool) -> TitleChanged:
        if success:
            next_title = self._get_next_title(chat_id, user_id)
            title = self._titles_repository.rotate_title(chat_id, user_id, next_title)
            self._remove_next_title(chat_id, user_id)
        else:
            title = self._titles_repository.get_title_after_touch(chat_id, user_id)
        return TitleChanged(title=title, changed=success)

    def handle_show_titles_bag(
        self, chat_id: int, user_id: int, page: int, page_size: int
    ) -> TitlesBagMenu:
        page = page if page > 0 else 0
        titles = [
            row.value
            for row in self._titles_repository.get_user_titles_bag(
                chat_id, user_id
            ).rows
        ]
        start_page = page * page_size
        end_page = start_page + page_size
        return TitlesBagMenu(
            items=[
                TitlesBagItemView(
                    user_id=user_id, titles_bag_id=title_bag_id, title=title
                )
                for title_bag_id, user_id, title in titles[start_page:end_page]
            ],
            page=page,
            has_prev_pages=page > 0,
            has_more_pages=end_page < len(titles),
        )

    def handle_swap_title(
        self, chat_id: int, user_id: int, title_bag_id: int
    ) -> TitleChanged:
        swapped_title = self._titles_repository.set_current(
            chat_id, user_id, title_bag_id
        )
        return TitleChanged(swapped_title, changed=swapped_title is not None)

    def get_gift_recipients(
        self,
        chat_id: int,
        user_id: int,
        page: int,
        page_size: int,
        get_username: Callable[[int], str],
    ) -> GiftRecipientsMenu:
        page = page if page > 0 else 0
        users = {
            user_id: get_username(user_id)
            for user_id in set(self._titles_repository.get_users_by_chat(chat_id))
        }
        recipients = sorted(
            [
                GiftRecipientInfo(uid, username)
                for uid, username in users.items()
                if uid != user_id and username
            ],
            key=lambda row: row.user_id,
        )
        start_page = page * page_size
        end_page = start_page + page_size
        return GiftRecipientsMenu(
            chat_id=chat_id,
            recipients=recipients[start_page:end_page],
            page=page,
            has_prev_pages=page > 0,
            has_more_pages=end_page < len(recipients),
        )

    def get_gift_titles(
        self, chat_id: int, user_id: int, target_id: int, page: int, page_size: int
    ) -> GiftTitlesMenu:
        page = page if page > 0 else 0
        titles = [
            TitleInfo(
                id=row.value[0],
                user_id=row.value[1],
                title=row.value[2],
                is_inventory=True,
            )
            for row in sorted(
                self._titles_repository.get_user_titles_bag(chat_id, user_id).rows,
                key=lambda row: row.value[2],
            )
        ]
        start_page = page * page_size
        end_page = start_page + page_size
        return GiftTitlesMenu(
            chat_id=chat_id,
            target_user_id=target_id,
            titles=titles[start_page:end_page],
            page=page,
            has_prev_pages=page > 0,
            has_more_pages=end_page < len(titles),
        )

    def give_title(self, chat_id: int, user_id: int, title_bag_id: int) -> TitleChanged:
        title = self._titles_repository.set_inventory(chat_id, user_id, title_bag_id)
        return TitleChanged(title, changed=title is not None)

    def is_valid_title(self, chat_id: int, user_id: int, title_bag_id: int) -> bool:
        return self._titles_repository.exists(chat_id, user_id, title_bag_id)

    def is_day_passed(self, chat_id: int, user_id: int) -> bool:
        return self._titles_repository.is_day_passed(chat_id, user_id)

    def _get_next_title(self, chat_id: int, user_id: int):
        key = daily_hash(chat_id + user_id)
        if not self._rolling_titles.get(key):
            self._rolling_titles[key] = self._titles_provider.next_title()
        return self._rolling_titles[key]

    def _remove_next_title(self, chat_id: int, user_id: int):
        self._rolling_titles.pop(daily_hash(chat_id + user_id))

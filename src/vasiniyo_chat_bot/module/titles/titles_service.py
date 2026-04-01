from vasiniyo_chat_bot.module.titles.dto import (
    RenameMenu,
    StealMenu,
    StealSuccessResult,
    TitleChanged,
    TitlesBagMenu,
)
from vasiniyo_chat_bot.module.titles.titles_provider import TitlesProvider
from vasiniyo_chat_bot.module.titles.titles_repository import TitlesRepository


class TitlesService:
    def __init__(
        self, titles_provider: TitlesProvider, titles_repository: TitlesRepository
    ):
        self.titles_provider = titles_provider
        self.titles_repository = titles_repository

    def get_user_title(self, chat_id, user_id):
        return self.titles_repository.find_user_title(chat_id, user_id)

    def rename(self, chat_id: int, user_id: int) -> TitleChanged | RenameMenu:
        title = self.titles_provider.next_title()
        inited_title = self.titles_repository.init_title(chat_id, user_id, title)
        if inited_title:
            return TitleChanged(title=title, changed=True)
        return self.show_rename_menu(chat_id, user_id)

    def show_rename_menu(self, chat_id: int, user_id: int) -> RenameMenu:
        if self.is_day_passed(chat_id, user_id):
            return RenameMenu(d6=True, random_d6=True, steal_menu=True, titles_bag=True)
        return RenameMenu(d6=False, random_d6=False, steal_menu=False, titles_bag=True)

    def show_steal_menu(
        self, chat_id: int, user_id: int, page: int, page_size: int
    ) -> StealMenu | RenameMenu:
        page = page if page > 0 else 0
        if not self.is_day_passed(chat_id, user_id):
            return RenameMenu(
                d6=False, random_d6=False, steal_menu=False, titles_bag=True
            )
        titles = [
            (row.user_id, row.value)
            for row in self.titles_repository.get_user_titles(chat_id).rows
        ]
        start_page = page * page_size
        end_page = start_page + page_size
        return StealMenu(
            titles=titles[start_page:end_page],
            page=page,
            has_prev_pages=page > 0,
            has_more_pages=end_page < len(titles),
        )

    def handle_steal(
        self, chat_id: int, actor_id: int, target_id: int, success: bool
    ) -> StealSuccessResult | None:
        if not success:
            self.titles_repository.update_last_changing(chat_id, actor_id)
            return None
        actor_title, target_title = self.titles_repository.steal_logic(
            chat_id, actor_id, target_id
        )
        target_title = target_title if target_title else "украдено"
        return StealSuccessResult(
            actor_id=actor_id,
            target_id=target_id,
            target_title=target_title,
            actor_title=actor_title,
        )

    def handle_roll(self, chat_id: int, user_id: int, success: bool) -> TitleChanged:
        if not success:
            return TitleChanged(
                title=self.titles_repository.get_title_after_touch(chat_id, user_id),
                changed=False,
            )
        title = self.titles_provider.next_title()
        return TitleChanged(
            title=self.titles_repository.rotate_title(chat_id, user_id, title),
            changed=True,
        )

    def handle_show_titles_bag(
        self, chat_id: int, user_id: int, page: int, page_size: int
    ) -> TitlesBagMenu:
        page = page if page > 0 else 0
        titles = [
            row.value
            for row in self.titles_repository.get_user_titles_bag(chat_id, user_id).rows
        ]
        start_page = page * page_size
        end_page = start_page + page_size
        return TitlesBagMenu(
            titles=titles[start_page:end_page],
            page=page,
            has_prev_pages=page > 0,
            has_more_pages=end_page < len(titles),
        )

    def handle_swap_title(
        self, chat_id: int, user_id: int, title_bag_id: int
    ) -> TitleChanged:
        swapped_title = self.titles_repository.swap_title(
            chat_id, user_id, title_bag_id
        )
        return TitleChanged(swapped_title, changed=swapped_title is not None)

    def is_day_passed(self, chat_id: int, user_id: int) -> bool:
        return self.titles_repository.is_day_passed(chat_id, user_id)

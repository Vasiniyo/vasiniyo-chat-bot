from typing import Callable

from injector import inject
from sqlalchemy.orm import Session

from vasiniyo_chat_bot.database.database import Database
from vasiniyo_chat_bot.database.entity.title_entity import TitlesStateEntity
from vasiniyo_chat_bot.database.repository.titles_bag_repository import (
    TitlesBagRepository,
)
from vasiniyo_chat_bot.database.repository.titles_bag_repository import TitlesBagEntity
from vasiniyo_chat_bot.database.repository.titles_states_repository import (
    TitlesStatesRepository,
)
from vasiniyo_chat_bot.module.titles.dto import ExchangeTitleMenu
from vasiniyo_chat_bot.module.titles.dto import FailedRollMenu
from vasiniyo_chat_bot.module.titles.dto import FailedStealMenu
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientInfo
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientsMenu
from vasiniyo_chat_bot.module.titles.dto import GiftTitlesMenu
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import StealMenu
from vasiniyo_chat_bot.module.titles.dto import SuccessSteal
from vasiniyo_chat_bot.module.titles.dto import Title
from vasiniyo_chat_bot.module.titles.dto import TitleExchanged
from vasiniyo_chat_bot.module.titles.dto import TitleInfo
from vasiniyo_chat_bot.module.titles.dto import TitlesBagItemView
from vasiniyo_chat_bot.module.titles.dto import TitlesBagMenu
from vasiniyo_chat_bot.module.titles.titles_provider import TitlesProvider
from vasiniyo_chat_bot.safely_bot_utils import daily_hash


@inject
class TitlesService:
    _rolling_titles: dict[int, str] = {}

    def __init__(
        self,
        titles_provider: TitlesProvider,
        titles_states_repository: TitlesStatesRepository,
        titles_bag_repository: TitlesBagRepository,
        database: Database,
    ):
        self._titles_provider = titles_provider
        self._titles_states_repository = titles_states_repository
        self._titles_bag_repository = titles_bag_repository
        self._database = database

    def get_user_title(self, chat_id: int, user_id: int) -> str | None:
        with self._database.session() as session:
            with session.begin():
                title = self._titles_bag_repository.find_active_title(
                    session, chat_id, user_id
                )
                return title.user_title if title else None

    def rename(self, chat_id: int, user_id: int) -> Title | RenameMenu:
        with self._database.session() as session:
            with session.begin():
                if self._titles_bag_repository.find_active_title(
                    session, chat_id, user_id
                ):
                    return self.show_rename_menu(chat_id, user_id)
                bag_entity = TitlesBagEntity(
                    chat_id=chat_id,
                    user_id=user_id,
                    user_title=self._get_next_title(chat_id, user_id),
                    is_inventory=False,
                )
                state_entity = self._titles_states_repository.find_by_id(
                    session, chat_id, user_id
                )
                if not state_entity:
                    state_entity = TitlesStateEntity(
                        chat_id=chat_id, user_id=user_id, last_changing=0
                    )
                self._titles_states_repository.save(session, state_entity)
                entity = self._titles_bag_repository.save(session, bag_entity)
                self._remove_next_title(chat_id, user_id)
                return Title(user_id=entity.user_id, value=entity.user_title)

    def show_rename_menu(self, chat_id: int, user_id: int) -> RenameMenu:
        with self._database.session() as session:
            with session.begin():
                inv_titles = self._titles_bag_repository.get_inventory_titles(
                    session, chat_id, user_id
                )
                if self.is_roll_remaining(chat_id, user_id):
                    title = self._get_next_title(chat_id, user_id)
                    return RenameMenu(
                        rolling_title=title,
                        has_d6_menu=True,
                        has_random_d6_menu=True,
                        has_steal_menu=True,
                        has_exchange_menu=bool(len(inv_titles)),
                        has_titles_bag_menu=bool(len(inv_titles)),
                    )
                return RenameMenu(
                    rolling_title=None,
                    has_d6_menu=False,
                    has_random_d6_menu=False,
                    has_steal_menu=False,
                    has_exchange_menu=bool(len(inv_titles)),
                    has_titles_bag_menu=bool(len(inv_titles)),
                )

    def show_steal_menu(
        self, chat_id: int, user_id: int, page: int, page_size: int
    ) -> StealMenu | RenameMenu:
        page = page if page > 0 else 0
        with self._database.session() as session:
            with session.begin():
                inv_titles = self._titles_bag_repository.get_inventory_titles(
                    session, chat_id, user_id
                )
                if not self.is_roll_remaining(chat_id, user_id):
                    return RenameMenu(
                        rolling_title=None,
                        has_d6_menu=False,
                        has_random_d6_menu=False,
                        has_steal_menu=False,
                        has_exchange_menu=bool(len(inv_titles)),
                        has_titles_bag_menu=bool(len(inv_titles)),
                    )
                rows = self._titles_bag_repository.get_by_chat(session, chat_id)
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
                    if row.id is not None
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

    def _update_attempt(
        self, session: Session, chat_id: int, user_id: int
    ) -> TitlesStateEntity:
        states_entity = self._titles_states_repository.find_by_id(
            session, chat_id, user_id
        )
        if states_entity is None:
            return self._titles_states_repository.save(
                session, TitlesStateEntity(chat_id=chat_id, user_id=user_id)
            )
        if self._titles_states_repository.is_day_passed(session, states_entity):
            self._titles_states_repository.consume_daily_roll(session, states_entity)
        else:
            self._titles_states_repository.set_extra_rolls(
                session, states_entity, max(0, states_entity.extra_rolls - 1)
            )
        return states_entity

    def handle_failed_steal(
        self, chat_id: int, user_id: int, title_id: int
    ) -> FailedStealMenu:
        with self._database.session() as session:
            with session.begin():
                inv_titles = self._titles_bag_repository.get_inventory_titles(
                    session, chat_id, user_id
                )
                bag_entity = self._titles_bag_repository.find_by_id(session, title_id)
                states_entity = self._update_attempt(session, chat_id, user_id)
                title_user_id = bag_entity.user_id if bag_entity else None
                user_title = bag_entity.user_title if bag_entity else None
                return FailedStealMenu(
                    chat_id=chat_id,
                    user_id=user_id,
                    extra_attempts=states_entity.extra_rolls,
                    target_title=TitleInfo(
                        id=bag_entity.id,
                        user_id=title_user_id,
                        title=user_title,
                        is_inventory=bag_entity.is_inventory,
                        username=None,
                    ),
                    has_exchange_menu=bool(len(inv_titles))
                    and states_entity.extra_rolls == 0,
                )

    def handle_steal(
        self, chat_id: int, user_id: int, title_id: int
    ) -> SuccessSteal | None:
        with self._database.session() as session:
            with session.begin():
                target_title = self._titles_bag_repository.find_by_id(session, title_id)
                if target_title is None or target_title.user_id == user_id:
                    return None
                target_user_id = target_title.user_id
                self._titles_bag_repository.transfer(session, target_title, user_id)
                self._titles_states_repository.consume_daily_roll(
                    session, TitlesStateEntity(chat_id=chat_id, user_id=target_user_id)
                )
                self._update_attempt(session, chat_id, user_id)
                new_title = self._titles_bag_repository.find_active_title(
                    session, chat_id, target_user_id
                )
                return SuccessSteal(
                    actor_title=Title(user_id=user_id, value=target_title.user_title),
                    target_title=Title(
                        user_id=target_user_id,
                        value=new_title.user_title if new_title else None,
                    ),
                )

    def handle_failed_roll(self, chat_id: int, user_id: int) -> FailedRollMenu:
        with self._database.session() as session:
            with session.begin():
                inv_titles = self._titles_bag_repository.get_inventory_titles(
                    session, chat_id, user_id
                )
                states_entity = self._update_attempt(session, chat_id, user_id)
                return FailedRollMenu(
                    title=self._get_next_title(chat_id, user_id),
                    extra_attempts=states_entity.extra_rolls,
                    has_exchange_menu=bool(len(inv_titles))
                    and states_entity.extra_rolls == 0,
                )

    def handle_success_roll(self, chat_id: int, user_id: int) -> Title:
        with self._database.session() as session:
            with session.begin():
                self._update_attempt(session, chat_id, user_id)
                title = TitlesBagEntity(
                    chat_id=chat_id,
                    user_id=user_id,
                    user_title=self._get_next_title(chat_id, user_id),
                    is_inventory=True,
                )
                self._titles_bag_repository.save(session, title)
                self._remove_next_title(chat_id, user_id)
                return Title(user_id=user_id, value=title.user_title)

    def handle_show_titles_bag(
        self, chat_id: int, user_id: int, page: int, page_size: int
    ) -> TitlesBagMenu:
        with self._database.session() as session:
            with session.begin():
                page = page if page > 0 else 0
                titles = self._titles_bag_repository.get_inventory_titles(
                    session, chat_id, user_id
                )
                start_page = page * page_size
                end_page = start_page + page_size
                return TitlesBagMenu(
                    items=[
                        TitlesBagItemView(
                            user_id=user_id,
                            titles_bag_id=entity.id,
                            title=entity.user_title,
                        )
                        for entity in titles[start_page:end_page]
                    ],
                    page=page,
                    has_prev_pages=page > 0,
                    has_more_pages=end_page < len(titles),
                )

    def handle_exchange_title(
        self,
        chat_id: int,
        user_id: int,
        page: int,
        page_size: int,
        *,
        has_return_button: bool,
    ) -> ExchangeTitleMenu:
        menu = self.handle_show_titles_bag(chat_id, user_id, page, page_size)
        return ExchangeTitleMenu(
            items=menu.items,
            page=menu.page,
            has_prev_pages=menu.has_prev_pages,
            has_more_pages=menu.has_more_pages,
            has_return_button=has_return_button,
        )

    def handle_swap_title(self, title_bag_id: int) -> str | None:
        with self._database.session() as session:
            with session.begin():
                title = self._titles_bag_repository.find_by_id(session, title_bag_id)
                if title:
                    self._titles_bag_repository.set_active(session, title)
                    return title.user_title
                return None

    def get_gift_recipients(
        self,
        chat_id: int,
        user_id: int,
        page: int,
        page_size: int,
        get_username: Callable[[int], str | None],
    ) -> GiftRecipientsMenu:
        with self._database.session() as session:
            with session.begin():
                page = page if page > 0 else 0
                users = {
                    title.user_id: get_username(title.user_id)
                    for title in self._titles_bag_repository.get_by_chat(
                        session, chat_id
                    )
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
        with self._database.session() as session:
            with session.begin():
                page = page if page > 0 else 0
                titles = [
                    TitleInfo(
                        id=title.id,
                        user_id=title.user_id,
                        title=title.user_title,
                        is_inventory=title.is_inventory,
                    )
                    for title in sorted(
                        self._titles_bag_repository.get_inventory_titles(
                            session, chat_id, user_id
                        ),
                        key=lambda title: title.user_title,
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

    def give_title(self, user_id: int, title_bag_id: int) -> str | None:
        with self._database.session() as session:
            with session.begin():
                title = self._titles_bag_repository.find_by_id(session, title_bag_id)
                if title:
                    self._titles_bag_repository.transfer(session, title, user_id)
                    return title.user_title
                return None

    def exchange_title(
        self, chat_id: int, user_id: int, title_bag_id: int
    ) -> TitleExchanged | None:
        with self._database.session() as session:
            with session.begin():
                title = self._titles_bag_repository.find_by_id(session, title_bag_id)
                states_entity = self._titles_states_repository.find_by_id(
                    session, chat_id, user_id
                )
                if (
                    not states_entity
                    or not title
                    or not self._titles_bag_repository.remove(session, title)
                ):
                    return None
                self._titles_states_repository.set_extra_rolls(
                    session, states_entity, states_entity.extra_rolls + 1
                )
                return TitleExchanged(
                    titles=[title.user_title], extra_rolls=states_entity.extra_rolls
                )

    def is_valid_title(self, chat_id: int, user_id: int, title_bag_id: int) -> bool:
        with self._database.session() as session:
            with session.begin():
                title = self._titles_bag_repository.find_by_id(session, title_bag_id)
                return (
                    title is not None
                    and title.chat_id == chat_id
                    and title.user_id == user_id
                )

    def is_roll_remaining(self, chat_id: int, user_id: int) -> bool:
        with self._database.session() as session:
            with session.begin():
                state_entity = self._titles_states_repository.find_by_id(
                    session, chat_id, user_id
                )
                return state_entity is not None and (
                    self._titles_states_repository.is_day_passed(session, state_entity)
                    or state_entity.extra_rolls > 0
                )

    def _get_next_title(self, chat_id: int, user_id: int):
        key = daily_hash(chat_id + user_id)
        if not self._rolling_titles.get(key):
            self._rolling_titles[key] = self._titles_provider.next_title()
        return self._rolling_titles[key]

    def _remove_next_title(self, chat_id: int, user_id: int):
        self._rolling_titles.pop(daily_hash(chat_id + user_id))

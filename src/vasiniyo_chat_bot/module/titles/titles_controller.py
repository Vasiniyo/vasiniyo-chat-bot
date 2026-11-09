from __future__ import annotations

from dataclasses import replace
from functools import wraps
import logging

from black.trans import defaultdict
from injector import inject

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.titles.dice_service import DiceService
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import Title
from vasiniyo_chat_bot.module.titles.titles_response_factory import (
    TitlesResponseFactory,
)
from vasiniyo_chat_bot.module.titles.titles_response_factory import SetResult
from vasiniyo_chat_bot.module.titles.titles_service import TitlesService
from vasiniyo_chat_bot.module.user_service import UserService

_logger = logging.getLogger(__name__)


def _require_daily_action(func):
    @wraps(func)
    def wrapper(self: TitlesController, ctx: CallbackContext, *args, **kwargs):
        if self._titles_service.is_roll_remaining(ctx.chat_id, ctx.user_id):
            return func(self, ctx, *args, **kwargs)
        response = self._response_factory.already_rolled()
        self._renderer.edit(response, ctx)
        return None

    return wrapper


@inject
class TitlesController:
    def __init__(
        self,
        titles_service: TitlesService,
        dice_service: DiceService,
        user_service: UserService,
        response_factory: TitlesResponseFactory,
        renderer: Renderer,
    ):
        self._titles_service = titles_service
        self._dice_service = dice_service
        self._user_service = user_service
        self._response_factory = response_factory
        self._renderer = renderer

    def try_sync_titles(self, db_title: str | None, ctx: UserContext) -> str | None:
        if not db_title:
            db_title = self._user_service.set_default_title(ctx)
        tg_title = self._user_service.get_title(ctx)
        if db_title and tg_title != db_title:
            tg_title = self._user_service.set_title(ctx, db_title)
        return tg_title

    def handle_rename(self, ctx: CallbackContext):
        db_title = self._titles_service.get_user_title(ctx.chat_id, ctx.user_id)
        if db_title and not self.try_sync_titles(db_title, ctx):
            _logger.warning(
                "title_not_set",
                extra={
                    "chat_id": ctx.chat_id,
                    "user_id": ctx.user_id,
                    "title": db_title,
                },
            )
            response = self._response_factory.please_set_title(db_title)
            self._renderer.send(response, ctx)
            return
        result = self._titles_service.rename(ctx.chat_id, ctx.user_id)
        if isinstance(result, Title):
            response = self._set_title(result, ctx)
            self._renderer.send(response, ctx)
            return
        response = self._response_factory.rename_menu(result)
        self._renderer.send(response, ctx)

    def dispatch_titles_callback(self, ctx: CallbackContext):
        def _require(field: str) -> int:
            value = getattr(payload, field)
            if value is None:
                _logger.error("%s not set", field, extra={"payload": payload})
                raise ValueError(f"{field} not set")
            return value

        payload = ctx.payload
        user_id = _require("user_id")
        if payload is None or ctx.user_id != user_id:
            response = self._response_factory.no_access()
            self._renderer.alert(response, ctx)
            return
        db_title = self._titles_service.get_user_title(ctx.chat_id, user_id)
        if not self.try_sync_titles(db_title, ctx):
            if not db_title:
                _logger.warning(
                    "title_not_set", extra={"chat_id": ctx.chat_id, "user_id": user_id}
                )
                return
            response = self._response_factory.please_set_title(db_title)
            self._renderer.edit(response, ctx)
            return
        match payload.action:
            case Action.ROLL_RANDOM_D6:
                self._handle_random_dice_roll(ctx)
            case Action.ROLL_D6:
                self._handle_dice_roll(ctx, _require("dice_value"))
            case Action.OPEN_RENAME_MENU:
                self._handle_back_to_rename_menu(ctx)
            case Action.OPEN_STEAL_MENU:
                self._show_steal_menu(ctx, _require("page"))
            case Action.STEAL_TITLE:
                self._handle_steal(ctx, _require("target_id"), _require("title_bag_id"))
            case Action.OPEN_TITLES_BAG:
                self._handle_show_titles_bag(ctx, _require("page"))
            case Action.SET_TITLE_BAG:
                self._handle_swap_title(ctx, _require("title_bag_id"))
            case Action.GIFT_RECIPIENTS_MENU:
                self._handle_show_recipients_menu(ctx, _require("page"))
            case Action.GIFT_TITLE_MENU:
                self._handle_show_gift_title_menu(
                    ctx, _require("target_id"), _require("page")
                )
            case Action.GIVE_TITLE:
                self._give_title(ctx, _require("target_id"), _require("title_bag_id"))
            case Action.OPEN_EXCHANGE_TITLE_MENU:
                self._exchange_title_menu(ctx, _require("page"))
            case Action.EXCHANGE_TITLE:
                self._handle_exchange_title(ctx, _require("title_bag_id"))

    def _set_title(self, title: Title, ctx: CallbackContext) -> Response:
        value = title.value or ""
        are_set = self._user_service.set_title(ctx, value) == value
        return self._response_factory.title_changed(
            ctx.chat_id, ctx.user_id, value, are_set
        )

    @_require_daily_action
    def _handle_random_dice_roll(self, ctx: CallbackContext):
        if self._dice_service.roll_random(ctx):
            title = self._titles_service.handle_success_roll(ctx.chat_id, ctx.user_id)
            response = self._response_factory.title_changed(
                ctx.chat_id, ctx.user_id, title.value or "", True
            )
        else:
            failed_roll = self._titles_service.handle_failed_roll(
                ctx.chat_id, ctx.user_id
            )
            response = self._response_factory.title_not_changed(failed_roll)
        self._renderer.edit_later(response, 5, ctx)

    @_require_daily_action
    def _handle_dice_roll(self, ctx: CallbackContext, dice_value: int):
        success = self._dice_service.roll_match(dice_value, ctx)
        if success:
            title = self._titles_service.handle_success_roll(ctx.chat_id, ctx.user_id)
            response = self._response_factory.title_changed(
                ctx.chat_id, ctx.user_id, title.value or "", True
            )
        else:
            failed_roll = self._titles_service.handle_failed_roll(
                ctx.chat_id, ctx.user_id
            )
            response = self._response_factory.title_not_changed(failed_roll)
        self._renderer.edit_later(response, 5, ctx)

    @_require_daily_action
    def _handle_steal(self, ctx: CallbackContext, target_id: int, title_id: int):
        if not self._titles_service.is_valid_title(ctx.chat_id, target_id, title_id):
            response = self._response_factory.title_invalid()
            self._renderer.edit(response, ctx)
            return
        success = self._dice_service.roll_random(ctx)
        if not success:
            menu = self._titles_service.handle_failed_steal(
                ctx.chat_id, ctx.user_id, title_id
            )
            response = self._response_factory.title_no_stolen(menu)
        else:
            result = self._titles_service.handle_steal(
                ctx.chat_id, ctx.user_id, title_id
            )
            if result is None:
                actor_title, target_title = None, None
            else:
                actor_id = result.actor_title.user_id
                actor_title = result.actor_title.value
                target_id = result.target_title.user_id
                target_title = result.target_title.value
            target_title_are_set = target_title == self._user_service.set_title(
                replace(ctx, user_id=target_id), target_title
            )
            response = self._response_factory.title_stolen(
                SetResult(
                    chat_id=ctx.chat_id,
                    user_id=actor_id,
                    title=actor_title,
                    are_set=True,
                ),
                SetResult(
                    chat_id=ctx.chat_id,
                    user_id=target_id,
                    title=target_title,
                    are_set=target_title_are_set,
                ),
            )
        self._renderer.edit_later(response, 5, ctx)

    def _handle_back_to_rename_menu(self, ctx: CallbackContext):
        menu = self._titles_service.show_rename_menu(ctx.chat_id, ctx.user_id)
        response = self._response_factory.rename_menu(menu)
        self._renderer.edit(response, ctx)

    def _show_steal_menu(self, ctx: CallbackContext, page: int, page_size: int = 20):
        menu = self._titles_service.show_steal_menu(
            ctx.chat_id, ctx.user_id, page, page_size
        )
        if isinstance(menu, RenameMenu):
            response = self._response_factory.rename_menu(menu)
            self._renderer.edit(response, ctx)
            return
        users = {
            user_id: self._user_service.get_username(menu.chat_id, user_id)
            for user_id in {info.user_id for info in menu.titles}
        }
        menu = replace(
            menu,
            titles=[
                replace(info, username=users[info.user_id]) for info in menu.titles
            ],
        )
        response = self._response_factory.steal_menu(menu)
        self._renderer.edit(response, ctx)

    def _handle_show_titles_bag(
        self, ctx: CallbackContext, page: int, page_size: int = 20
    ):
        titles_bag_menu = self._titles_service.handle_show_titles_bag(
            ctx.chat_id, ctx.user_id, page, page_size
        )
        response = self._response_factory.inventory(titles_bag_menu)
        self._renderer.edit(response, ctx)

    def _exchange_title_menu(
        self, ctx: CallbackContext, page: int, page_size: int = 20
    ):
        titles_bag_menu = self._titles_service.handle_exchange_title(
            ctx.chat_id, ctx.user_id, page, page_size, has_return_button=True
        )
        response = self._response_factory.exchange_menu(titles_bag_menu)
        self._renderer.edit(response, ctx)

    def _handle_swap_title(self, ctx: CallbackContext, title_bag_id: int):
        db_title = self._titles_service.handle_swap_title(title_bag_id)
        tg_title = (
            self._user_service.set_title(ctx, db_title)
            if db_title is not None
            else None
        )
        response = self._response_factory.inventory_swap(
            ctx.chat_id, ctx.user_id, db_title, tg_title
        )
        self._renderer.edit(response, ctx)

    def _handle_show_recipients_menu(
        self, ctx: CallbackContext, page: int, page_size: int = 21
    ):
        def get_username(user_id: int) -> str | None:
            return self._user_service.get_username(ctx.chat_id, user_id, is_active=True)

        menu = self._titles_service.get_gift_recipients(
            ctx.chat_id, ctx.user_id, page, page_size, get_username
        )
        response = self._response_factory.gift_recipients_menu(menu)
        self._renderer.edit(response, ctx)

    def _handle_show_gift_title_menu(
        self, ctx: CallbackContext, target_id: int, page: int, page_size: int = 20
    ):
        menu = self._titles_service.get_gift_titles(
            ctx.chat_id, ctx.user_id, target_id, page, page_size
        )
        response = self._response_factory.gift_title_menu(menu)
        self._renderer.edit(response, ctx)

    def _give_title(self, ctx: CallbackContext, target_id: int, title_id: int):
        title = self._titles_service.give_title(target_id, title_id)
        if title is not None:
            response = self._response_factory.title_given(
                ctx.chat_id, ctx.user_id, target_id, title
            )
        else:
            response = self._response_factory.title_invalid()
        self._renderer.edit(response, ctx)

    def _handle_exchange_title(self, ctx: CallbackContext, title_id: int):
        result = self._titles_service.exchange_title(ctx.chat_id, ctx.user_id, title_id)
        exchange_title_menu = self._titles_service.handle_exchange_title(
            ctx.chat_id, ctx.user_id, 0, 20, has_return_button=False
        )
        global _exchanged
        exchanged_in_context = _exchanged[ctx.chat_id, int(ctx.message_id)]
        exchanged_in_context.extend(result.titles)
        result = replace(result, titles=exchanged_in_context)
        response = Response(
            text_units=self._response_factory.title_exchanged(result).text_units,
            menu=exchange_title_menu,
        )
        self._renderer.edit(response, ctx)


_exchanged: dict[tuple[int, int], list[str]] = defaultdict(list)

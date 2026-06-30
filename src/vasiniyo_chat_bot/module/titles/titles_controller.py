from __future__ import annotations

from dataclasses import replace
from functools import wraps

from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.titles.dice_service import DiceService
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import TitleChanged
from vasiniyo_chat_bot.module.titles.dto import TitlesCallbackContext
from vasiniyo_chat_bot.module.titles.titles_response_factory import (
    TitlesResponseFactory,
)
from vasiniyo_chat_bot.module.titles.titles_service import TitlesService
from vasiniyo_chat_bot.module.user_service import UserService


def _require_daily_action(func):
    @wraps(func)
    def wrapper(self: TitlesController, ctx: CallbackContext, *args, **kwargs):
        if self._titles_service.is_roll_remaining(ctx.chat_id, ctx.user_id):
            return func(self, ctx, *args, **kwargs)
        response = self._response_factory.already_rolled()
        self._renderer.edit(response, ctx)

    return wrapper


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

    def try_sync_titles(self, db_title: str, ctx: UserContext) -> bool:
        if not db_title:
            self._user_service.set_default_title(ctx)
            return True
        tg_title = self._user_service.get_title(ctx)
        if tg_title == db_title:
            return True
        if db_title == self._user_service.set_title(ctx, db_title):
            return True
        return False

    def handle_rename(self, ctx: UserContext):
        db_title = self._titles_service.get_user_title(ctx.chat_id, ctx.user_id)
        if not self.try_sync_titles(db_title, ctx):
            response = self._response_factory.please_set_title(db_title)
            self._renderer.send(response, ctx)
            return
        result = self._titles_service.rename(ctx.chat_id, ctx.user_id)
        if isinstance(result, TitleChanged):
            response = self._set_title(result, ctx)
            self._renderer.send(response, ctx)
            return
        response = self._response_factory.rename_menu(result)
        self._renderer.send(response, ctx)

    def dispatch_titles_callback(self, ctx: TitlesCallbackContext):
        payload = ctx.payload
        if ctx.user_id != payload.user_id:
            response = self._response_factory.no_access()
            self._renderer.alert(response, ctx)
            return
        db_title = self._titles_service.get_user_title(ctx.chat_id, ctx.user_id)
        if not self.try_sync_titles(db_title, ctx):
            response = self._response_factory.please_set_title(db_title)
            self._renderer.edit(response, ctx)
            return
        match payload.action:
            case Action.ROLL_RANDOM_D6:
                self._handle_random_dice_roll(ctx)
            case Action.ROLL_D6:
                self._handle_dice_roll(ctx, payload.dice_value)
            case Action.OPEN_RENAME_MENU:
                self._handle_back_to_rename_menu(ctx)
            case Action.OPEN_STEAL_MENU:
                self._show_steal_menu(ctx, payload.page)
            case Action.STEAL_TITLE:
                self._handle_steal(ctx, payload.target_id, payload.title_bag_id)
            case Action.OPEN_TITLES_BAG:
                self._handle_show_titles_bag(ctx, payload.page)
            case Action.SET_TITLE_BAG:
                self._handle_swap_title(ctx, payload.title_bag_id)
            case Action.GIFT_RECIPIENTS_MENU:
                self._handle_show_recipients_menu(ctx, payload.page)
            case Action.GIFT_TITLE_MENU:
                self._handle_show_gift_title_menu(ctx, payload.target_id, payload.page)
            case Action.GIVE_TITLE:
                self._give_title(ctx, payload.target_id, payload.title_bag_id)
            case Action.OPEN_EXCHANGE_TITLE_MENU:
                self._exchange_title_menu(ctx, payload.page)
            case Action.EXCHANGE_TITLE:
                self._handle_exchange_title(ctx, payload.title_bag_id)

    def _set_title(self, title_changed: TitleChanged, ctx: UserContext) -> Response:
        are_set = title_changed.changed and (
            self._user_service.set_title(ctx, title_changed.title)
            == title_changed.title
        )
        return self._response_factory.title_changed(
            ctx.chat_id, ctx.user_id, title_changed, are_set
        )

    @_require_daily_action
    def _handle_random_dice_roll(self, ctx: UserContext):
        success = self._dice_service.roll_random(ctx)
        title_changed = self._titles_service.handle_roll(
            ctx.chat_id, ctx.user_id, success
        )
        response = self._set_title(title_changed, ctx)
        self._renderer.edit_later(response, 5, ctx)

    @_require_daily_action
    def _handle_dice_roll(self, ctx: UserContext, dice_value: int):
        success = self._dice_service.roll_match(dice_value, ctx)
        title_changed = self._titles_service.handle_roll(
            ctx.chat_id, ctx.user_id, success
        )
        response = self._set_title(title_changed, ctx)
        self._renderer.edit_later(response, 5, ctx)

    @_require_daily_action
    def _handle_steal(self, ctx: UserContext, target_id: int, title_id: int):
        if not self._titles_service.is_valid_title(ctx.chat_id, target_id, title_id):
            response = self._response_factory.title_invalid()
            self._renderer.edit(response, ctx)
            return
        success = self._dice_service.roll_random(ctx)
        result = self._titles_service.handle_steal(
            ctx.chat_id, ctx.user_id, title_id, success
        )
        if not result.changed:
            actor_title_are_set, target_title_are_set = None, None
        else:
            actor_title_are_set = result.actor_title == self._user_service.set_title(
                replace(ctx, user_id=result.actor_id), result.actor_title
            )
            target_title_are_set = result.target_title == self._user_service.set_title(
                replace(ctx, user_id=result.target_id), result.target_title
            )
        response = self._response_factory.title_stolen(
            ctx.chat_id,
            result,
            actor_title_are_set=actor_title_are_set,
            target_title_are_set=target_title_are_set,
        )
        self._renderer.edit_later(response, 5, ctx)

    def _handle_back_to_rename_menu(self, ctx: UserContext):
        menu = self._titles_service.show_rename_menu(ctx.chat_id, ctx.user_id)
        response = self._response_factory.rename_menu(menu)
        self._renderer.edit(response, ctx)

    def _show_steal_menu(self, ctx: UserContext, page: int, page_size: int = 20):
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

    def _handle_show_titles_bag(self, ctx: UserContext, page: int, page_size: int = 20):
        titles_bag_menu = self._titles_service.handle_show_titles_bag(
            ctx.chat_id, ctx.user_id, page, page_size
        )
        response = self._response_factory.inventory(titles_bag_menu)
        self._renderer.edit(response, ctx)

    def _exchange_title_menu(self, ctx: UserContext, page: int, page_size: int = 20):
        titles_bag_menu = self._titles_service.handle_exchange_title(
            ctx.chat_id, ctx.user_id, page, page_size
        )
        response = self._response_factory.exchange_menu(titles_bag_menu)
        self._renderer.edit(response, ctx)

    def _handle_swap_title(self, ctx: UserContext, title_bag_id: int):
        result = self._titles_service.handle_swap_title(
            ctx.chat_id, ctx.user_id, title_bag_id
        )
        tg_title = (
            self._user_service.set_title(ctx, result.title) if result.changed else None
        )
        response = self._response_factory.inventory_swap(
            ctx.chat_id, ctx.user_id, result, are_set=result.title == tg_title
        )
        self._renderer.edit(response, ctx)

    def _handle_show_recipients_menu(
        self, ctx: UserContext, page: int, page_size: int = 21
    ):
        menu = self._titles_service.get_gift_recipients(
            ctx.chat_id,
            ctx.user_id,
            page,
            page_size,
            lambda uid: self._user_service.get_username(
                ctx.chat_id, uid, is_active=True
            ),
        )
        response = self._response_factory.gift_recipients_menu(menu)
        self._renderer.edit(response, ctx)

    def _handle_show_gift_title_menu(
        self, ctx: UserContext, target_id: int, page: int, page_size: int = 20
    ):
        menu = self._titles_service.get_gift_titles(
            ctx.chat_id, ctx.user_id, target_id, page, page_size
        )
        response = self._response_factory.gift_title_menu(menu)
        self._renderer.edit(response, ctx)

    def _give_title(self, ctx: UserContext, target_id: int, title_id: int):
        result = self._titles_service.give_title(ctx.chat_id, target_id, title_id)
        if result.changed:
            response = self._response_factory.title_given(
                ctx.chat_id, ctx.user_id, target_id, result.title
            )
        else:
            response = self._response_factory.title_invalid()
        self._renderer.edit(response, ctx)

    def _handle_exchange_title(self, ctx: UserContext, title_id: int):
        result = self._titles_service.exchange_title(ctx.chat_id, ctx.user_id, title_id)
        response = self._response_factory.title_exchanged(result)
        self._renderer.edit(response, ctx)

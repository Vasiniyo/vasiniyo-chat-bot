from typing import Callable

from telebot.types import InlineKeyboardMarkup

from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import InlineCallbackContext
from vasiniyo_chat_bot.module.dto import Menu
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import UserContext
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.titles.dto import AnimeGenreMenu
from vasiniyo_chat_bot.module.titles.dto import CaptchaMenu
from vasiniyo_chat_bot.module.titles.dto import ExchangeTitleMenu
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientsMenu
from vasiniyo_chat_bot.module.titles.dto import GiftTitlesMenu
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import StealMenu
from vasiniyo_chat_bot.module.titles.dto import TitlesBagMenu
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.keyboard.anime_keyboard_factory import (
    AnimeKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.keyboard.captcha_keyboard_factory import (
    CaptchaKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.keyboard.titles_keyboard_factory import (
    TitlesKeyboardFactory,
)


class TelegramRenderer(Renderer):
    def __init__(
        self,
        bot_service: BotService,
        keyboard_factory: TitlesKeyboardFactory,
        keyboard_factory2: AnimeKeyboardFactory,
        keyboard_factory3: CaptchaKeyboardFactory,
    ):
        self._bot_service = bot_service
        self._keyboard_factory = keyboard_factory
        self._keyboard_factory2 = keyboard_factory2
        self._keyboard_factory3 = keyboard_factory3

    def send(self, response: Response, ctx: UserContext):
        if response.picture:
            message = self._bot_service.send_photo(
                response.picture,
                ctx,
                caption=response.text_units,
                reply_markup=self._to_markup(response.menu, ctx.user_id),
            )
            return message.id
        message = self._bot_service.send_message(
            response.text_units,
            ctx,
            reply_markup=self._to_markup(response.menu, ctx.user_id),
        )
        return message.id

    def send_sticker(self, response: Response, ctx: UserContext):
        self._bot_service.send_sticker(response.text_units, ctx)

    def send_photo(self, response: Response, ctx: UserContext):
        message = self._bot_service.send_photo(
            response.picture,
            ctx,
            caption=response.text_units,
            reply_markup=self._to_markup(response.menu, ctx.user_id),
        )
        return message.id

    def edit(self, response: Response, ctx: UserContext, is_disabled_preview=True):
        if response.picture:
            self._bot_service.edit_message_media(
                response.picture,
                ctx.chat_id,
                ctx.message_id,
                caption=response.text_units,
                reply_markup=self._to_markup(response.menu, ctx.user_id),
            )
            return
        self._bot_service.edit_message_text(
            response.text_units,
            ctx,
            reply_markup=self._to_markup(response.menu, ctx.user_id),
            is_disabled_preview=is_disabled_preview,
        )

    def edit_caption(
        self, response: Response, ctx: UserContext, is_disabled_preview=True
    ):
        self._bot_service.edit_message_caption(
            ctx.chat_id,
            ctx.message_id,
            response.text_units,
            reply_markup=self._to_markup(response.menu, ctx.user_id),
        )

    def edit_later(self, response: Response, delay: int, ctx: UserContext):
        self._bot_service.edit_message_text_async(
            response.text_units,
            ctx,
            delay=delay,
            reply_markup=self._to_markup(response.menu, ctx.user_id),
        )

    def alert(self, response: Response, ctx: CallbackContext):
        self._bot_service.answer_callback_query(
            response.text_units, int(ctx.callback_id)
        )

    def answer_inline_query(
        self,
        commands: list[tuple[str, Callable[[], Response]]],
        ctx: InlineCallbackContext,
    ):
        def bar(
            f: Callable[[], Response],
        ) -> Callable[[], tuple[str, InlineKeyboardMarkup | None]]:
            t = f()
            return lambda: (t.text_units, self._to_markup(t.menu, ctx.user_id))

        c = [(text, lambda func=func: bar(func)()) for text, func in commands]
        return self._bot_service.answer_inline_query(c, ctx.callback_id)

    def delete(self, ctx: UserContext):
        self._bot_service.delete_message(ctx)

    def _to_markup(
        self, menu: Menu | None, user_id: int
    ) -> InlineKeyboardMarkup | None:
        if menu is None:
            return None
        if isinstance(menu, RenameMenu):
            return self._keyboard_factory.rename_menu(menu, user_id)
        elif isinstance(menu, StealMenu):
            return self._keyboard_factory.steal_menu(menu, user_id)
        elif isinstance(menu, TitlesBagMenu):
            return self._keyboard_factory.titles_bag(menu, user_id)
        elif isinstance(menu, GiftRecipientsMenu):
            return self._keyboard_factory.gift_recipients_menu(menu, user_id)
        elif isinstance(menu, GiftTitlesMenu):
            return self._keyboard_factory.gift_titles_menu(menu, user_id)
        elif isinstance(menu, AnimeGenreMenu):
            return self._keyboard_factory2.genre_options_markup(user_id)
        elif isinstance(menu, CaptchaMenu):
            return self._keyboard_factory3.update_button(user_id)
        elif isinstance(menu, ExchangeTitleMenu):
            return self._keyboard_factory.exchange_menu(menu, user_id)
        else:
            return None

import logging
from typing import Callable
from typing import cast

from injector import inject
from telebot.types import InlineKeyboardMarkup

from vasiniyo_chat_bot.module.anime.dto import AnimeGenreMenu
from vasiniyo_chat_bot.module.captcha.dto import CaptchaMenu
from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import InlineCallbackContext
from vasiniyo_chat_bot.module.dto import InlineQueryContext
from vasiniyo_chat_bot.module.dto import Menu
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.titles.dto import ExchangeTitleMenu
from vasiniyo_chat_bot.module.titles.dto import FailedRollMenu
from vasiniyo_chat_bot.module.titles.dto import FailedStealMenu
from vasiniyo_chat_bot.module.titles.dto import GiftRecipientsMenu
from vasiniyo_chat_bot.module.titles.dto import GiftTitlesMenu
from vasiniyo_chat_bot.module.titles.dto import RenameMenu
from vasiniyo_chat_bot.module.titles.dto import StealMenu
from vasiniyo_chat_bot.module.titles.dto import TitlesBagMenu
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.keyboard.anime_keyboard import AnimeKeyboardFactory
from vasiniyo_chat_bot.telegram.keyboard.captcha_keyboard import CaptchaKeyboardFactory
from vasiniyo_chat_bot.telegram.keyboard.titles_keyboard import TitlesKeyboardFactory

_logger = logging.getLogger(__name__)


@inject
class TelegramRenderer(Renderer):
    def __init__(self, bot_service: BotService):
        self._bot_service = bot_service

    def send(
        self, response: Response, ctx: MessageContext | CallbackContext
    ) -> int | None:
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
        return message.id if message else None

    def send_sticker(self, response: Response, ctx: MessageContext) -> None:
        file_id = response.text_units
        if not isinstance(file_id, str):
            _logger.warning("invalid_file_id", extra={"file_id": file_id})
            return
        self._bot_service.send_sticker(file_id, ctx)

    def edit(
        self,
        response: Response,
        ctx: MessageContext | CallbackContext | InlineCallbackContext,
        is_disabled_preview=True,
    ) -> None:
        if isinstance(ctx, InlineCallbackContext):
            self._bot_service.edit_via_message_text(
                response.text_units,
                ctx,
                reply_markup=self._to_markup(response.menu, ctx.user_id),
                is_disabled_preview=is_disabled_preview,
            )
            return
        if response.picture:
            caption = response.text_units
            if not isinstance(caption, str):
                _logger.warning("invalid_caption_text", extra={"caption": caption})
                return
            self._bot_service.edit_message_media(
                response.picture,
                ctx,
                caption=caption,
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
        self, response: Response, ctx: MessageContext, is_disabled_preview=True
    ) -> None:
        caption = response.text_units
        if not isinstance(caption, str):
            _logger.warning("invalid_caption_text", extra={"caption": caption})
            return
        self._bot_service.edit_message_caption(
            ctx.chat_id,
            ctx.message_id,
            caption=caption,
            reply_markup=self._to_markup(response.menu, ctx.user_id),
        )

    def edit_later(
        self, response: Response, delay: int, ctx: MessageContext | CallbackContext
    ) -> None:
        self._bot_service.edit_message_text_async(
            response.text_units,
            ctx,
            delay=delay,
            reply_markup=self._to_markup(response.menu, ctx.user_id),
        )

    def alert(
        self, response: Response, ctx: CallbackContext | InlineCallbackContext
    ) -> None:
        text = response.text_units
        if not isinstance(text, str):
            _logger.warning("invalid_alert_text", extra={"text": text})
            return
        self._bot_service.answer_callback_query(text, ctx.callback_id)

    def answer_inline_query(
        self,
        commands: list[tuple[str, Callable[[], Response]]],
        ctx: InlineQueryContext,
    ) -> None:
        def bar(
            f: Callable[[], Response],
        ) -> Callable[[], tuple[str, InlineKeyboardMarkup | None]]:
            t = f()
            text = t.text_units
            if not isinstance(text, str):
                _logger.warning("invalid_inline_text", extra={"text": text})
                return lambda: ("", None)
            return lambda: (cast(str, text), self._to_markup(t.menu, ctx.user_id))

        c = [(text, lambda func=func: bar(func)()) for text, func in commands]
        self._bot_service.answer_inline_query(c, ctx.callback_id)

    def delete(self, ctx: MessageContext):
        self._bot_service.delete_message(ctx)

    @staticmethod
    def _to_markup(menu: Menu | None, user_id: int) -> InlineKeyboardMarkup | None:
        if menu is None:
            return None
        if isinstance(menu, RenameMenu):
            return TitlesKeyboardFactory.rename_menu(menu, user_id)
        if isinstance(menu, StealMenu):
            return TitlesKeyboardFactory.steal_menu(menu, user_id)
        if isinstance(menu, FailedRollMenu):
            return TitlesKeyboardFactory.failed_roll(menu, user_id)
        if isinstance(menu, FailedStealMenu):
            return TitlesKeyboardFactory.failed_steal(menu, user_id)
        if isinstance(menu, TitlesBagMenu):
            return TitlesKeyboardFactory.inventory_menu(menu, user_id)
        if isinstance(menu, GiftRecipientsMenu):
            return TitlesKeyboardFactory.recipients_menu(menu, user_id)
        if isinstance(menu, GiftTitlesMenu):
            return TitlesKeyboardFactory.gift_menu(menu, user_id)
        if isinstance(menu, AnimeGenreMenu):
            return AnimeKeyboardFactory.anime_menu(user_id)
        if isinstance(menu, CaptchaMenu):
            return CaptchaKeyboardFactory.captcha_menu(user_id)
        if isinstance(menu, ExchangeTitleMenu):
            return TitlesKeyboardFactory.exchange_menu(menu, user_id)
        return None

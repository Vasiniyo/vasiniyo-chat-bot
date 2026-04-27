from typing import Callable, Protocol

from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.dto import (
    CallbackContext,
    InlineCallbackContext,
    Response,
    UserContext,
)


class Renderer(Protocol):
    def send(self, response: Response, ctx: UserContext) -> int | None: ...
    def send_sticker(self, response: Response, ctx: UserContext) -> None: ...
    def send_photo(self, response: Response, ctx: UserContext) -> int | None: ...
    def edit(
        self, response: Response, ctx: UserContext, is_disabled_preview=True
    ) -> None: ...
    def edit_caption(self, response: Response, ctx: UserContext) -> None: ...
    def edit_later(self, response: Response, delay: int, ctx: UserContext) -> None: ...
    def alert(self, response: Response, ctx: CallbackContext) -> None: ...
    def answer_inline_query(
        self, commands: list[tuple[str, Callable[[], str]]], ctx: InlineCallbackContext
    ) -> None: ...
    def delete(self, ctx: UserContext) -> None: ...


class TelegramRenderer(Renderer):
    def __init__(self, bot_service: BotService):
        self._bot_service = bot_service

    def send(self, response: Response, ctx: UserContext):
        if response.picture:
            message = self._bot_service.send_photo(
                response.picture,
                ctx,
                caption=response.text_units,
                reply_markup=response.markup,
            )
            return message.id
        message = self._bot_service.send_message(
            response.text_units, ctx, reply_markup=response.markup
        )
        return message.id

    def send_sticker(self, response: Response, ctx: UserContext):
        self._bot_service.send_sticker(response.text_units, ctx)

    def send_photo(self, response: Response, ctx: UserContext):
        message = self._bot_service.send_photo(
            response.picture,
            ctx,
            caption=response.text_units,
            reply_markup=response.markup,
        )
        return message.id

    def edit(self, response: Response, ctx: UserContext, is_disabled_preview=True):
        if response.picture:
            self._bot_service.edit_message_media(
                response.picture,
                ctx.chat_id,
                ctx.message_id,
                caption=response.text_units,
                reply_markup=response.markup,
            )
            return
        self._bot_service.edit_message_text(
            response.text_units,
            ctx,
            reply_markup=response.markup,
            is_disabled_preview=is_disabled_preview,
        )

    def edit_caption(
        self, response: Response, ctx: UserContext, is_disabled_preview=True
    ):
        self._bot_service.edit_message_caption(
            ctx.chat_id,
            ctx.message_id,
            response.text_units,
            reply_markup=response.markup,
        )

    def edit_later(self, response: Response, delay: int, ctx: UserContext):
        self._bot_service.edit_message_text_async(
            response.text_units, ctx, delay=delay, reply_markup=response.markup
        )

    def alert(self, response: Response, ctx: CallbackContext):
        self._bot_service.answer_callback_query(
            response.text_units, int(ctx.callback_id)
        )

    def answer_inline_query(
        self, commands: list[tuple[str, Callable[[], str]]], ctx: InlineCallbackContext
    ):
        self._bot_service.answer_inline_query(commands, ctx.callback_id)

    def delete(self, ctx: UserContext):
        self._bot_service.delete_message(ctx)

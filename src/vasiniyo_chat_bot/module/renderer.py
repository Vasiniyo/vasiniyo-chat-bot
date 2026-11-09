from __future__ import annotations

from typing import Callable
from typing import Protocol

from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.dto import InlineCallbackContext
from vasiniyo_chat_bot.module.dto import InlineQueryContext
from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.dto import Response
from vasiniyo_chat_bot.module.dto import UserContext


class Renderer(Protocol):
    def send(
        self, response: Response, ctx: MessageContext | CallbackContext
    ) -> int | None: ...
    def send_sticker(self, response: Response, ctx: MessageContext) -> None: ...
    def send_photo(self, response: Response, ctx: UserContext) -> int | None: ...
    def edit(
        self,
        response: Response,
        ctx: MessageContext | CallbackContext | InlineCallbackContext,
        is_disabled_preview=True,
    ) -> None: ...
    def edit_caption(self, response: Response, ctx: MessageContext) -> None: ...
    def edit_later(
        self, response: Response, delay: int, ctx: MessageContext | CallbackContext
    ) -> None: ...
    def alert(
        self, response: Response, ctx: CallbackContext | InlineCallbackContext
    ) -> None: ...
    def answer_inline_query(
        self,
        commands: list[tuple[str, Callable[[], Response]]],
        ctx: InlineQueryContext,
    ) -> None: ...
    def delete(self, ctx: MessageContext) -> None: ...

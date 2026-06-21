from dataclasses import replace

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.renderer import Renderer
from vasiniyo_chat_bot.module.reply.dto import StickerResult
from vasiniyo_chat_bot.module.reply.dto import TextResult
from vasiniyo_chat_bot.module.reply.reply_response_factory import ReplyResponseFactory
from vasiniyo_chat_bot.module.reply.reply_service import ReplyService


class ReplyController:
    def __init__(
        self,
        reply_service: ReplyService,
        response_factory: ReplyResponseFactory,
        renderer: Renderer,
    ):
        self._reply_service = reply_service
        self._response_factory = response_factory
        self._renderer = renderer

    def handle_text_reply(self, ctx: MessageContext):
        result = self._reply_service.handle_text_replies(ctx.text)
        if result:
            self._send_reply(result, ctx)

    def handle_sticker_reply(self, ctx: MessageContext):
        result = self._reply_service.handle_sticker_replies(ctx.file_id)
        if result:
            self._send_reply(result, ctx)

    def _send_reply(self, result: TextResult | StickerResult, ctx: MessageContext):
        message_id = (
            ctx.prev.message_id if result.to_reply and ctx.prev else ctx.message_id
        )
        ctx = replace(ctx, message_id=message_id)
        if isinstance(result, TextResult):
            response = self._response_factory.text(result)
            self._renderer.send(response, ctx)
        elif isinstance(result, StickerResult):
            response = self._response_factory.sticker(result)
            self._renderer.send_sticker(response, ctx)

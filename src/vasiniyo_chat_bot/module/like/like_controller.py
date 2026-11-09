from injector import inject

from vasiniyo_chat_bot.module.dto import MessageContext
from vasiniyo_chat_bot.module.like.like_response_factory import LikeResponseFactory
from vasiniyo_chat_bot.module.like.like_service import LikeService
from vasiniyo_chat_bot.module.renderer import Renderer


@inject
class LikeController:
    def __init__(
        self,
        like_service: LikeService,
        response_factory: LikeResponseFactory,
        renderer: Renderer,
    ) -> None:
        self._like_service = like_service
        self._response_factory = response_factory
        self._renderer = renderer

    def set_like(self, ctx: MessageContext):
        to_user_id = ctx.prev.user_id if ctx.prev else None
        if not to_user_id:
            response = self._response_factory.like_reply_required()
        else:
            like = self._like_service.handle_like(ctx.chat_id, ctx.user_id, to_user_id)
            response = self._response_factory.like(like, ctx.chat_id, to_user_id)
        self._renderer.send(response, ctx)

    def top_likes(self, ctx: MessageContext):
        leaderboard = self._like_service.handle_top_likes(ctx.chat_id)
        response = self._response_factory.leaderboard(leaderboard)
        self._renderer.send(response, ctx)

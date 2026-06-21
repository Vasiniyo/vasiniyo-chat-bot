from dataclasses import dataclass

from vasiniyo_chat_bot.module.anime.anime_payload_factory import AnimePayload
from vasiniyo_chat_bot.module.anime.anime_response_factory import AnimeResponseFactory
from vasiniyo_chat_bot.module.anime.anime_service import AnimeService
from vasiniyo_chat_bot.module.dto import CallbackContext
from vasiniyo_chat_bot.module.renderer import Renderer


@dataclass(frozen=True)
class AnimeCallbackContext(CallbackContext):
    payload: AnimePayload


class AnimeController:
    def __init__(
        self,
        anime_service: AnimeService,
        response_factory: AnimeResponseFactory,
        renderer: Renderer,
    ) -> None:
        self._anime_service = anime_service
        self._response_factory = response_factory
        self._renderer = renderer

    def handle_anime_command(self):
        return self._response_factory.genre_options()

    def dispatch_anime_callback(self, ctx: AnimeCallbackContext):
        payload = ctx.payload
        if ctx.user_id != payload.user_id:
            response = self._response_factory.no_access()
            self._renderer.alert(response, ctx)
            return
        anime = self._anime_service.handle_anime(score=8, anime_genre=payload.genre)
        response = self._response_factory.link(anime)
        self._renderer.edit(response, ctx, is_disabled_preview=False)

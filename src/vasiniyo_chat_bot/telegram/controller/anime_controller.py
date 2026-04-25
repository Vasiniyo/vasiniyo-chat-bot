from vasiniyo_chat_bot.module.anime.anime_service import AnimeService
from vasiniyo_chat_bot.module.anime.dto import AnimeGenre
from vasiniyo_chat_bot.safely_bot_utils import extract_field, parse_json
from vasiniyo_chat_bot.telegram.dto import CallbackContext, Field, UserContext
from vasiniyo_chat_bot.telegram.renderer.anime_response_factory import (
    AnimeResponseFactory,
)
from vasiniyo_chat_bot.telegram.renderer.renderer import Renderer


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

    def handle_anime_command(self, ctx: UserContext):
        response = self._response_factory.genre_options(ctx.user_id)
        self._renderer.send(response, ctx)

    def dispatch_anime_callback(self, ctx: CallbackContext):
        payload = parse_json(ctx.data)
        payload_user_id = extract_field(payload, Field.USER_ID)
        anime_genre = extract_field(payload, Field.ANIME_GENRE)
        if ctx.user_id != payload_user_id:
            response = self._response_factory.no_access()
            self._renderer.alert(response, ctx)
            return
        genre = AnimeGenre(anime_genre)
        anime = self._anime_service.handle_anime(score=8, anime_genre=genre)
        response = self._response_factory.link(anime)
        self._renderer.edit(response, ctx, is_disabled_preview=False)

from dataclasses import dataclass
import logging
from typing import Callable

from telebot.types import CallbackQuery, Message

from vasiniyo_chat_bot.anilist.anilist_anime_provider import AnilistAnimeProvider
from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.database.sqlite.dao import (
    EventsDao,
    LikesDao,
    TitlesBagDAO,
    TitlesDAO,
)
from vasiniyo_chat_bot.database.sqlite.repository.dto import SqliteDatabaseSettings
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_events_repository import (
    SqliteEventsRepository,
)
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_likes_repository import (
    SqliteLikesRepository,
)
from vasiniyo_chat_bot.database.sqlite.repository.sqlite_titles_repository import (
    SqliteTitlesRepository,
)
from vasiniyo_chat_bot.module.anime.anime_service import AnimeService
from vasiniyo_chat_bot.module.captcha.captcha_repository import CaptchaRepository
from vasiniyo_chat_bot.module.captcha.captcha_service import CaptchaService
from vasiniyo_chat_bot.module.drink_or_not.drink_service import DrinkService
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.module.likes.like_service import LikeService
from vasiniyo_chat_bot.module.play.event_player_repository import EventPlayersRepository
from vasiniyo_chat_bot.module.play.image_service import ImageService
from vasiniyo_chat_bot.module.play.play_service import PlayService
from vasiniyo_chat_bot.module.reply.reply_service import ReplyService
from vasiniyo_chat_bot.module.titles.titles_provider import TitlesProvider
from vasiniyo_chat_bot.module.titles.titles_service import TitlesService
from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper
from vasiniyo_chat_bot.shikimori.shikimori_anime_provider import ShikimoriAnimeProvider
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.controller import (
    AnimeController,
    CaptchaController,
    DrinkController,
    HelpController,
    LikeController,
    PlayController,
    ReplyController,
    TitlesController,
)
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.renderer import (
    AnimeRenderer,
    CaptchaRenderer,
    DrinkRenderer,
    HelpRenderer,
    LikeRenderer,
    PlayRenderer,
    ReplyRenderer,
    TitlesRenderer,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Command:
    name: str
    handler: Callable[[Message], None]


class MessageHandler:
    handler: Callable[[Message], None]
    kwargs: dict[str, any]

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[Message], None],
        validator: Filter[Message] = None,
        content_types: list[str] = None,
    ) -> None:
        in_allowed_chat = Filter(
            lambda m: "*" in allowed_chats or str(m.chat.id) in allowed_chats
        )
        self.handler = safe_wrapper()(handler)
        self.kwargs = {
            "func": in_allowed_chat & (validator or Filter(lambda _: True)),
            "content_types": list(content_types or []) or None,
        }


class CommandHandler(MessageHandler):
    def __init__(
        self, bot_username, allowed_chats: list[str], command: Command
    ) -> None:
        self.bot_username = bot_username
        self._command = command
        super().__init__(
            allowed_chats, self._get_handler(command), Filter(self._command_for_bot)
        )

    def _get_handler(self, command: Command):
        def inner(message: Message):
            logger.info(
                "handle_command",
                extra={
                    "command": self._command.name,
                    "chat_id": message.chat.id,
                    "user_id": message.from_user.id,
                },
            )
            command.handler(message)

        return inner

    def _command_for_bot(self, message: Message) -> bool:
        if not message.text:
            return False
        c = message.text.lstrip().split()
        if not c:
            return False
        x = c[0].split("@")
        if len(x) == 1:
            return x[0] == self._command.name
        return x[0] == self._command.name and x[1] == self.bot_username


class StickerHandler(MessageHandler):
    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[Message], None],
        validator: Filter[Message] = None,
    ) -> None:
        super().__init__(allowed_chats, handler, validator, ["sticker"])


class NewMemberHandler(MessageHandler):
    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[Message], None],
        validator: Filter[Message] = None,
    ) -> None:
        super().__init__(allowed_chats, handler, validator, ["new_chat_members"])


class QueryHandler:
    handler: Callable[[CallbackQuery], None]
    kwargs: dict

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[CallbackQuery], None],
        validator: Filter[CallbackQuery],
    ) -> None:
        in_allowed_chat = Filter(
            lambda call: "*" in allowed_chats
            or str(call.message.chat.id) in allowed_chats
        )
        self.handler = safe_wrapper(handler)(handler)
        self.kwargs = {"func": in_allowed_chat & validator}


class Controller:
    my_commands: dict[str, str] = dict()
    callbacks: list[QueryHandler] = list()
    messages: list[MessageHandler] = list()

    def __init__(
        self, bot_service: BotService, allowed_chats: list[str], enabled_test_mode
    ):
        self._bot_service = bot_service
        self._allowed_chats = allowed_chats
        self._enabled_test_mode = enabled_test_mode

    def apply_controllers(
        self,
        help_controller: HelpController | None = None,
        like_controller: LikeController | None = None,
        drink_controller: DrinkController | None = None,
        anime_controller: AnimeController | None = None,
        titles_controller: TitlesController | None = None,
        play_controller: PlayController | None = None,
        reply_controller: ReplyController | None = None,
        captcha_controller: CaptchaController | None = None,
    ):
        commands: dict[CommandKey, Command] = dict()
        if like_controller:
            commands[CommandKey.LIKE] = Command("/like", like_controller.set_like)
            commands[CommandKey.TOP_LIKES] = Command(
                "/top_likes", like_controller.top_likes
            )
        if drink_controller:
            commands[CommandKey.DRINK_OR_NOT] = Command(
                "/drink_or_not", drink_controller.advice_drink
            )
        if anime_controller:
            commands[CommandKey.ANIME] = Command(
                "/anime", anime_controller.handle_anime_command
            )
        if titles_controller:
            commands[CommandKey.RENAME] = Command(
                "/rename", titles_controller.handle_rename
            )
            self.callbacks.append(
                QueryHandler(
                    self._allowed_chats,
                    titles_controller.dispatch_titles_callback,
                    Filter(titles_controller.has_titles_payload),
                )
            )
        if play_controller:
            commands[CommandKey.PLAY] = Command("/play", play_controller.handle_play)
            commands[CommandKey.PLAYERS] = Command(
                "/players", play_controller.handle_players
            )
            commands[CommandKey.WINNER] = Command(
                "/winner", play_controller.handle_winner
            )
            commands[CommandKey.TOP_WINNERS] = Command(
                "/top_winners", play_controller.handle_top_winners
            )
            if self._enabled_test_mode:
                commands[CommandKey.TEST_NEW_CATEGORY] = Command(
                    "/test_new_category", play_controller.handle_test_new_category
                )
                commands[CommandKey.TEST_NEW_WINNER] = Command(
                    "/test_new_winner", play_controller.handle_test_new_winner
                )

        if reply_controller:
            self.messages.append(
                StickerHandler(
                    self._allowed_chats, reply_controller.handle_sticker_reply
                )
            )
            self.messages.append(
                MessageHandler(self._allowed_chats, reply_controller.handle_text_reply)
            )
        if help_controller:

            def unknown_command_for_bot(message: Message) -> bool:
                text = message.text
                if not text:
                    return False
                command, _, username = text.lstrip().split(maxsplit=1)[0].partition("@")
                names = {d.name for d in commands.values()}
                return (
                    username == self._bot_service.get_me().username
                    and command not in names
                )

            help_commands = {}
            commands[CommandKey.HELP] = Command(
                "/help",
                lambda message: help_controller.show_help(message, help_commands),
            )
            help_commands.update(
                {command_key: values.name for command_key, values in commands.items()}
            )
            self.messages[:0] = [
                MessageHandler(
                    self._allowed_chats,
                    help_controller.handle_unknown_command,
                    Filter(unknown_command_for_bot),
                )
            ]
        self.messages[:0] = [
            CommandHandler(
                self._bot_service.get_me().username, self._allowed_chats, command
            )
            for command in commands.values()
        ]
        if captcha_controller:
            self.messages[:0] = [
                MessageHandler(
                    self._allowed_chats,
                    captcha_controller.handle_verify_captcha,
                    Filter(captcha_controller.are_captcha_user),
                ),
                NewMemberHandler(
                    self._allowed_chats, captcha_controller.handle_new_user
                ),
            ]
            self.callbacks[:0] = [
                QueryHandler(
                    self._allowed_chats,
                    captcha_controller.handle_captcha_button_press,
                    captcha_controller.is_captcha_user
                    and Filter(captcha_controller.has_captcha_payload),
                )
            ]
        self.my_commands = {
            command.name: help_controller.help_renderer.helps[command_key]
            for command_key, command in commands.items()
        }


def init_controller(config: Config):
    bot_service = BotService(config.bot_settings.bot)
    database_settings = config.database
    if not isinstance(database_settings, SqliteDatabaseSettings):
        raise NotImplementedError(
            f"Database type {type(database_settings).__name__} is not supported yet"
        )
    controller = Controller(
        bot_service,
        config.bot_settings.allowed_chats,
        "test" in config.bot_settings.mods,
    )
    controller.apply_controllers(
        help_controller=HelpController(HelpRenderer(bot_service)),
        like_controller=(
            LikeController(
                LikeService(SqliteLikesRepository(LikesDao(), database_settings)),
                LikeRenderer(bot_service),
            )
            if "like" in config.bot_settings.mods
            else None
        ),
        drink_controller=(
            DrinkController(DrinkService(config.drinks), DrinkRenderer(bot_service))
            if "drink" in config.bot_settings.mods
            else None
        ),
        anime_controller=(
            AnimeController(
                AnimeService([AnilistAnimeProvider(), ShikimoriAnimeProvider()]),
                AnimeRenderer(bot_service),
            )
            if "anime" in config.bot_settings.mods
            else None
        ),
        titles_controller=(
            TitlesController(
                TitlesService(
                    TitlesProvider(config.custom_titles),
                    SqliteTitlesRepository(
                        TitlesDAO(), TitlesBagDAO(), database_settings
                    ),
                ),
                bot_service,
                TitlesRenderer(bot_service),
            )
            if "titles" in config.bot_settings.mods
            else None
        ),
        play_controller=(
            PlayController(
                PlayService(
                    EventPlayersRepository(bot_service),
                    SqliteEventsRepository(EventsDao(), database_settings),
                    config.event.play_categories,
                ),
                PlayRenderer(
                    bot_service,
                    ImageService(
                        config.event.default_winner_avatar, config.event.winner_pictures
                    ),
                ),
            )
            if "play" in config.bot_settings.mods
            else None
        ),
        reply_controller=(
            ReplyController(
                ReplyService(
                    long_messages=config.long_message, triggers=config.trigger_replies
                ),
                ReplyRenderer(bot_service),
            )
            if "reply" in config.bot_settings.mods
            else None
        ),
        captcha_controller=(
            CaptchaController(
                CaptchaService(config.captcha_properties, CaptchaRepository()),
                bot_service,
                CaptchaRenderer(bot_service, config.captcha_properties),
            )
            if "captcha" in config.bot_settings.mods
            else None
        ),
    )
    return controller

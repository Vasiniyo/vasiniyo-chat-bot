from dataclasses import dataclass
import logging
from typing import Callable

from telebot.types import CallbackQuery, InlineQuery, Message

from vasiniyo_chat_bot.anilist.anilist_anime_provider import AnilistAnimeProvider
from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.database.sqlite.dao import (
    EventsDao,
    LikesDao,
    TitlesBagDAO,
    TitlesStatesDAO,
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
from vasiniyo_chat_bot.module.daily_size.daily_size_service import DailySizeService
from vasiniyo_chat_bot.module.drink_or_not.drink_service import DrinkService
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.module.likes.like_service import LikeService
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
from vasiniyo_chat_bot.telegram.controller.daily_size_controller import (
    DailySizeController,
)
from vasiniyo_chat_bot.telegram.dto import (
    CallbackContext,
    InlineCallbackContext,
    MessageContext,
    UserContext,
)
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.keyboard.anime_keyboard_factory import (
    AnimeKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.keyboard.captcha_keyboard_factory import (
    CaptchaKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.keyboard.titles_keyboard_factory import (
    TitlesKeyboardFactory,
)
from vasiniyo_chat_bot.telegram.payload.anime_payload_factory import AnimePayloadFactory
from vasiniyo_chat_bot.telegram.payload.captcha_payload_factory import (
    CaptchaPayloadFactory,
)
from vasiniyo_chat_bot.telegram.payload.titles_payload_factory import (
    TitlesPayloadFactory,
)
from vasiniyo_chat_bot.telegram.renderer import (
    AnimeResponseFactory,
    CaptchaResponseFactory,
    HelpResponseFactory,
    LikeResponseFactory,
    PlayResponseFactory,
    ReplyResponseFactory,
)
from vasiniyo_chat_bot.telegram.renderer.daily_size_response_factory import (
    DailySizeResponseFactory,
)
from vasiniyo_chat_bot.telegram.renderer.drink_response_factory import (
    DrinkResponseFactory,
)
from vasiniyo_chat_bot.telegram.renderer.renderer import TelegramRenderer
from vasiniyo_chat_bot.telegram.renderer.titles_response_factory import (
    TitlesResponseFactory,
)
from vasiniyo_chat_bot.telegram.service.markdown_v2_service import MarkdownV2Service
from vasiniyo_chat_bot.telegram.service.telegram_event_players_service import (
    TelegramEventPlayersService,
)
from vasiniyo_chat_bot.telegram.service.telegram_roll_service import TelegramRollService
from vasiniyo_chat_bot.telegram.service.telegram_user_service import TelegramUserService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Command:
    name: str
    handler: Callable[[MessageContext], None]


class MessageHandler:
    handler: Callable[[Message], None]
    kwargs: dict[str, any]

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[MessageContext], None],
        validator: Filter[Message] = None,
        content_types: list[str] = None,
    ) -> None:
        in_allowed_chat = Filter(
            lambda m: "*" in allowed_chats or str(m.chat.id) in allowed_chats
        )
        self.handler = safe_wrapper(default=None)(self._to_handler(handler))
        self.kwargs = {
            "func": in_allowed_chat & (validator or Filter(lambda _: True)),
            "content_types": list(content_types or []) or None,
        }

    @staticmethod
    def _to_handler(
        handler: Callable[[MessageContext], None],
    ) -> Callable[[Message], None]:
        def inner(message: Message):
            users = message.new_chat_members or [message.from_user]
            for user in users:
                if user.is_bot:
                    logger.info(
                        "new_chat_members",
                        extra={"user_id": user.id, "details": "user is bot, skipping"},
                    )
                    continue
                handler(
                    MessageContext(
                        user_id=user.id,
                        chat_id=message.chat.id,
                        message_id=message.id,
                        prev=(
                            _message_to_user_context(message.reply_to_message)
                            if message.reply_to_message
                            else None
                        ),
                        file_id=message.sticker.file_id if message.sticker else None,
                        text=message.text,
                    )
                )

        return inner


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
        def inner(ctx: MessageContext):
            logger.info(
                "handle_command",
                extra={
                    "command": self._command.name,
                    "chat_id": ctx.chat_id,
                    "user_id": ctx.user_id,
                },
            )
            command.handler(ctx)

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
        handler: Callable[[MessageContext], None],
        validator: Filter[Message] = None,
    ) -> None:
        super().__init__(allowed_chats, handler, validator, ["sticker"])


class NewMemberHandler(MessageHandler):
    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[UserContext], None],
        validator: Filter[Message] = None,
    ) -> None:
        super().__init__(allowed_chats, handler, validator, ["new_chat_members"])


class LeftChatMemberHandler(MessageHandler):
    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[UserContext], None],
        validator: Filter[Message] = None,
    ) -> None:
        super().__init__(allowed_chats, handler, validator, ["left_chat_member"])


class QueryHandler:
    handler: Callable[[CallbackQuery], None]
    kwargs: dict

    def __init__(
        self,
        allowed_chats: list[str],
        handler: Callable[[CallbackContext], None],
        validator: Filter[CallbackQuery],
    ) -> None:
        in_allowed_chat = Filter(
            lambda call: "*" in allowed_chats
            or str(call.message.chat.id) in allowed_chats
        )
        self.handler = safe_wrapper(default=None)(self._to_handler(handler))
        self.kwargs = {"func": in_allowed_chat & validator}

    @staticmethod
    def _to_handler(
        handler: Callable[[CallbackContext], None],
    ) -> Callable[[CallbackQuery], None]:
        return lambda call: handler(
            CallbackContext(
                user_id=call.from_user.id,
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                data=call.data,
                callback_id=call.id,
            )
        )


class InlineQueryHandler:
    handler: Callable[[InlineQuery], None]
    kwargs: dict

    def __init__(self, handler: Callable[[InlineCallbackContext], None]) -> None:
        self.handler = safe_wrapper(default=None)(self._to_handler(handler))
        self.kwargs = {"func": lambda q: q.query == ""}

    @staticmethod
    def _to_handler(
        handler: Callable[[InlineCallbackContext], None],
    ) -> Callable[[InlineQuery], None]:
        return lambda call: handler(
            InlineCallbackContext(
                user_id=call.from_user.id, query=call.query, callback_id=call.id
            )
        )


def _call_to_user_context(call: CallbackQuery) -> UserContext:
    return UserContext(
        user_id=call.from_user.id,
        chat_id=call.message.chat.id,
        message_id=call.message.id,
    )


def _message_to_user_context(message: Message) -> UserContext:
    return UserContext(
        user_id=message.from_user.id, chat_id=message.chat.id, message_id=message.id
    )


class Controller:
    my_commands: dict[str, str] = dict()
    callbacks: list[QueryHandler] = list()
    messages: list[MessageHandler] = list()
    inline: InlineQueryHandler = None

    def __init__(
        self,
        bot_service: BotService,
        user_service: TelegramUserService,
        allowed_chats: list[str],
        enabled_test_mode,
    ):
        self._bot_service = bot_service
        self._user_service = user_service
        self._allowed_chats = allowed_chats
        self._enabled_test_mode = enabled_test_mode

    def apply_controllers(
        self,
        help_controller: HelpController | None = None,
        like_controller: LikeController | None = None,
        drink_controller: DrinkController | None = None,
        daily_size_controller: DailySizeController | None = None,
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
        if daily_size_controller:
            self.inline = InlineQueryHandler(daily_size_controller.get_daily_size)
        if anime_controller:
            commands[CommandKey.ANIME] = Command(
                "/anime", anime_controller.handle_anime_command
            )
            self.callbacks.append(
                QueryHandler(
                    self._allowed_chats,
                    anime_controller.dispatch_anime_callback,
                    Filter(
                        lambda call: AnimePayloadFactory.has_anime_payload(call.data)
                    ),
                )
            )
        if titles_controller:
            commands[CommandKey.RENAME] = Command(
                "/rename", titles_controller.handle_rename
            )
            self.callbacks.append(
                QueryHandler(
                    self._allowed_chats,
                    titles_controller.dispatch_titles_callback,
                    Filter(
                        lambda call: TitlesPayloadFactory.has_titles_payload(call.data)
                    ),
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
                    Filter(
                        lambda message: captcha_controller.is_captcha_user(
                            _message_to_user_context(message)
                        )
                    ),
                    content_types=[
                        # fmt: off
                        "animation", "audio", "contact", "dice",
                        "document", "location", "photo", "text",
                        "sticker", "video", "video_note", "voice"
                        # fmt: on
                    ],
                )
            ]
            self.callbacks[:0] = [
                QueryHandler(
                    self._allowed_chats,
                    captcha_controller.handle_captcha_button_press,
                    Filter(
                        lambda call: captcha_controller.is_captcha_user(
                            _call_to_user_context(call)
                        )
                    )
                    and Filter(
                        lambda call: CaptchaPayloadFactory.has_captcha_payload(
                            call.data
                        )
                    ),
                )
            ]

        def invalidate_user_cache(func: Callable[[UserContext], None] = lambda _: None):
            def handler(ctx: UserContext):
                self._user_service.invalidate_cache(ctx.chat_id, ctx.user_id)
                func(ctx)

            return handler

        self.messages[:0] = [
            NewMemberHandler(
                self._allowed_chats,
                invalidate_user_cache(
                    captcha_controller.handle_new_user
                    if captcha_controller
                    else lambda _: None
                ),
            ),
            LeftChatMemberHandler(self._allowed_chats, invalidate_user_cache()),
        ]
        self.my_commands = {
            command.name: help_controller._response_factory.helps[command_key]
            for command_key, command in commands.items()
        }


def init_controller(config: Config):
    bot_service = BotService(config.bot_settings.bot, MarkdownV2Service())
    user_service = TelegramUserService(bot_service)
    renderer = TelegramRenderer(bot_service)
    database_settings = config.database
    if not isinstance(database_settings, SqliteDatabaseSettings):
        raise NotImplementedError(
            f"Database type {type(database_settings).__name__} is not supported yet"
        )
    controller = Controller(
        bot_service,
        user_service,
        config.bot_settings.allowed_chats,
        "test" in config.bot_settings.mods,
    )
    controller.apply_controllers(
        help_controller=HelpController(HelpResponseFactory(), renderer),
        like_controller=(
            LikeController(
                LikeService(SqliteLikesRepository(LikesDao(), database_settings)),
                LikeResponseFactory(),
                renderer,
            )
            if "like" in config.bot_settings.mods
            else None
        ),
        drink_controller=(
            DrinkController(
                DrinkService(config.drinks), DrinkResponseFactory(), renderer
            )
            if "drink" in config.bot_settings.mods
            else None
        ),
        daily_size_controller=(
            DailySizeController(
                DailySizeService(config.daily_size_settings),
                DailySizeResponseFactory(),
                renderer,
            )
            if "daily_size" in config.bot_settings.mods
            else None
        ),
        anime_controller=(
            AnimeController(
                AnimeService([AnilistAnimeProvider(), ShikimoriAnimeProvider()]),
                AnimeResponseFactory(AnimeKeyboardFactory(AnimePayloadFactory())),
                renderer,
            )
            if "anime" in config.bot_settings.mods
            else None
        ),
        titles_controller=(
            TitlesController(
                TitlesService(
                    TitlesProvider(config.custom_titles),
                    SqliteTitlesRepository(
                        TitlesStatesDAO(), TitlesBagDAO(), database_settings
                    ),
                ),
                TelegramRollService(bot_service),
                user_service,
                TitlesResponseFactory(TitlesKeyboardFactory(TitlesPayloadFactory())),
                renderer,
            )
            if "titles" in config.bot_settings.mods
            else None
        ),
        play_controller=(
            PlayController(
                PlayService(
                    TelegramEventPlayersService(bot_service),
                    SqliteEventsRepository(EventsDao(), database_settings),
                    config.event.play_categories,
                ),
                PlayResponseFactory(
                    user_service,
                    ImageService(
                        config.event.default_winner_avatar, config.event.winner_pictures
                    ),
                ),
                renderer,
            )
            if "play" in config.bot_settings.mods
            else None
        ),
        reply_controller=(
            ReplyController(
                ReplyService(
                    long_messages=config.long_message, triggers=config.trigger_replies
                ),
                ReplyResponseFactory(),
                renderer,
            )
            if "reply" in config.bot_settings.mods
            else None
        ),
        captcha_controller=(
            CaptchaController(
                user_service,
                CaptchaService(config.captcha_properties, CaptchaRepository()),
                CaptchaResponseFactory(
                    config.captcha_properties,
                    CaptchaKeyboardFactory(CaptchaPayloadFactory()),
                ),
                renderer,
            )
            if "captcha" in config.bot_settings.mods
            else None
        ),
    )
    return controller

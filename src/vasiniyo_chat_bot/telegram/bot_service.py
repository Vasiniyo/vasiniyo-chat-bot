import asyncio
from functools import lru_cache
from io import BytesIO
import logging
import threading
from typing import Callable, Literal
import uuid

from telebot import REPLY_MARKUP_TYPES, TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import (
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberMember,
    File,
    InlineQueryResultArticle,
    InputFile,
    InputMediaPhoto,
    InputTextMessageContent,
    LinkPreviewOptions,
    Message,
    ReplyParameters,
)

from vasiniyo_chat_bot.safely_bot_utils import safe_wrapper
from vasiniyo_chat_bot.telegram.dto import (
    BoldTemplate,
    InlineCodeTemplate,
    ItalicTemplate,
    TextTemplate,
    UserContext,
    UserTemplate,
)
from vasiniyo_chat_bot.telegram.service.markdown_v2_service import MarkdownV2Service

logger = logging.getLogger(__name__)


class BotService:
    def __init__(self, bot: TeleBot, formatter: MarkdownV2Service):
        self._bot = bot
        self._formatter = formatter
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._start_loop, daemon=True).start()

    @lru_cache
    def get_me(self):
        logger.info("bot_get_me")
        return self._bot.get_me()

    def get_chat_member(self, chat_id: int, user_id: int) -> ChatMember | None:
        logger.info("get_chat_member", extra={"chat_id": chat_id, "user_id": user_id})
        try:
            return self._bot.get_chat_member(chat_id, user_id)
        except:
            logger.info(
                "member_not_found", extra={"chat_id": chat_id, "user_id": user_id}
            )
            return None

    @safe_wrapper(default=None)
    def get_profile_photo(self, user_id: int) -> bytes | None:
        file_info = self.get_user_profile_photo_file_info(user_id)
        if not file_info:
            return None
        logger.info("download_file", extra={"file_path": file_info.file_path})
        return self._bot.download_file(file_info.file_path)

    @safe_wrapper(default=None)
    def get_admin_title(self, ctx: UserContext) -> str | None:
        member = self.get_chat_member(ctx.chat_id, ctx.user_id)
        return getattr(member, "tag", getattr(member, "custom_title", None))

    @safe_wrapper(default=[])
    def get_chat_administrators(self, chat_id: int) -> list[ChatMember]:
        logger.info("fetch_admins", extra={"chat_id": chat_id})
        return self._bot.get_chat_administrators(chat_id)

    @safe_wrapper(default=None)
    def get_user_profile_photo_file_info(self, user_id: int) -> File | None:
        logger.info("get_user_profile_photo", extra={"user_id": user_id})
        photo = self._bot.get_user_profile_photos(user_id, limit=1)
        file_id = photo.photos[0][-1].file_id
        logger.info("get_file", extra={"file_id": file_id})
        return self._bot.get_file(file_id) if photo.photos else None

    @safe_wrapper(default=None)
    def set_title(self, ctx: UserContext, title: str) -> str | None:
        if len(title) > 16:
            return None
        if self.get_admin_title(ctx) == title:
            return title
        member = self.get_chat_member(ctx.chat_id, ctx.user_id)
        bot_user = self.get_chat_member(ctx.chat_id, self.get_me().id)
        if not isinstance(bot_user, ChatMemberAdministrator):
            return None
        if isinstance(member, ChatMemberAdministrator) and member.can_be_edited:
            logger.info(
                "set_custom_title",
                extra={"chat_id": ctx.chat_id, "user_id": ctx.user_id, "title": title},
            )
            self._bot.set_chat_administrator_custom_title(
                ctx.chat_id, ctx.user_id, title
            )
        elif isinstance(member, ChatMemberMember) and bot_user.can_manage_tags:
            logger.info(
                "set_member_tag",
                extra={"chat_id": ctx.chat_id, "user_id": ctx.user_id, "title": title},
            )
            self._bot.set_chat_member_tag(ctx.chat_id, ctx.user_id, title)
        else:
            return None
        return title

    @safe_wrapper(default=None)
    def edit_message_text_async(
        self,
        text_units: str | list[str | TextTemplate],
        ctx: UserContext,
        delay: int | None = 0,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        should_edit: Callable[[], bool] = lambda: True,
    ) -> None:
        async def edit_message():
            await asyncio.sleep(delay)
            if should_edit():
                self.edit_message_text(text_units, ctx, reply_markup=reply_markup)

        logger.info(
            "schedule editing",
            extra={
                "chat_id": ctx.chat_id,
                "message_id": ctx.message_id,
                "delay": delay,
            },
        )
        asyncio.run_coroutine_threadsafe(edit_message(), self._loop)

    @safe_wrapper(default=None)
    def edit_message_text(
        self,
        text_units: str | list[str | TextTemplate],
        ctx: UserContext,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        is_disabled_preview: bool = True,
    ) -> None:
        text = self._to_text(text_units)
        logger.info(
            "edit_message_text",
            extra={
                "chat_id": ctx.chat_id,
                "message_id": ctx.message_id,
                "message_text": text,
            },
        )
        self._bot.edit_message_text(
            text,
            ctx.chat_id,
            ctx.message_id,
            parse_mode="MarkdownV2",
            link_preview_options=LinkPreviewOptions(is_disabled=is_disabled_preview),
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def edit_message_caption(
        self,
        chat_id: int,
        message_id: int,
        caption: str,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
    ):
        logger.info(
            "edit_message_caption",
            extra={"chat_id": chat_id, "message_id": message_id, "caption": caption},
        )
        self._bot.edit_message_caption(
            chat_id=chat_id,
            message_id=message_id,
            caption=caption,
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def edit_message_media(
        self,
        photo: BytesIO,
        chat_id: int,
        message_id: int,
        caption: str | None = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
    ):
        logger.info(
            "edit_message_media", extra={"chat_id": chat_id, "message_id": message_id}
        )
        self._bot.edit_message_media(
            media=InputMediaPhoto(InputFile(photo), caption, "HTML"),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def clear_markup(self, ctx: UserContext):
        logger.info(
            "clear_message_markup",
            extra={"chat_id": ctx.chat_id, "message_id": ctx.message_id},
        )
        self._bot.edit_message_reply_markup(
            ctx.chat_id, ctx.message_id, reply_markup=None
        )

    def send_dice(self, emoji: Literal["🎲", "🎯", "🏀", "⚽", "🎰"], ctx: UserContext):
        logger.info(
            "send_dice",
            extra={
                "chat_id": ctx.chat_id,
                "message_id": ctx.message_id,
                "emoji": emoji,
            },
        )
        return self._bot.send_dice(
            ctx.chat_id,
            reply_to_message_id=ctx.message_id,
            emoji=emoji,
            reply_parameters=ReplyParameters(
                message_id=ctx.message_id, allow_sending_without_reply=True
            ),
        )

    @safe_wrapper(default=None)
    def answer_callback_query(self, text: str, query_id: int) -> None:
        logger.info(
            "answer_callback_query", extra={"query_id": query_id, "query": text}
        )
        self._bot.answer_callback_query(query_id, text=text, cache_time=3)

    @safe_wrapper(default=None)
    def answer_inline_query(
        self, commands: list[tuple[str, Callable[[], str]]], query_id: str
    ) -> None:
        inline_results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=title,
                input_message_content=InputTextMessageContent(get_content()),
            )
            for (title, get_content) in commands
        ]
        self._bot.answer_inline_query(query_id, inline_results, cache_time=0)

    @safe_wrapper(default=None)
    def send_message(
        self,
        text_units: str | list[str | TextTemplate],
        ctx: UserContext,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
        is_disabled_preview: bool = True,
    ) -> Message | None:
        reply_parameters = (
            ReplyParameters(message_id=ctx.message_id, allow_sending_without_reply=True)
            if ctx.message_id
            else None
        )
        text = self._to_text(text_units)
        logger.info(
            "send_message",
            extra={
                "chat_id": ctx.chat_id,
                "message_id": ctx.message_id,
                "message_text": text,
            },
        )
        return self._bot.send_message(
            ctx.chat_id,
            text,
            parse_mode="MarkdownV2",
            disable_notification=True,
            link_preview_options=LinkPreviewOptions(is_disabled=is_disabled_preview),
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
        )

    @safe_wrapper(default=None)
    def send_sticker(self, file_id: str, ctx: UserContext) -> None:
        logger.info(
            "send_sticker",
            extra={
                "chat_id": ctx.chat_id,
                "message_id": ctx.message_id,
                "file_id": file_id,
            },
        )
        self._bot.send_sticker(
            ctx.chat_id,
            file_id,
            reply_parameters=ReplyParameters(
                message_id=ctx.message_id, allow_sending_without_reply=True
            ),
        )

    @safe_wrapper(default=None)
    def send_photo(
        self,
        photo: BytesIO,
        ctx: UserContext,
        caption: (
            str | list[str | UserTemplate | BoldTemplate | ItalicTemplate] | None
        ) = None,
        reply_markup: REPLY_MARKUP_TYPES | None = None,
    ) -> Message:
        logger.info(
            "send_photo", extra={"chat_id": ctx.chat_id, "message_id": ctx.message_id}
        )
        reply_parameters = (
            ReplyParameters(message_id=ctx.message_id, allow_sending_without_reply=True)
            if ctx.message_id
            else None
        )
        return self._bot.send_photo(
            ctx.chat_id,
            photo=InputFile(photo),
            caption=self._to_text(caption) if caption else None,
            parse_mode="MarkdownV2",
            disable_notification=True,
            reply_markup=reply_markup,
            reply_parameters=reply_parameters,
        )

    @safe_wrapper(default=None)
    def delete_message(self, ctx: UserContext) -> None:
        logger.info(
            f"delete_message",
            extra={"chat_id": ctx.chat_id, "message_id": ctx.message_id},
        )
        self._bot.delete_message(ctx.chat_id, ctx.message_id)

    @safe_wrapper(default=None)
    def ban_chat_member(self, ctx: UserContext) -> None:
        logger.info(
            f"ban_chat_member", extra={"chat_id": ctx.chat_id, "user_id": ctx.user_id}
        )
        try:
            self._bot.ban_chat_member(ctx.chat_id, ctx.user_id)
        except ApiTelegramException as e:
            logger.info(
                "ban_chat_member_failed",
                extra={
                    "chat_id": ctx.chat_id,
                    "user_id": ctx.user_id,
                    "reason": e.description,
                },
            )

    def _start_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _to_text(self, text_units: str | list[str | TextTemplate]) -> str:
        if isinstance(text_units, str):
            return self._formatter.escape(text_units)
        text = ""
        for unit in text_units:
            if isinstance(unit, UserTemplate):
                member = self.get_chat_member(unit.chat_id, unit.user_id)
                if member:
                    text += self._formatter.to_link(
                        member.user.full_name, member.user.username
                    )
                else:
                    text += self._formatter.to_italic("Неизвестный")
            elif isinstance(unit, BoldTemplate):
                text += self._formatter.to_bold(unit.text)
            elif isinstance(unit, ItalicTemplate):
                text += self._formatter.to_italic(unit.text)
            elif isinstance(unit, InlineCodeTemplate):
                text += self._formatter.to_inline(unit.text)
            elif isinstance(unit, str):
                text += self._formatter.escape(unit)
        return text

import logging

from injector import inject

from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.module.reply.dto import MessageType
from vasiniyo_chat_bot.module.reply.dto import StickerTrigger
from vasiniyo_chat_bot.module.reply.dto import TextTrigger
from vasiniyo_chat_bot.module.reply.dto import TriggerReplies

_logger = logging.getLogger(__name__)


@inject
class ReplyReader:
    def __init__(
        self, config: Config, stickers_by_unique_id: dict[tuple[str, str], str]
    ):
        self._config = config
        self._stickers_by_unique_id = stickers_by_unique_id

    def load(self) -> TriggerReplies:
        stickers = self._load_stickers()
        text_replies = [
            *self._build_text_to_sticker(stickers),
            *self._build_text_to_text(
                key="text_to_text_to_target",
                to_target=True,
                fuzzy=False,
                exact_match=True,
            ),
            *self._build_text_to_text(key="text_to_text", to_target=False, fuzzy=True),
            *self._build_text_to_text(
                key="text_to_text_no_fuzzy", to_target=False, fuzzy=False, chance=0.1
            ),
        ]
        sticker_replies = self._build_sticker_to_sticker(stickers)
        return TriggerReplies(
            text_replies=text_replies, sticker_replies=sticker_replies
        )

    def _build_text_to_sticker(
        self, stickers: dict[str, str], exact_match=False
    ) -> list[TextTrigger]:
        return [
            TextTrigger(
                response_type=MessageType.STICKER,
                request=key,
                responses=self._to_sticker_list(stickers, value),
                chance=1.0,
                to_target=False,
                fuzzy=True,
                exact_match=exact_match,
            )
            for key, value in self._config.section.get("text_to_sticker", {}).items()
        ]

    def _build_text_to_text(
        self,
        *,
        key: str,
        to_target: bool,
        fuzzy: bool,
        exact_match=False,
        chance: float = 1.0,
    ) -> list[TextTrigger]:
        expanded = {
            req.replace(f"{{{category[0]}}}", value): self._to_list(res)
            for req, res in self._config.section.get(key, {}).items()
            for category in self._config.section.get("categories", {}).items()
            for value in category[1]
        }
        return [
            TextTrigger(
                response_type=MessageType.TEXT,
                request=req,
                responses=responses,
                chance=chance,
                to_target=to_target,
                fuzzy=fuzzy,
                exact_match=exact_match,
            )
            for req, responses in expanded.items()
        ]

    def _build_sticker_to_sticker(
        self, stickers: dict[str, str], exact_match=False
    ) -> list[StickerTrigger]:
        return [
            StickerTrigger(
                response_type=MessageType.STICKER,
                request=stickers[key],
                responses=self._to_sticker_list(stickers, value),
                chance=1.0,
                to_target=False,
                exact_match=exact_match,
                fuzzy=False,
            )
            for key, value in self._config.section.get("sticker_to_sticker", {}).items()
            if key in stickers
        ]

    def _expand_templates(self, template_dict: dict) -> dict[str, list[str]]:
        return {
            req.replace(f"{{{category[0]}}}", value): self._to_list(res)
            for req, res in template_dict.items()
            for category in self._config.section.get("categories", {}).items()
            for value in category[1]
        }

    def _load_stickers(self) -> dict[str, str]:
        stickers = {}
        for sticker_name, pack_with_uid in self._config.section.get(
            "unique_file_id", {}
        ).items():
            if sticker_name in stickers:
                _logger.warning("sticker_name already exists, rewriting it")
            pack_with_uid_array = pack_with_uid.split(";")
            if len(pack_with_uid_array) != 2:
                _logger.warning(
                    f"invalid sticker id format, expected: 'sticker_pack;uid', skipping",
                    extra={"sticker_info": pack_with_uid},
                )
                continue
            file_id = self._stickers_by_unique_id.get(
                (pack_with_uid_array[0], pack_with_uid_array[1])
            )
            if not file_id:
                _logger.warning(
                    f"sticker uid doesn't exist, skipping",
                    extra={
                        "sticker_pack_name": pack_with_uid_array[0],
                        "sticker_uid": pack_with_uid_array[1],
                    },
                )
                continue
            stickers[sticker_name] = file_id
        return stickers

    @staticmethod
    def _to_list(value: str | list[str]) -> list[str]:
        return [value] if isinstance(value, str) else value

    @staticmethod
    def _to_sticker_list(stickers, value: str | list[str]):
        return [stickers[v] for v in ReplyReader._to_list(value) if v in stickers]

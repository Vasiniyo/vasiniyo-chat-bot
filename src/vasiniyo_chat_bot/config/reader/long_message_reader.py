from injector import inject

from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.module.reply.dto import LongMessage


@inject
class LongMessageReader:
    def __init__(self, config: Config) -> None:
        self._config = config

    def load(self) -> LongMessage:
        return LongMessage(
            responses=self._config.section.get("long_message", {}).get(
                "long_message", ["А можно дубль покороче?"]
            ),
            max_len=self._config.section.get("long_message", {}).get(
                "message_max_len", 1000
            ),
        )

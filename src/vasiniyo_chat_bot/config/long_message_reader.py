from vasiniyo_chat_bot.module.reply.dto import LongMessage


class LongMessageReader:
    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> LongMessage:
        return LongMessage(
            responses=self._section.get("long_message", {}).get("long_message", []),
            max_len=self._section.get("long_message", {}).get("message_max_len", 1000),
        )

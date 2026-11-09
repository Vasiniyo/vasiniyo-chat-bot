from injector import inject

from vasiniyo_chat_bot.config.dto import Config


@inject
class StickersReader:
    def __init__(self, config: Config):
        self._config = config

    def load(self) -> set[str]:
        return {
            unique_id.split(";")[0]
            for unique_id in self._config.section.get("unique_file_id", {}).values()
        }

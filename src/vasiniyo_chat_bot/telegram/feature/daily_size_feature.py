from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.daily_size.daily_size_controller import (
    DailySizeController,
)
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.feature.feature import Feature


class DailySizeFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: DailySizeController | None,
        commands: dict[CommandKey, CommandInfo],
    ):
        self._controller = controller
        super().__init__(
            bot_username,
            allowed_chats,
            inline_handler=[
                lambda ctx: (
                    commands.get(CommandKey.DAILY_SIZE).name,
                    self._controller.get_daily_size(ctx),
                )
            ],
        )

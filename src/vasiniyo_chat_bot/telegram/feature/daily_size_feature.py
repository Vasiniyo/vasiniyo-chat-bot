from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.daily_size.daily_size_controller import (
    DailySizeController,
)
from vasiniyo_chat_bot.module.help.command import CommandKey
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.feature import Feature


@inject
class DailySizeFeature(Feature):
    def __init__(
        self,
        settings: BotSettings,
        bot_service: BotService,
        controller: DailySizeController,
    ):
        self._controller = controller
        super().__init__(
            settings,
            bot_service,
            inline_handler=[
                lambda ctx: (
                    settings.commands[CommandKey.DAILY_SIZE].name,
                    self._controller.get_daily_size(ctx),
                )
            ],
        )

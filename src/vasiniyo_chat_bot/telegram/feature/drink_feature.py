from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.drink.drink_controller import DrinkController
from vasiniyo_chat_bot.module.help.command import CommandKey
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.feature import Feature


@inject
class DrinkFeature(Feature):
    def __init__(
        self,
        settings: BotSettings,
        bot_service: BotService,
        controller: DrinkController,
    ):
        self._controller = controller
        super().__init__(
            settings,
            bot_service,
            inline_handler=[
                lambda ctx: (
                    settings.commands[CommandKey.DRINK_OR_NOT].name,
                    self._controller.advice_drink(ctx),
                )
            ],
        )

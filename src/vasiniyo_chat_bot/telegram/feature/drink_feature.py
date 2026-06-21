from vasiniyo_chat_bot.config.bot_settings_reader import CommandInfo
from vasiniyo_chat_bot.module.drink.drink_controller import DrinkController
from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.feature.feature import Feature


class DrinkFeature(Feature):
    def __init__(
        self,
        bot_username: str,
        allowed_chats: list[str],
        controller: DrinkController | None,
        commands: dict[CommandKey, CommandInfo],
    ):
        self._controller = controller
        super().__init__(
            bot_username,
            allowed_chats,
            inline_handler=[
                lambda ctx: (
                    commands.get(CommandKey.DRINK_OR_NOT).name,
                    self._controller.advice_drink(ctx),
                )
            ],
        )

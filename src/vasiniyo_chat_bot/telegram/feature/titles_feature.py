from injector import inject

from vasiniyo_chat_bot.config.dto import BotSettings
from vasiniyo_chat_bot.module.dto import Action
from vasiniyo_chat_bot.module.help.command import CommandInfo
from vasiniyo_chat_bot.module.help.command import CommandKey
from vasiniyo_chat_bot.module.payload_factory import PayloadFactory
from vasiniyo_chat_bot.module.titles.titles_controller import TitlesController
from vasiniyo_chat_bot.telegram.bot_service import BotService
from vasiniyo_chat_bot.telegram.feature.feature import Feature
from vasiniyo_chat_bot.telegram.filter import Filter
from vasiniyo_chat_bot.telegram.handler.query_handler import QueryHandler


@inject
class TitlesFeature(Feature):
    _valid_payload_actions = {
        Action.ROLL_RANDOM_D6,
        Action.ROLL_D6,
        Action.OPEN_RENAME_MENU,
        Action.OPEN_STEAL_MENU,
        Action.STEAL_TITLE,
        Action.OPEN_TITLES_BAG,
        Action.SET_TITLE_BAG,
        Action.GIFT_RECIPIENTS_MENU,
        Action.GIFT_TITLE_MENU,
        Action.GIVE_TITLE,
        Action.OPEN_EXCHANGE_TITLE_MENU,
        Action.EXCHANGE_TITLE,
    }

    def __init__(
        self,
        settings: BotSettings,
        bot_service: BotService,
        controller: TitlesController,
    ):
        self._controller = controller
        super().__init__(
            settings,
            bot_service,
            all_commands={
                CommandKey.RENAME: (
                    settings.commands.get(CommandKey.RENAME),
                    self._controller.handle_rename,
                )
            },
            callback_handlers=[
                QueryHandler(
                    settings.allowed_chats,
                    self._controller.dispatch_titles_callback,
                    Filter(
                        lambda call: PayloadFactory.has_action(
                            call.data,
                            {
                                Action.ROLL_RANDOM_D6,
                                Action.ROLL_D6,
                                Action.OPEN_RENAME_MENU,
                                Action.OPEN_STEAL_MENU,
                                Action.STEAL_TITLE,
                                Action.OPEN_TITLES_BAG,
                                Action.SET_TITLE_BAG,
                                Action.GIFT_RECIPIENTS_MENU,
                                Action.GIFT_TITLE_MENU,
                                Action.GIVE_TITLE,
                                Action.OPEN_EXCHANGE_TITLE_MENU,
                                Action.EXCHANGE_TITLE,
                            },
                        )
                    ),
                )
            ],
        )

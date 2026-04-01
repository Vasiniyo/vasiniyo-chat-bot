from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.bot_service import BotService


class HelpRenderer:
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    helps = {
        CommandKey.HELP: "Выводит список доступных команд и их описание.",
        CommandKey.ANIME: "Выбирает случайное аниме.",
        CommandKey.TOP_LIKES: "Показывает топ пользователей по лайкам.",
        CommandKey.LIKE: "Ставит лайк сообщению, на которое вы ответили.",
        CommandKey.RENAME: "Ставит случайную лычку.",
        CommandKey.DRINK_OR_NOT: "Говорит пить сегодня или нет.",
        CommandKey.PLAY: "Узнать своё значение в сегодняшней категории.",
        CommandKey.PLAYERS: "Показать всех игроков.",
        CommandKey.WINNER: "Показать победителя дня.",
        CommandKey.TOP_WINNERS: "Топ победителей за всё время.",
        CommandKey.TEST_NEW_CATEGORY: "Сыграть в случайную категорию.",
        CommandKey.TEST_NEW_WINNER: "Выбрать случайного победителя.",
    }

    def send(self, commands: dict[CommandKey, str], chat_id: int, message_id: int):
        help_text = f"Доступные команды:\n\n" + "\n".join(
            f"{title} - {self.helps.get(help_key, 'Описание отсутствует')}"
            for help_key, title in commands.items()
        )
        self.bot_service.send_message(help_text, chat_id, message_id)

    def send_unknown_command(self, chat_id: int, message_id: int):
        self.bot_service.send_message(
            "🤯 Я такой команды не знаю! Посмотреть доступные можно при помощи /help",
            chat_id,
            message_id,
        )

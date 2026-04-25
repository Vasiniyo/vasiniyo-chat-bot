from vasiniyo_chat_bot.module.help.command_key import CommandKey
from vasiniyo_chat_bot.telegram.dto import Response


class HelpResponseFactory:
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

    @staticmethod
    def send(commands: dict[CommandKey, str]):
        text = f"Доступные команды:\n\n" + "\n".join(
            f"{title} - {HelpResponseFactory.helps.get(help_key, 'Описание отсутствует')}"
            for help_key, title in commands.items()
        )
        return Response(text_units=text)

    @staticmethod
    def send_unknown_command():
        text = "🤯 Я такой команды не знаю! Посмотреть доступные можно при помощи /help"
        return Response(text_units=text)

from config import bot


def handle_help(message):
    from .dispatcher import COMMANDS

    help_text = "🤖 Доступные команды:\n\n" + "\n".join(
        f"/{cmd} - {desc}" for cmd, (_, desc) in COMMANDS.items()
    )
    bot.reply_to(message, help_text)


def handle_unknown(message):
    bot.reply_to(message, "🤯 Я такой команды не знаю! Введите /help")

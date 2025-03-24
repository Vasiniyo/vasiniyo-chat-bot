from telebot.types import InlineQueryResultArticle, InputTextMessageContent

from config import bot


def handle_help(message):
    from .dispatcher import COMMANDS

    help_text = "🤖 Доступные команды:\n\n" + "\n".join(
        f"/{cmd} - {desc}" for cmd, (_, desc) in COMMANDS.items()
    )
    bot.reply_to(message, help_text)


def handle_inline_help(query):
    from .dispatcher import COMMANDS

    commands = [
        InlineQueryResultArticle(
            id=ord,
            title=cmd,
            description=desc[1],
            input_message_content=InputTextMessageContent(f"/{cmd}"),
        )
        for ord, (cmd, desc) in enumerate(COMMANDS.items())
    ]
    bot.answer_inline_query(query.id, commands)


def handle_unknown(message):
    bot.reply_to(message, "🤯 Я такой команды не знаю! Введите /help")

from telebot.types import InlineQueryResultArticle, InputTextMessageContent

from config import phrases
import safely_bot_utils as bot


def handle_help(commands):
    help_text = f"{phrases('help_header')}\n\n" + "\n".join(
        f"/{cmd} - {desc}" for cmd, (_, desc) in commands.items()
    )
    return bot.reply_to(help_text)


def handle_inline_help(commands):
    inline_results = [
        InlineQueryResultArticle(
            id=ord,
            title=cmd,
            description=desc[1],
            input_message_content=InputTextMessageContent(f"/{cmd}"),
        )
        for ord, (cmd, desc) in enumerate(commands.items())
    ]
    return bot.answer_inline_query(inline_results)


handle_unknown = bot.reply_to

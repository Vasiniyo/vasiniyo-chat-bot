from config import bot


def handle_help(message):
    from .dispatcher import COMMANDS

    help_text = "🤖 Доступные команды:\n\n" + "\n".join(
        f"/{cmd} - {desc}" for cmd, (_, desc) in COMMANDS.items()
    )
    bot.reply_to(message, help_text)

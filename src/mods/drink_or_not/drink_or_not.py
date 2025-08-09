import random

from config import drinks, phrases
import safely_bot_utils as bot

from ..register import reg_command

# ========== COMMANDS =========================================================


@reg_command("drink_or_not", phrases("drink_or_not_help"), drinks)
def handle_drink_or_not(source):
    def _handle(message):
        idx = bot.daily_hash(message.from_user.id) % len(source)
        emoji = random.choice(source[idx].get("emoji"))
        answer = random.choice(source[idx].get("answer"))
        return bot.reply_to(f"{emoji} {answer}")(message)

    return _handle


# reg_command("drink_or_not", phrases("drink_or_not_help"))(handle_drink_or_not(drinks))

from random import choice, random

from commands.utils import handler, laplace_cdf
from config import MESSAGE_MAX_LEN, long_message
import safely_bot_utils as bot

from ..register import reg_handler

# scales values between 0 and maximal allowed message length in telegram
scaler = lambda x: x / 4096
probability = laplace_cdf(scaler(MESSAGE_MAX_LEN / 2))(scaler(MESSAGE_MAX_LEN * 2))

is_long_message = (
    lambda m: len(m.text) > 100 and random() <= probability(scaler(len(m.text))) / 2.0
)


# ========== HANDLERS =========================================================


@reg_handler(handler(is_long_message), long_message)
def handle_long(answers):
    return lambda m: bot.reply_to(choice(answers))(m)


# reg_handler(handler(is_long_message))(handle_long(long_message))

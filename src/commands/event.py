import random

from database.events import commit_win, get_last_winner, is_day_passed
import safely_bot_utils as bot


def get_players(chat_id):
    are_players = lambda user: user.can_be_edited or user.status == "creator"
    players = filter(are_players, bot.get_chat_administrators(chat_id))
    return list(map(lambda a: a.user, players))


def play(message):
    event_id = 0
    chat_id = message.chat.id
    players = get_players(chat_id)
    day_passed = is_day_passed(chat_id, event_id)
    if day_passed == 1 or day_passed is None:
        winner = random.choice(players)
        commit_win(chat_id, winner.id, event_id)
        bot.reply_with_user_links("Эспер дня: " + bot.to_link_user(winner))(message)
    else:
        winner_id = get_last_winner(chat_id, event_id)
        winner = next(filter(lambda p: p.id == winner_id, players))
        bot.reply_with_user_links(
            "Ничего не поменялось.\nЭспер дня: " + bot.to_link_user(winner)
        )(message)


def send_players(message):
    answer = "\n".join(
        f"{i + 1}. {username}"
        for i, username in enumerate(
            map(bot.to_link_user, get_players(message.chat.id))
        )
    )
    bot.reply_with_user_links(answer)(message)

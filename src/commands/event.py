from config import phrases
from database.events import commit_win, fetch_top, get_last_winner, is_day_passed
import safely_bot_utils as bot

from .how_much import daily_percentage

esper_event_id = 0


def get_players(chat_id):
    are_players = lambda user: user.can_be_edited or user.status == "creator"
    players = filter(are_players, bot.get_chat_administrators(chat_id))
    return list(map(lambda a: a.user, players))


def play(message):
    event_id = esper_event_id
    chat_id = message.chat.id
    players = get_players(chat_id)

    def _find_next_winner():
        winner = max(players, key=daily_percentage)
        commit_win(chat_id, winner.id, event_id)
        return phrases(
            "play_select", bot.to_link_user(winner), daily_percentage(winner)
        )

    if len(players) == 0:
        return bot.reply_to(phrases("play_zero_players"))(message)
    day_passed = is_day_passed(chat_id, event_id)
    if day_passed == 1 or day_passed is None:
        answer = _find_next_winner()
    else:
        winner_id = get_last_winner(chat_id, event_id)
        winner = next(filter(lambda p: p.id == winner_id, players), None)
        if winner:
            answer = phrases("play_already_selected", bot.to_link_user(winner))
        else:
            answer = _find_next_winner()
    return bot.reply_with_user_links(answer)(message)


def send_players(message):
    answer = "\n".join(
        f"{i + 1}. {username}"
        for i, username in enumerate(
            map(bot.to_link_user, get_players(message.chat.id))
        )
    )
    bot.reply_with_user_links(answer)(message)


def handle_top_espers(message):
    bot.reply_top(
        lambda: fetch_top(message.chat.id, esper_event_id, 10),
        message.chat.id,
        phrases("top_espers_header"),
    )(message)

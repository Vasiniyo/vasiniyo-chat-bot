"""Test command for simulating category reset."""

from contextlib import contextmanager
import datetime
import logging
import random

from commands.play.play_utils import (
    CATEGORIES,
    get_current_playable_category,
    get_player_value,
)
from commands.play_event import PLAY_EVENT_ID, get_players
from database.events import commit_win, get_last_winner
from database.utils import commit_query, database_name, fetch_number
import safely_bot_utils as bot

_last_test_win = None
logger = logging.getLogger(__name__)


@contextmanager
def revert_db_changes():
    """Context manager to revert database changes made during testing."""
    global _last_test_win
    _last_test_win = None

    try:
        yield
    finally:
        if _last_test_win:
            chat_id, user_id, timestamp = _last_test_win
            commit_query(
                """
                DELETE FROM events 
                WHERE chat_id = ? AND winner_user_id = ? AND event_id = ? AND last_played = ?
                """,
                (chat_id, user_id, PLAY_EVENT_ID, timestamp),
            )
            _last_test_win = None


def handle_test_new_category(message):
    """Simulate a new day category reset for testing."""
    chat_id = message.chat.id
    rng = random.Random()
    category = get_current_playable_category(chat_id, test=True)
    players = list(get_players(chat_id))
    sender = message.from_user
    if not any(p.id == sender.id for p in players):
        players.append(sender)
    if len(players) == 0:
        bot.reply_to("❌ No eligible players found")(message)
        return
    player_values = []
    for player in players:
        value = get_player_value(category, chat_id, player.id)
        player_values.append((player, value))
    winner_value = category.get_winner_value()
    if isinstance(category.winner_value, int):
        exact_winners = [(p, v) for p, v in player_values if v == winner_value]
        if exact_winners:
            winner, value = rng.choice(exact_winners)
            winner_name = bot.to_link_user(winner)
        else:
            winner = None
            value = winner_value
            winner_name = "🤖 Bot (no player hit the target value)"
    else:
        if category.winner_value == "max":
            winner, value = max(player_values, key=lambda x: x[1])
        else:
            winner, value = min(player_values, key=lambda x: x[1])
        winner_name = bot.to_link_user(winner)

    category_name_escaped = bot.escape_markdown_v2(category.name)
    winner_value_type_escaped = bot.escape_markdown_v2(category.winner_value)
    target_value_escaped = bot.escape_markdown_v2(winner_value)
    value_escaped = bot.escape_markdown_v2(value)

    lines = [
        "========= [TEST] =========",
        "Simulating category reset.",
        "==========================",
        f"New category: {category_name_escaped}",
        f"Winner value type: {winner_value_type_escaped}",
        f"Target value: {target_value_escaped}",
        f"New winner: {winner_name} {value_escaped}",
        "",
        "Values of all players:",
    ]
    sorted_players = sorted(player_values, key=lambda x: x[1], reverse=True)
    for player, player_value in sorted_players:
        is_winner = player == winner if winner else False
        winner_mark = " 👑" if is_winner else ""
        player_value_escaped = bot.escape_markdown_v2(player_value)
        lines.append(
            f"  {bot.to_link_user(player)}: {player_value_escaped}{winner_mark}"
        )

    with revert_db_changes():
        if winner:
            global _last_test_win
            timestamp = int(datetime.datetime.now().timestamp())
            _last_test_win = (chat_id, winner.id, timestamp)
            commit_query(
                """
                INSERT INTO events (chat_id, winner_user_id, event_id, last_played) 
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, winner.id, PLAY_EVENT_ID, timestamp),
            )
    bot.reply_with_user_links("\n".join(lines))(message)

from contextlib import contextmanager
import datetime
import logging
import random
from typing import Any, List, Optional, Tuple

from commands.play.play_utils import get_current_playable_category
from commands.play_event import PLAY_EVENT_ID, get_players, send_congratulations
from config import config
from database.events import commit_win, get_last_winner
from database.utils import commit_query, database_name, fetch_number
import safely_bot_utils as bot

_last_test_win: Optional[Tuple[int, int, int]] = None
logger = logging.getLogger(__name__)


@contextmanager
def revert_db_changes():
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
    chat_id = message.chat.id
    rng = random.Random()
    category = get_current_playable_category(chat_id, test=True)
    players: List = list(get_players(chat_id))
    sender = message.from_user
    if not any(p.id == sender.id for p in players):
        players.append(sender)
    if len(players) == 0:
        bot.reply_to("❌ No eligible players found")(message)
        return
    player_values = []
    for player in players:
        user_hash = bot.daily_hash(player.id)
        value = category.get_random_value_for_user(user_hash)
        player_values.append((player, value))

    win_type = category.win_value.type
    win_target = category.win_value.value

    if win_type == "exact":
        exact_winners = [(p, v) for p, v in player_values if v == win_target]
        if exact_winners:
            winner, value = rng.choice(exact_winners)
            winner_name = bot.to_link_user(winner)
        else:
            winner = None
            value = win_target
            winner_name = "🤖 Bot (no player hit the target value)"
    elif win_type == "max":
        winner, value = max(player_values, key=lambda x: x[1])
        winner_name = bot.to_link_user(winner)
    else:
        winner, value = min(player_values, key=lambda x: x[1])
        winner_name = bot.to_link_user(winner)

    category_name_escaped = bot.escape_markdown_v2(category.name)
    win_type_escaped = bot.escape_markdown_v2(win_type)
    target_value_escaped = bot.escape_markdown_v2(str(win_target))
    value_escaped = bot.escape_markdown_v2(str(value))

    lines = [
        "========= [TEST] =========",
        "Simulating category reset.",
        "==========================",
        f"New category: {category_name_escaped}",
        f"Winner value type: {win_type_escaped}",
        f"Target value: {target_value_escaped}",
        f"New winner: {winner_name} {value_escaped}",
        "",
        "Values of all players:",
    ]
    sorted_players = sorted(player_values, key=lambda x: x[1], reverse=True)
    for player, player_value in sorted_players:
        is_winner = player == winner if winner else False
        winner_mark = " 👑" if is_winner else ""
        player_value_escaped = bot.escape_markdown_v2(str(player_value))
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


def handle_test_send_congratz(message):
    chat_id = message.chat.id
    category = get_current_playable_category(chat_id)
    user = message.from_user
    user_hash = bot.daily_hash(user.id)
    value = category.get_random_value_for_user(user_hash)
    send_congratulations(user, value, category, message)


def handle_test_all_categories(message):
    from commands.play.play_config import CATEGORIES

    chat_id = message.chat.id
    user = message.from_user

    lines = ["========= [TEST] =========", "All categories:", ""]

    for cat_name, cat_spec in CATEGORIES.items():
        lines.append(f"• {cat_name}")

    bot.reply_to("\n".join(lines))(message)


def handle_test_win_goal(message):
    chat_id = message.chat.id
    category = get_current_playable_category(chat_id)

    category_name = category.locale.name.get(config.language, category.name)
    category_name_escaped = bot.escape_markdown_v2(category_name)

    win_goal = category.win_value.get_goal_text(config.language)
    win_goal_escaped = bot.escape_markdown_v2(win_goal)

    answer = f"Category: {category_name_escaped}\nWin goal: {win_goal_escaped}"
    bot.reply_to(answer)(message)

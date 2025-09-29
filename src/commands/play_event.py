"""Play event handlers for the bot."""

from io import BytesIO
import logging
import random

from PIL import Image

from config import default_winner_avatar, phrases, winner_pictures
from database.events import commit_win, fetch_top, get_last_winner, is_day_passed
import safely_bot_utils as bot

from .play.play_utils import get_current_playable_category, get_player_value

# Event ID for play categories
PLAY_EVENT_ID = 1


def get_players(chat_id):
    """Get all eligible players (admins who can be edited or creators)."""
    are_players = lambda user: user.can_be_edited or user.status == "creator"
    players = filter(are_players, bot.get_chat_administrators(chat_id))
    return list(map(lambda a: a.user, players))


def send_congratulations(winner, value, category_name, message):
    """Send a congratulations message with winner picture."""
    try:
        profile_photo = bot.download_profile_photo(winner.id)
        avatar = Image.open(
            BytesIO(profile_photo) if profile_photo else default_winner_avatar
        )
        winner_picture_template = winner_pictures[
            bot.daily_hash(winner.id) % len(winner_pictures)
        ]
        avatar_size = winner_picture_template.get("avatar_size")
        avatar = avatar.resize((avatar_size, avatar_size))
        background = Image.open(winner_picture_template.get("background"))
        background.paste(
            avatar,
            (
                winner_picture_template.get("avatar_position_x"),
                winner_picture_template.get("avatar_position_y"),
            ),
        )
        output = BytesIO()
        background.save(output, format="PNG")
        output.seek(0)

        # TODO  remake congratz msg as a member of PlayableCategory
        msg_text = f"🏆 Победитель дня в категории '{category_name}': {bot.to_link_user(winner)} [{value}]"
        bot.send_photo_with_user_links(background, msg_text)(message)
    except Exception as e:
        logging.exception(e)
        msg_text = f"🏆 Победитель дня в категории '{category_name}': {bot.to_link_user(winner)} [{value}]"
        bot.reply_with_user_links(msg_text)(message)


def handle_play(message):
    """Handle the /play command - show user's value in current category."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    category = get_current_playable_category(chat_id)
    value = get_player_value(category, chat_id, user_id)

    # Get the tier for this value
    tier = category.get_tier_for_value(value)

    if tier:
        # Select random phrase and emoji for this tier
        phrase = random.choice(tier.phrases)
        emoji = "🎲"  # Default emoji, can be customized per category

        answer = f"{emoji} [{category.name}]\n[{value}] {phrase}"
    else:
        answer = f"❌ Ошибка: значение {value} вне диапазона категории {category.name}"

    bot.reply_to(answer)(message)


def handle_winner(message):
    """Handle the /winner command - show or select today's winner."""
    chat_id = message.chat.id
    players = get_players(chat_id)

    if len(players) == 0:
        bot.reply_to("❌ В чате нет подходящих участников (нужны админы)")(message)
        return

    # Get current category
    category = get_current_playable_category(chat_id)
    winner_value = category.get_winner_value()

    # Check if we need to select a new winner
    day_passed = is_day_passed(chat_id, PLAY_EVENT_ID)

    if day_passed == 1 or day_passed is None:
        # Find winner(s) - those whose value equals or is closest to winner_value
        player_values = [
            (p, get_player_value(category, chat_id, p.id)) for p in players
        ]

        # If winner_value is a specific number, find exact matches
        exact_winners = [(p, v) for p, v in player_values if v == winner_value]

        if exact_winners:
            # If multiple players hit the exact value, pick one randomly
            winner, value = random.choice(exact_winners)
        else:
            # Find closest value
            if category.winner_value == "max":
                winner, value = max(player_values, key=lambda x: x[1])
            elif category.winner_value == "min":
                winner, value = min(player_values, key=lambda x: x[1])
            else:
                # Find closest to target value
                winner, value = min(
                    player_values, key=lambda x: abs(x[1] - winner_value)
                )

        # Save winner to database
        commit_win(chat_id, winner.id, PLAY_EVENT_ID)

        # Send congratulations
        send_congratulations(winner, value, category.name, message)
    else:
        # Show existing winner
        last_winner_id = get_last_winner(chat_id, PLAY_EVENT_ID)
        last_winner = next(filter(lambda p: p.id == last_winner_id, players), None)

        if last_winner:
            value = get_player_value(category, chat_id, last_winner.id)
            answer = f"🏆 Сегодняшний победитель в категории '{category.name}': {bot.to_link_user(last_winner)} [{value}]"
            bot.reply_with_user_links(answer)(message)
        else:
            # The previous winner is no longer an admin, select new one
            handle_winner(message)


def handle_top_winners(message):
    """Show top winners across all categories."""
    bot.reply_top(
        lambda: fetch_top(message.chat.id, PLAY_EVENT_ID, 10),
        message.chat.id,
        "🏆 Топ победителей за всё время:",
    )(message)

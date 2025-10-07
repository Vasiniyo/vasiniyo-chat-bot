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
logger = logging.getLogger(__name__)


def get_players(chat_id):
    """Get all eligible players (admins who can be edited or creators)."""
    logger.info(" GET_PLAYER ".center(50, "="))
    logger.info(f"Getting players for chat_id: {chat_id}")

    admins = bot.get_chat_administrators(chat_id)
    logger.info(f"Total admins fetched: {len(admins)}")

    for admin in admins:
        logger.debug(
            f"Admin: {admin.user.id} ({admin.user.username}), "
            f"status: {admin.status}, can_be_edited: {admin.can_be_edited}"
        )

    are_players = lambda user: user.can_be_edited or user.status == "creator"
    eligible_admins = list(filter(are_players, admins))
    logger.info(f"Eligible players (can_be_edited or creator): {len(eligible_admins)}")

    players = list(map(lambda a: a.user, eligible_admins))

    for player in players:
        logger.info(f"Eligible player: {player.id} ({player.username})")
    logger.info("=" * 50)

    return players


def send_congratulations(user, value, category_name, message):
    """Send a congratulations message with winner picture."""
    category_name_escaped = bot.escape_markdown_v2(category_name)
    winner_value_escaped = bot.escape_markdown_v2(value)

    # TODO  remake congratz msg as a member of PlayableCategory
    msg_text = (
        "🏆 Победитель дня: \n\t \\[{}]".format(category_name_escaped)
        + "\n\t \\[{}]".format(bot.to_link_user(user))
        + "\n\t󰆥 \\[{}]".format(winner_value_escaped)
    )

    # IMAGE
    try:
        profile_photo = bot.download_profile_photo(user.id)
        avatar = Image.open(
            BytesIO(profile_photo) if profile_photo else default_winner_avatar
        )
        winner_picture_template = winner_pictures[
            bot.daily_hash(user.id) % len(winner_pictures)
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

        bot.send_photo_with_user_links(background, msg_text)(message)
    except Exception as e:
        logging.exception(e)
        bot.reply_with_user_links(msg_text)(message)


def handle_play(message):
    """Handle the /play command - show user's value in current category."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    category = get_current_playable_category(chat_id)
    value = get_player_value(category, chat_id, user_id)

    tier = category.get_tier_for_value(value)

    if tier:
        phrase = random.choice(tier.phrases)
        emoji = "🎲"  # TODO possibly select emoji for each category

        answer = f"{emoji} [{category.name}]\n[{value}] {phrase}"
    else:
        answer = f"❌ Ошибка: значение {value} вне диапазона категории {category.name}"

    bot.reply_to(answer)(message)


def handle_winner(message):
    """Handle the /winner command - show or select today's winner."""
    logger.info(" HANDLE_WINNER ".center(50, "="))

    chat_id = message.chat.id
    players = get_players(chat_id)

    if len(players) == 0:
        bot.reply_to("❌ В чате нет подходящих участников (нужны админы)")(message)
        return

    category = get_current_playable_category(chat_id)
    winner_value = category.get_winner_value()
    day_passed = is_day_passed(chat_id, PLAY_EVENT_ID)

    # NOTE new players would have to wait untils the day resets to particupate
    if day_passed == 1 or day_passed is None:
        logger.info(f"Selecting new winner!")
        player_values = [
            (p, get_player_value(category, chat_id, p.id)) for p in players
        ]

        logger.info(f"=== Player values for category '{category.name}' ===")
        for player, value in player_values:
            logger.info(f"\tPlayer: {player.id} ({player.username}) -> Value: {value}")
        logger.info(f"Category winner_value type: {category.winner_value}")

        # NOTE needs testing
        if category.winner_value == "exact":
            exact_winners = [(p, v) for p, v in player_values if v == winner_value]
            if exact_winners:
                winner, value = random.choice(exact_winners)
                logger.info(
                    f"Selected exact winner: {winner.id} ({winner.username}) with value: {value}"
                )
            else:  # TODO: count a win for a bot, when no players won.
                # Currently it chooses the closes one to the winning value
                winner, value = min(
                    player_values, key=lambda x: abs(x[1] - winner_value)
                )
                logger.info(
                    f"Selected closest to exact winner: {winner.id} ({winner.username}) with value: {value}"
                )
        elif category.winner_value == "max":
            winner, value = max(player_values, key=lambda x: x[1])
            logger.info(
                f"Selected max winner: {winner.id} ({winner.username}) with value: {value}"
            )
        elif category.winner_value == "min":
            winner, value = min(player_values, key=lambda x: x[1])
            logger.info(
                f"Selected min winner: {winner.id} ({winner.username}) with value: {value}"
            )
        else:
            logger.info(f"Unknown winner_value type category")

        commit_win(chat_id, winner.id, PLAY_EVENT_ID)
        send_congratulations(winner, value, category.name, message)

    else:
        logger.info(f"Looking for previous winner")
        last_winner_id = get_last_winner(chat_id, PLAY_EVENT_ID)
        last_winner = next(filter(lambda p: p.id == last_winner_id, players), None)

        if last_winner:
            value = get_player_value(category, chat_id, last_winner.id)

            category_name_escaped = bot.escape_markdown_v2(category.name)
            winner_value_type_escaped = bot.escape_markdown_v2(category.winner_value)
            target_value_escaped = bot.escape_markdown_v2(winner_value)
            value_escaped = bot.escape_markdown_v2(value)
            answer = (
                "🏆 Сегодняшний победитель в категории \\[{}]: \\[{}] \\[{}]".format(
                    category_name_escaped, bot.to_link_user(last_winner), value_escaped
                )
            )
            bot.reply_with_user_links(answer)(message)

        else:
            handle_winner(message)

    logger.info("=" * 50)


def handle_top_winners(message):
    """Show top winners across all categories."""
    bot.reply_top(
        lambda: fetch_top(message.chat.id, PLAY_EVENT_ID, 10),
        message.chat.id,
        "🏆 Топ победителей за всё время:",
    )(message)

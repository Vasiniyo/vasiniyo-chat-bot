"""Play event handlers for the bot."""

from io import BytesIO
import logging
import random

from PIL import Image

from config import default_winner_avatar, lang, phrases, winner_pictures
from database.events import commit_win, fetch_top, get_last_winner, is_day_passed
import safely_bot_utils as bot

from .play.play import PlayableCategory
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


def send_congratulations(user, value, category: PlayableCategory, message):
    """Send a congratulations message with winner picture."""

    category_name = category.locale.name.get(lang, category.name)
    category_name_escaped = bot.escape_markdown_v2(category_name)

    value_str = str(value)
    value_escaped = bot.escape_markdown_v2(value_str)

    units = category.locale.units.get(lang, "")
    units_escaped = bot.escape_markdown_v2(units)

    win_goal = category.win_value.get_goal_text(lang)
    win_goal_escaped = bot.escape_markdown_v2(win_goal)

    msg_text = (
        f"🏆 Победитель дня в категории:\n\t{category_name_escaped}:\n"
        f"{bot.to_link_user(user)}\n"
        f"{win_goal_escaped} \\[{value_escaped} {units_escaped}]"
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
    chat_id = message.chat.id
    user_id = message.from_user.id

    category = get_current_playable_category(chat_id)
    value = get_player_value(category, chat_id, user_id)

    tier = category.get_tier_for_value(value)

    if tier:
        phrases_list = tier.locale.phrases.get(lang, [])
        if phrases_list:
            phrase = random.choice(phrases_list)
        else:
            phrase = "Результат получен!"

        emoji = "🎲"
        category_name = category.locale.name.get(lang, category.name)
        units = category.locale.units.get(lang, "")

        answer = f"{emoji} [{category_name}]\n[{value} {units}] {phrase}"
    else:
        category_name = category.locale.name.get(lang, category.name)
        answer = f"❌ Ошибка: значение {value} вне диапазона категории {category_name}"

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
    winner_value = category.win_value.value
    win_type = category.win_value.type
    day_passed = is_day_passed(chat_id, PLAY_EVENT_ID)

    if day_passed == 1 or day_passed is None:
        logger.info(f"Selecting new winner!")
        player_values = [
            (p, get_player_value(category, chat_id, p.id)) for p in players
        ]

        logger.info(f"=== Player values for category '{category.name}' ===")
        for player, value in player_values:
            logger.info(f"\tPlayer: {player.id} ({player.username}) -> Value: {value}")
        logger.info(f"Category win_value type: {win_type}")

        winner = None
        value = None

        if win_type == "exact":
            exact_winners = [(p, v) for p, v in player_values if v == winner_value]
            if exact_winners:
                winner, value = random.choice(exact_winners)
                logger.info(
                    f"Selected exact winner: {winner.id} ({winner.username}) with value: {value}"
                )
            else:
                winner, value = min(
                    player_values, key=lambda x: abs(x[1] - winner_value)
                )
                logger.info(
                    f"Selected closest to exact winner: {winner.id} ({winner.username}) with value: {value}"
                )
        elif win_type == "max":
            winner, value = max(player_values, key=lambda x: x[1])
            logger.info(
                f"Selected max winner: {winner.id} ({winner.username}) with value: {value}"
            )
        elif win_type == "min":
            winner, value = min(player_values, key=lambda x: x[1])
            logger.info(
                f"Selected min winner: {winner.id} ({winner.username}) with value: {value}"
            )
        else:
            logger.info(f"Unknown win_value type category")

        if winner is not None and value is not None:
            commit_win(chat_id, winner.id, PLAY_EVENT_ID)
            send_congratulations(winner, value, category, message)

    else:
        logger.info(f"Looking for previous winner")
        last_winner_id = get_last_winner(chat_id, PLAY_EVENT_ID)
        last_winner = next(filter(lambda p: p.id == last_winner_id, players), None)

        if last_winner:
            value = get_player_value(category, chat_id, last_winner.id)

            category_name = category.locale.name.get(lang, category.name)
            category_name_escaped = bot.escape_markdown_v2(category_name)
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

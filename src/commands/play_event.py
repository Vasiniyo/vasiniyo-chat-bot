"""Play event handlers for the bot."""

from io import BytesIO
import logging
import random

from PIL import Image

from config import config
from database.events import commit_win, fetch_top, get_last_winner, is_day_passed
import safely_bot_utils as bot

from .play.play import PlayableCategory
from .play.play_utils import get_current_playable_category

# Event ID for play categories
PLAY_EVENT_ID = 0
logger = logging.getLogger(__name__)


def _to_bold(str: str) -> str:
    return f"*{str}*"


def _to_italic(str: str) -> str:
    return f"_{str}_"


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


def handle_play(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    category = get_current_playable_category(chat_id)
    user_hash = bot.daily_hash(user_id)
    value = category.get_random_value_for_user(user_hash)

    tier = category.get_tier_for_value(value)

    if tier:
        phrases_list = tier.locale.phrases.get(config.language, [])
        if phrases_list:
            phrase = random.choice(phrases_list)
        else:
            phrase = "Результат получен!"

        # TODO make this locale-based
        # fmt: off
        msg_template = (
            "{intro} {cat}"
            "\n\n{measuring} {units}\\!"
            "\n{mark}\\[{value}\\]: {phrase}"
        )
        # fmt: on

        intro_formatted = bot.escape_markdown_v2("Играем в категорию....:")
        measuring_formatted = bot.escape_markdown_v2("Хе-хе! Меряю, сколько в тебe")

        category_name = category.locale.name.get(config.language, category.name)
        units = category.locale.units.get(config.language, "")

        category_name_formatted = bot.escape_markdown_v2(category_name)
        units_formatted = bot.escape_markdown_v2(units)
        value_formatted = bot.escape_markdown_v2(str(value))
        phrase_formatted = bot.escape_markdown_v2(phrase)

        emoji = category.get_emoji_for_value(value, seed=None)
        mark = bot.escape_markdown_v2(f"  {emoji} ")

        answer = msg_template.format(
            intro=intro_formatted,
            cat=_to_bold(category_name_formatted),
            measuring=measuring_formatted,
            units=units_formatted,
            mark=mark,
            value=_to_bold(value_formatted),
            phrase=_to_italic(phrase_formatted),
        )

    else:
        category_name = category.locale.name.get(config.language, category.name)
        answer = f"❌ Ошибка: значение {value} вне диапазона категории {category_name}"

    bot.reply_with_user_links(answer, mode="MarkdownV2")(message)


def _format_winner_msg_text(user, value, category: PlayableCategory):
    # fmt: off
    msg_template = (
        "{intro} \\({cat}\\):" 
        "\n{mark} {user}\\!" 
        "\n\nЦелых {value} {units}\\!" 
        "\n{outro}"
    )
    # fmt: on

    # TODO: move to the *locale* config
    intro = bot.escape_markdown_v2("Победитель в сегодняшей категории")
    outro = bot.escape_markdown_v2("Ого! Поздравляю!")

    user_str = bot.to_link_user_v2(user)

    category_name = category.locale.name.get(config.language, category.name)
    category_name_formatted = bot.escape_markdown_v2(category_name)

    emoji = category.get_emoji_for_value(value, force_top=True)
    value_mark = bot.escape_markdown_v2(f"  {emoji} ")

    value_str = f"[{str(value)}]"
    value_formatted = bot.escape_markdown_v2(value_str)

    units = category.locale.units.get(config.language, "")
    units_formatted = bot.escape_markdown_v2(units)

    win_goal = category.win_value.get_goal_text(config.language)
    win_goal_formatted = bot.escape_markdown_v2(win_goal)

    msg_text = msg_template.format(
        intro=_to_bold(intro),
        cat=_to_italic(category_name_formatted),
        mark=value_mark,
        user=user_str,
        value=_to_bold(value_formatted),
        units=units_formatted,
        outro=outro,
    )
    return msg_text


def send_congratulations(user, value, category: PlayableCategory, message):
    """Send a congratulations message with winner picture."""

    msg_text = _format_winner_msg_text(user, value, category)
    # IMAGE
    try:
        profile_photo = bot.download_profile_photo(user.id)
        avatar = Image.open(
            BytesIO(profile_photo)
            if profile_photo
            else config.event.default_winner_avatar
        )
        winner_picture_template = config.event.winner_pictures[
            bot.daily_hash(user.id) % len(config.event.winner_pictures)
        ]
        avatar_size = winner_picture_template.avatar_size
        avatar = avatar.resize((avatar_size, avatar_size))
        background = Image.open(winner_picture_template.background)
        background.paste(
            avatar,
            (
                winner_picture_template.avatar_position_x,
                winner_picture_template.avatar_position_y,
            ),
        )
        output = BytesIO()
        background.save(output, format="PNG")
        output.seek(0)

        bot.send_photo_with_user_links(background, msg_text, parse_mode="MarkdownV2")(
            message
        )
    except Exception as e:
        logging.exception(e)

        bot.reply_with_user_links(msg_text, mode="MarkdownV2")(message)


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
            (p, category.get_random_value_for_user(bot.daily_hash(p.id)))
            for p in players
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
            user_hash = bot.daily_hash(last_winner.id)
            value = category.get_random_value_for_user(user_hash)
            msg_text = _format_winner_msg_text(last_winner, value, category)

            bot.reply_with_user_links(msg_text, mode="MarkdownV2")(message)

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

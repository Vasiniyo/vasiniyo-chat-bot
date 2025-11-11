from io import BytesIO
import logging

from PIL import Image

from config import config
from database.events import commit_win, fetch_top, get_last_winner, is_day_passed
import safely_bot_utils as bot

from .how_much import daily_percentage

esper_event_id = 0


def get_players(chat_id):
    are_players = lambda user: user.can_be_edited or user.status == "creator"
    players = filter(are_players, bot.get_chat_administrators(chat_id))
    return list(map(lambda a: a.user, players))


def send_congratulations(winner, message):
    profile_photo = bot.download_profile_photo(winner.id)
    avatar = Image.open(
        BytesIO(profile_photo) if profile_photo else config.event.default_winner_avatar
    )
    winner_picture_template = config.event.winner_pictures[
        bot.daily_hash(winner.id) % len(config.event.winner_pictures)
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
    bot.send_photo_with_user_links(
        background,
        bot.phrases("play_select", bot.to_link_user(winner), daily_percentage(winner)),
    )(message)


def play(message):
    event_id = esper_event_id
    chat_id = message.chat.id
    players = get_players(chat_id)

    def _select_and_announce_next_winner():
        winner = max(players, key=daily_percentage)
        commit_win(chat_id, winner.id, event_id)
        try:
            send_congratulations(winner, message)
        except Exception as e:
            logging.exception(e)
            msg_text = bot.phrases(
                "play_select", bot.to_link_user(winner), daily_percentage(winner)
            )
            bot.reply_with_user_links(msg_text)(message)

    if len(players) == 0:
        bot.reply_to(bot.phrases("play_zero_players"))(message)
        return
    day_passed = is_day_passed(chat_id, event_id)
    if day_passed == 1 or day_passed is None:
        _select_and_announce_next_winner()
        return
    last_winner_id = get_last_winner(chat_id, event_id)
    last_winner = next(filter(lambda p: p.id == last_winner_id, players), None)
    if last_winner:
        answer = bot.phrases("play_already_selected", bot.to_link_user(last_winner))
        bot.reply_with_user_links(answer)(message)
    else:
        _select_and_announce_next_winner()


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
        bot.phrases("top_espers_header"),
    )(message)

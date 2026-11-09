from io import BytesIO
import random

from PIL import Image
from injector import inject

from vasiniyo_chat_bot.module.play.dto import Event


@inject
class ImageService:
    def __init__(self, event: Event):
        self._default_winner_avatar = (event.default_winner_avatar,)
        self._winner_pictures = event.winner_pictures

    def create_picture(self, profile_photo: bytes) -> BytesIO:
        avatar = BytesIO(profile_photo or self._default_winner_avatar.read_bytes())
        if not self._winner_pictures:
            return avatar
        settings = random.choice(self._winner_pictures)
        avatar_size = settings.avatar_size
        avatar = Image.open(avatar).resize((avatar_size, avatar_size))
        background = Image.open(settings.background)
        background.paste(
            avatar, (settings.avatar_position_x, settings.avatar_position_y)
        )
        output = BytesIO()
        background.save(output, format="PNG")
        output.seek(0)
        return output

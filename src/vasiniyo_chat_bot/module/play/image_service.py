from io import BytesIO
from pathlib import Path
import random

from PIL import Image

from vasiniyo_chat_bot.module.play.dto import Picture


class ImageService:
    def __init__(self, default_winner_avatar: Path, winner_pictures: list[Picture]):
        self._default_winner_avatar = default_winner_avatar
        self._winner_pictures = winner_pictures

    def create_picture(self, profile_photo: bytes) -> BytesIO:
        avatar = (
            BytesIO(profile_photo) if profile_photo else self._default_winner_avatar
        )
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

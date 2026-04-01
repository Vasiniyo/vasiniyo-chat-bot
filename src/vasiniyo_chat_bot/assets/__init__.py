def image(name: str):
    from importlib.resources import files

    return files("vasiniyo_chat_bot.assets.images") / name


def font(name: str):
    from importlib.resources import files

    return files("vasiniyo_chat_bot.assets.fonts") / name

def sqlite():
    from importlib.resources import files

    return files("vasiniyo_chat_bot.migration.sqlite").iterdir()

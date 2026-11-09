def sqlite_files():
    from importlib.resources import files

    return files("vasiniyo_chat_bot.database.migration.sqlite").iterdir()

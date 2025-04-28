import logging


def pretty_msg(arg):
    if hasattr(arg, "message_id"):
        return (
            f"message: [{arg.message_id}] {arg.text if arg.content_type == 'text' else arg.content_type}\n"
            f"\tchat: [{arg.chat.id}] {arg.chat.title}\n"
            f"\tfrom_user: [{arg.from_user.id}] {arg.from_user.username if arg.from_user.username is not None else ''}"
        )
    return arg


def pretty_markup(arg):
    if hasattr(arg, "keyboard"):
        handle_row = lambda l: map(lambda b: f"[{b.text}]", l)
        handle_column = map(lambda l: " ".join(handle_row(l)), arg.keyboard)
        return "buttons{ " + "\n".join(handle_column) + " }"
    return arg


def logger(func):
    def wrapper(*args, **kwargs):
        block = "=" * (30 - len(func.__name__) // 2)
        header = f"{block}|{func.__name__}|{block}"
        footer = "=" * (len(header))
        readable_args = "\n".join(
            f"[{i}]\t{pretty_msg(arg)}" for i, arg in enumerate(args)
        )
        readable_kwargs = "\n".join(
            [
                f"{{{i}}}\t{k}={pretty_markup(v)}"
                for i, (k, v) in enumerate(kwargs.items())
            ]
        )
        logging.info(f"\n{header}\n{readable_args}\n{readable_kwargs}\n{footer}")
        return func(*args, **kwargs)

    return wrapper

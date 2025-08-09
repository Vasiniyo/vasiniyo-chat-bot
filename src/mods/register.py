__all__ = ["COMMANDS", "HANDLERS", "QUERY_HANDLERS"]


COMMANDS = {}
HANDLERS = {}
QUERY_HANDLERS = {}

expand = lambda func, args: func(*args) if args else func


def reg_command(name, description, *args):
    def register(func):
        func = expand(func, args)
        COMMANDS[name] = (func, description)
        return func

    return register


def reg_handler(handler, *args):
    def register(func):
        func = expand(func, args)
        HANDLERS[func] = handler
        return func

    return register


def reg_query_handler(**kwargs):
    def register(func):
        QUERY_HANDLERS[func] = kwargs
        return func

    return register

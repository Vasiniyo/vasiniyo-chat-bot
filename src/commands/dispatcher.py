from commands.help import handle_help, handle_inline_help, handle_unknown
from commands.utils import handler, head
from config import MAIN_MENU, is_submenu_empty, phrases
import mods
import safely_bot_utils as bot

at = lambda l: lambda n: l[n] if n < len(l) else None
cmd_name = lambda m: head(split_cmd(m))
split_cmd = lambda m: head(m.text.lstrip("/").split()).split("@")
is_cmd_for_bot = lambda c: any([at(c)(1) is None, is_bot_username(c)])
is_bot_username = lambda c: at(c)(1) == bot.get_me().username

unknown_cmd = (
    lambda c: head(c) == "@"
    and is_bot_username(c)
    and head(c) not in list(COMMANDS.keys())
)

cmd_ok = lambda m: is_cmd_for_bot(split_cmd(m))
cmd_no_ok = lambda m: unknown_cmd(split_cmd(m))

menu = MAIN_MENU
menu.update({"help": (None, phrases("help_help"))})
menu.update(mods.COMMANDS)

COMMANDS = dict(filter(lambda pair: not is_submenu_empty(pair), menu.items()))
COMMANDS["help"] = (handle_help(COMMANDS), COMMANDS["help"][1])


handle_cmd = lambda m: head(COMMANDS[cmd_name(m)])(m)

handlers = {
    handle_cmd: handler(cmd_ok, commands=list(COMMANDS.keys())),
    handle_unknown: handler(cmd_no_ok),
}
handlers.update(mods.HANDLERS)

inline_handlers = {handle_inline_help(COMMANDS): {lambda query: query.query == ""}}

query_handlers = {}
query_handlers.update(mods.QUERY_HANDLERS)

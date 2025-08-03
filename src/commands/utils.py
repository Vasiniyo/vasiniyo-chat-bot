from math import e

from config import allowed_chats

head = lambda l: l[0] if l else None
chat_ok = lambda p: lambda m: p(m) and in_allowed_chat(m)
in_allowed_chat = lambda m: any(["*" in allowed_chats, str(m.chat.id) in allowed_chats])

handler = lambda func, commands=None, content_types=None: {
    "func": chat_ok(func),
    "commands": commands,
    "content_types": content_types,
}

laplace_cdf = lambda L: lambda M: lambda x: (
    0.5 * e ** ((x - M) / L) if x < M else 1.0 - 0.5 / e ** ((x - M) / L)
)

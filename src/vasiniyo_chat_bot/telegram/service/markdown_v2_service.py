class MarkdownV2Service:
    def to_bold(self, text: str) -> str:
        return f"*{self.escape(text)}*"

    def to_italic(self, text: str) -> str:
        return f"_{self.escape(text)}_"

    def to_inline(self, text: str) -> str:
        return f"`{self.escape(text)}`"

    def to_link(self, full_name: str, username: str | None) -> str:
        full_name_escaped = self.escape(full_name)
        if username:
            username_escaped = self.escape(username)
            url = f"https://t\\.me/{username_escaped}"
            return f"{full_name_escaped} \\([{username_escaped}]({url})\\)"

        return full_name_escaped

    @staticmethod
    def escape(text: str) -> str:
        if text is None:
            return ""
        special_chars = "_*[]()~`>#+-=|{}.!"
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

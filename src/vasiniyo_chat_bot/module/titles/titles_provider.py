import random

from vasiniyo_chat_bot.module.titles.dto import CustomTitles


class TitlesProvider:
    def __init__(self, custom_titles: CustomTitles):
        self._adjectives = custom_titles.adjectives
        self._nouns = custom_titles.nouns
        self._weights = custom_titles.weights

    def next_title(self):
        adj = random.choices(self._adjectives, weights=self._weights, k=1)[0]
        noun = random.choice(
            [noun for noun in self._nouns if len(adj) + 1 + len(noun) <= 16]
        )
        return f"{adj} {noun}"

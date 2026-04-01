import random

from vasiniyo_chat_bot.module.titles.dto import CustomTitles


class TitlesProvider:
    def __init__(self, custom_titles: CustomTitles):
        self.adjectives = custom_titles.adjectives
        self.nouns = custom_titles.nouns
        self.weights = custom_titles.weights

    def next_title(self):
        adj = random.choices(self.adjectives, weights=self.weights, k=1)[0]
        noun = random.choice(
            [noun for noun in self.nouns if len(adj) + 1 + len(noun) <= 16]
        )
        return f"{adj} {noun}"

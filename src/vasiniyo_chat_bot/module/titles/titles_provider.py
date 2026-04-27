import random

from vasiniyo_chat_bot.module.titles.dto import CustomTitles


class TitlesProvider:
    def __init__(self, custom_titles: CustomTitles):
        self._adjectives = custom_titles.adjectives
        self._nouns = custom_titles.nouns

    def next_title(self):
        adj_group = random.choice(self._adjectives)
        adj_base = random.choice(adj_group.base)
        match random.randint(0, 3):
            case 0:
                adj = f"{adj_base}{adj_group.male_ending}"
                noun_group = random.choice(self._nouns.male)
                noun_base = random.choice(noun_group.base)
                noun = f"{noun_base}{noun_group.singular_ending}"
            case 1:
                adj = f"{adj_base}{adj_group.female_ending}"
                noun_group = random.choice(self._nouns.female)
                noun_base = random.choice(noun_group.base)
                noun = f"{noun_base}{noun_group.singular_ending}"
            case 2:
                adj = f"{adj_base}{adj_group.neuter_ending}"
                noun_group = random.choice(self._nouns.neuter)
                noun_base = random.choice(noun_group.base)
                noun = f"{noun_base}{noun_group.singular_ending}"
            case _:
                adj = f"{adj_base}{adj_group.plural_ending}"
                match random.randint(0, 2):
                    case 0:
                        noun_group = random.choice(self._nouns.neuter)
                        noun_base = random.choice(noun_group.base)
                        noun = f"{noun_base}{noun_group.plural_ending}"
                    case 1:
                        noun_group = random.choice(self._nouns.female)
                        noun_base = random.choice(noun_group.base)
                        noun = f"{noun_base}{noun_group.plural_ending}"
                    case _:
                        noun_group = random.choice(self._nouns.female)
                        noun_base = random.choice(noun_group.base)
                        noun = f"{noun_base}{noun_group.plural_ending}"
        title = f"{adj} {noun}"
        return title if len(title) <= 16 else self.next_title()

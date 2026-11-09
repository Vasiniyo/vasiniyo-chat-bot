from injector import inject

from vasiniyo_chat_bot.config.dto import Config
from vasiniyo_chat_bot.module.titles.dto import AdjectiveGroup
from vasiniyo_chat_bot.module.titles.dto import CustomTitles
from vasiniyo_chat_bot.module.titles.dto import NounGroup
from vasiniyo_chat_bot.module.titles.dto import Nouns


@inject
class CustomTitlesReader:
    def __init__(self, config: Config) -> None:
        self._config = config

    def load(self) -> CustomTitles:
        adjectives_default = {
            "base": ["наш"],
            "male_ending": "",
            "female_ending": "а",
            "neuter_ending": "е",
            "plural_ending": "и",
        }
        male_default = {"base": "манул", "singular_ending": "", "plural_ending": "ы"}
        female_default = {"base": "кошк", "singular_ending": "а", "plural_ending": "и"}
        neuter_default = {"base": "сияни", "singular_ending": "е", "plural_ending": "я"}
        titles_section = self._config.section.get("custom-titles", {})
        adjectives = titles_section.get("adjectives", [adjectives_default])
        nouns = self._config.section.get("custom-titles", {}).get("nouns", {})
        return CustomTitles(
            adjectives=[AdjectiveGroup(**adj) for adj in adjectives],
            nouns=Nouns(
                male=[NounGroup(**n) for n in nouns.get("male", male_default)],
                female=[NounGroup(**n) for n in nouns.get("female", female_default)],
                neuter=[NounGroup(**n) for n in nouns.get("neuter", neuter_default)],
            ),
        )

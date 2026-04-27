from vasiniyo_chat_bot.module.titles.dto import (
    AdjectiveGroup,
    CustomTitles,
    NounGroup,
    Nouns,
)


class CustomTitlesReader:
    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> CustomTitles:
        adjectives = self._section.get("custom-titles", {}).get("adjectives", [])
        nouns = self._section.get("custom-titles", {}).get("nouns", {})
        return CustomTitles(
            adjectives=[AdjectiveGroup(**adj) for adj in adjectives],
            nouns=Nouns(
                male=[NounGroup(**n) for n in nouns.get("male")],
                female=[NounGroup(**n) for n in nouns.get("female")],
                neuter=[NounGroup(**n) for n in nouns.get("neuter")],
            ),
        )

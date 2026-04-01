import bisect

from vasiniyo_chat_bot.module.titles.dto import CustomTitles


class CustomTitlesReader:
    def __init__(self, section: dict[str, any]) -> None:
        self._section = section

    def load(self) -> CustomTitles:
        _adjectives = sorted(
            set(
                [
                    str(x)
                    for x in self._section.get("custom-titles", {}).get(
                        "adjectives", []
                    )
                ]
            ),
            key=len,
        )
        _nouns = list(set(self._section.get("custom-titles", {}).get("nouns", [])))
        _weights = []

        for adj in _adjectives:
            max_len = 15 - len(adj)
            count = bisect.bisect_right([len(n) for n in _nouns], max_len)
            _weights.append(count)

        return CustomTitles(adjectives=_adjectives, nouns=_nouns, weights=_weights)

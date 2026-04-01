class StickersConfigReader:
    def __init__(self, section: dict[str, any]):
        self._section = section

    def load_configuration(self) -> set[str]:
        return {
            unique_id.split(";")[0]
            for unique_id in self._section.get("unique_file_id", {}).values()
        }

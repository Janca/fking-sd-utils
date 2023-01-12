from __future__ import annotations

import jsonpickle


class FkPreferences:
    def __init__(
            self,
            image_preview_size: int = 512
    ):
        self.image_preview_size = image_preview_size

    def save(self, path: str) -> FkPreferences:
        return self


def load_preferences(path: str = None) -> FkPreferences:
    if path is None:
        return FkPreferences()

    with open(path, "r") as f:
        data = f.read()
        f.close()

        return jsonpickle.decode(data)

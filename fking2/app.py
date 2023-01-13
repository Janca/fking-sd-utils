from fking2.dataset import FkDataset
from fking2.preferences import FkPreferences

version = "0.0.2"


class FkApp:
    _working_directory: str = None
    _working_dataset: FkDataset = None
    _preferences: FkPreferences = None

    def __init__(self, preferences):
        self._preferences = preferences

    @property
    def working_dataset(self) -> FkDataset:
        return self._working_dataset

    @property
    def working_directory(self) -> str:
        return self._working_directory

    @property
    def preferences(self):
        return self._preferences

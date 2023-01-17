from typing import Union

from fking2.dataset import FkDataset
from fking2.preferences import FkPreferences

version = "0.0.2"


class FkApp:
    _working_directory: str = None
    _working_dataset: FkDataset = None
    _preferences: FkPreferences = None

    def __init__(self, preferences):
        self._preferences = preferences

    def set_working_dataset(self, dataset: Union[FkDataset, None]):
        self._working_dataset = dataset
        self._working_directory = None if dataset is None else dataset.directory_path

    @property
    def working_dataset(self) -> FkDataset:
        return self._working_dataset

    @property
    def working_directory(self) -> str:
        return self._working_directory

    @property
    def preferences(self):
        return self._preferences

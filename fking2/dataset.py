from __future__ import annotations

import os.path
from functools import cmp_to_key
from typing import Tuple, TypeAlias, TypeVar, Union

import fking2.utils as fkutils
from fking2.concepts import FkConcept, FkConceptImage

CaptionList: TypeAlias = list[str]
T = TypeVar("T")


class FkDataset:
    class IWorkingDatum:
        _modified: bool = False
        _name: str

        _tags: list[str]
        _original_tags: list[str]

        _concept: FkConcept
        _canonical_name: str

        def __init__(self, dataset: FkDataset) -> None:
            self._dataset = dataset

        def reset_tags(self):
            self._tags = self._original_tags[:]
            self._modified = False

        def apply_tags(self, tags: str | list[str]):
            if isinstance(tags, str):
                tags = tags.split(',')

            tags = fkutils.normalize_tags(tags)
            if set(tags) != set(self._tags):
                self._modified = True
            self._tags = tags

        @property
        def name(self) -> str:
            return self._name

        @property
        def canonical_name(self) -> str:
            return self._canonical_name

        @property
        def concept(self) -> FkConcept:
            return self._concept

        @property
        def modified(self) -> bool:
            return self._modified

        @property
        def tags(self) -> CaptionList:
            return self._tags[:]

        def compare(self, other: FkDataset.IWorkingDatum) -> int:
            if self == other:
                return 0

            canonical_name = self.canonical_name
            other_canonical_name = other.canonical_name

            if canonical_name == other_canonical_name:
                return 0

            self_split = canonical_name.split('.')
            other_split = other_canonical_name.split('.')

            self_split_len = len(self_split)
            other_split_len = len(other_split)

            if self_split_len < other_split_len:
                return -1
            elif self_split_len > other_split_len:
                return 1
            else:
                self_is_image = isinstance(self, FkDataset.WorkingImage)
                other_is_image = isinstance(other, FkDataset.WorkingImage)

                if self_is_image and not other_is_image:
                    return 1
                elif not self_is_image and other_is_image:
                    return -1
                else:
                    s_filename, s_ext = os.path.splitext(self.image.file_path
                                                         if isinstance(self, FkDataset.WorkingImage)
                                                         else self.concept.directory_path)

                    o_filename, o_ext = os.path.splitext(other.image.file_path
                                                         if isinstance(other, FkDataset.WorkingImage)
                                                         else other.concept.directory_path)

                    if s_ext == o_ext:
                        self_is_int, self_as_int = fkutils.is_int(s_filename)
                        other_is_int, other_as_int = fkutils.is_int(o_filename)

                        if s_filename == o_filename:
                            return 0
                        elif self_is_int and other_is_int:
                            if self_as_int == other_as_int:
                                return 0
                            elif self_as_int < other_as_int:
                                return -1
                            else:
                                return 1
                        elif s_filename < o_filename:
                            return -1
                        else:
                            return 1

                    if s_ext < o_ext:
                        return -1
                    else:
                        return 1

    class WorkingConcept(IWorkingDatum):
        def __init__(self, dataset: FkDataset, concept: FkConcept):
            self._concept = concept
            self._canonical_name = concept.canonical_name
            self._name = concept.name
            self._modified = False

            self._original_tags = concept.read_tags()
            self._tags = self._original_tags[:]

            super().__init__(dataset)

    class WorkingImage(IWorkingDatum):
        def __init__(self, dataset: FkDataset, concept: FkDataset.WorkingConcept, image: Union[FkConceptImage | str]):
            self._concept = concept.concept
            self._working_concept = concept

            str_image = image
            if isinstance(image, FkConceptImage):
                str_image = image.file_path

            basename = os.path.basename(str_image)

            self._canonical_name = f"{concept.canonical_name}.{basename}"
            self._modified = False
            self._image = image
            self._name = basename

            self._original_tags = image.read_tags()
            self._tags = self._original_tags[:]
            self._meta = {}

            super().__init__(dataset)

        @property
        def working_concept(self):
            return self._working_concept

        @property
        def image(self) -> Union[FkConceptImage | str]:
            return self._image

        def set_meta(self, key: str, v: T) -> T:
            previous_val = self.get_meta(key)
            self._meta[key] = v
            return previous_val

        def get_meta(self, key) -> T:
            return None if key not in self._meta else self._meta[key]

    _directory_path: str
    _working_set: [dict, IWorkingDatum]

    def __init__(self, root: FkConcept):
        self.root = FkDataset.WorkingConcept(self, root)
        self._working_set = build_working_set(self, self.root)
        self._directory_path = root.directory_path

    @property
    def modified(self) -> bool:
        for datum in self._working_set:
            if self._working_set[datum].modified:
                return True

        return False

    @property
    def directory_path(self):
        return self._directory_path

    def get(self, canonical_name) -> FkDataset.IWorkingDatum:
        return self._working_set[canonical_name]

    def get_tags(self, canonical_name) -> Tuple[CaptionList, CaptionList]:
        target = self.get(canonical_name)

        target_tags = target.tags
        target_tags = fkutils.find_and_replace(target_tags, [["__folder__", target.name.lower()]])

        hierarchy = self.get_concept_hierarchy(canonical_name)

        hierarchy_tags: CaptionList = []
        for concept in hierarchy:
            c_tags = fkutils.find_and_replace(concept.tags, [["__folder__", concept.name.lower()]])
            hierarchy_tags.extend(c_tags)

        hierarchy_tags.reverse()
        return fkutils.normalize_tags(target_tags), \
            fkutils.normalize_tags(hierarchy_tags)

    def apply_tags(self, canonical_name, tags: CaptionList):
        self._working_set[canonical_name].apply_tags(tags)

    def reset_tags(self, canonical_name):
        self._working_set[canonical_name].reset_tags()

    def get_concept_hierarchy(self, canonical_name) -> list[FkDataset.WorkingConcept]:
        target: FkDataset.IWorkingDatum = self.get(canonical_name)
        hierarchy: list[FkDataset.WorkingConcept] = []
        concept = target.concept

        parent = concept.parent
        while parent is not None:
            working_parent = self.get(parent.canonical_name)
            if isinstance(working_parent, FkDataset.WorkingConcept):
                hierarchy.append(working_parent)
                parent = parent.parent
            else:
                raise ValueError

        return hierarchy

    def refresh(self):
        self._working_set = build_working_set(self, self.root)

    def keys(self) -> list[str]:
        def compare(a: str, b: str) -> int:
            awi = self.get(a)
            bwi = self.get(b)
            return awi.compare(bwi)

        keys = list(self._working_set.keys())
        keys.sort(key=cmp_to_key(compare))
        return keys


def build_working_set(dataset: FkDataset, root: FkDataset.WorkingConcept) -> dict[str, FkDataset.IWorkingDatum]:
    working_set: dict[str, FkDataset.IWorkingDatum] = {root.canonical_name: root}

    for concept in root.concept.children:
        working_concept = FkDataset.WorkingConcept(dataset, concept)
        child_set = build_working_set(dataset, working_concept)
        working_set.update(child_set)

    for image in root.concept.images:
        working_set[image.canonical_name] = FkDataset.WorkingImage(dataset, root, image)

    return working_set

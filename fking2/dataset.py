from __future__ import annotations

from typing import TypeAlias

import fking2.utils as fkutils
from fking2.concepts import FkConcept, FkConceptImage

CaptionList: TypeAlias = list[str]


class FkDataset:
    class IWorkingDatum:
        _modified: bool = False

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
        def canonical_name(self) -> str:
            return self._canonical_name

        @property
        def concept(self) -> FkConcept:
            return self.concept

        @property
        def modified(self) -> bool:
            return self.modified

        @property
        def tags(self) -> CaptionList:
            return self._tags[:]

    class WorkingConcept(IWorkingDatum):
        def __init__(self, dataset: FkDataset, concept: FkConcept):
            self._concept = concept
            self._canonical_name = concept.canonical_name
            self._name = concept.name
            self._modified = False

            self._original_tags = concept.read_tags()
            self._tags = self._original_tags[:]

            super().__init__(dataset)

        @property
        def name(self):
            return self._name

    class WorkingImage(IWorkingDatum):
        def __init__(self, dataset: FkDataset, concept: FkDataset.WorkingConcept, image: FkConceptImage):
            self._concept = concept.concept
            self._working_concept = concept
            self._canonical_name = image.canonical_name
            self._modified = False

            self._original_tags = image.read_tags()
            self._tags = self._original_tags[:]

            super().__init__(dataset)

        @property
        def working_concept(self):
            return self._working_concept

    def __init__(self, root: FkConcept):
        self.root = FkDataset.WorkingConcept(self, root)
        self._working_set = build_working_set(self.root)

    @property
    def modified(self) -> bool:
        for datum in self._working_set:
            if self._working_set[datum].modified:
                return True

        return False

    def get(self, canonical_name) -> FkDataset.IWorkingDatum:
        return self._working_set[canonical_name]

    def get_tags(self, canonical_name) -> tuple[CaptionList, CaptionList]:
        target_tags = self.get(canonical_name).tags
        hierarchy = self.get_concept_hierarchy(canonical_name)

        hierarchy_tags: CaptionList = []
        for concept in hierarchy:
            hierarchy_tags.extend(concept.tags)

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


def build_working_set(root: FkDataset.WorkingConcept) -> dict[str, FkDataset.IWorkingDatum]:
    working_set: dict[str, FkDataset.IWorkingDatum] = {root.canonical_name: root}

    for concept in root.concept.children:
        working_concept = FkDataset.WorkingConcept(concept)
        child_set = build_working_set(working_concept)
        working_set.update(child_set)

    for image in root.concept.images:
        working_set[image.canonical_name] = FkDataset.WorkingImage(root, image)

    return working_set

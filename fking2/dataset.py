from __future__ import annotations

import fking2.utils as fkutils
from fking2.concepts import FkConcept, FkConceptImage


class FkDataset:
    class WorkingConcept:
        def __init__(self, concept: FkConcept):
            self.concept = concept
            self.canonical_name = concept.canonical_name
            self.name = concept.name
            self.modified = False

            self._original_tags = concept.read_tags()
            self.tags = self._original_tags[:]

        def reset_tags(self):
            self.tags = self._original_tags[:]
            self.modified = False

        def apply_tags(self, tags: str | list[str]):
            if isinstance(tags, str):
                tags = tags.split(',')

            tags = fkutils.normalize_tags(tags)
            if set(tags) != set(self.tags):
                self.modified = True
            self.tags = tags

    class WorkingImage:
        def __init__(self, concept: FkDataset.WorkingConcept, image: FkConceptImage):
            self.concept = concept
            self.canonical_name = image.canonical_name
            self.modified = False

            self._original_tags = image.read_tags()
            self.tags = self._original_tags[:]

        def reset_tags(self):
            self.tags = self._original_tags[:]

    def __init__(self, root: FkConcept):
        self.root = FkDataset.WorkingConcept(root)
        self._working_set = build_working_set(self.root)

    def get(self, canonical_name) -> FkDataset.WorkingConcept | FkDataset.WorkingImage:
        return self._working_set[canonical_name]


def build_working_set(root: FkDataset.WorkingConcept) -> dict[str, FkDataset.WorkingConcept | FkDataset.WorkingImage]:
    working_set: dict[str, FkDataset.WorkingConcept | FkDataset.WorkingImage] = {root.canonical_name: root}

    for concept in root.concept.children:
        working_concept = FkDataset.WorkingConcept(concept)
        child_set = build_working_set(working_concept)
        working_set.update(child_set)

    for image in root.concept.images:
        working_set[image.canonical_name] = FkDataset.WorkingImage(root, image)

    return working_set

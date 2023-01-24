from __future__ import annotations

import os
from typing import List, Optional, Union, Callable

import fking2.utils as fkutils
from fking2.utils import IFkCanonical


class FkConcept(IFkCanonical):
    directory_path: str

    def __init__(self, parent: Union[FkConcept, None], directory_path: str):
        self.parent = parent
        self.children: List[FkConcept] = []
        self.images: List[FkConceptImage] = []

        self.directory_path = os.path.normcase(os.path.normpath(directory_path))
        self.tags_file_path = os.path.join(directory_path, "__prompt.txt")
        self.special_tags_file_path = os.path.join(directory_path, "__special.json")

        self.directory_name = os.path.basename(directory_path)
        self.name = self.directory_name.replace('_', ' ').title()

        self._canonical_name = get_canonical_name(self)

    def add_child(self, child: FkConcept):
        self.children.append(child)

    def add_image(self, image: FkConceptImage):
        self.images.append(image)

    def read_tags(self) -> List[str]:
        return fkutils.read_tags(self.tags_file_path)

    def read_special_tags(self):
        pass  # TODO


class FkVirtualConcept(FkConcept):
    _name: str

    def __init__(self, parent: Union[FkConcept, None], name: str, tags: List[str]):
        self._tags = tags
        self._name = name

        directory_name = name.replace(' ', '_').lower()

        directory_path: str
        if parent is None:
            directory_path = directory_name
        else:
            directory_path = os.path.join(parent.directory_path, directory_name)

        super().__init__(parent, directory_path)

    def read_tags(self) -> List[str]:
        return self._tags[:]

    def copy_to(
            self,
            dst: FkConcept,
            filter_fn: Callable[[Union[FkConcept, FkConceptImage]], bool] = None
    ):
        copy(self, dst, filter_fn)


class FkConceptImage(IFkCanonical):
    file_path: str
    filename: str

    def __init__(self, concept: FkConcept, file_path: str):
        self.concept = concept

        self.file_path = os.path.abspath(file_path)
        self.filename = os.path.basename(file_path)

        self.text_filename = f"{os.path.splitext(self.filename)[0]}.txt"

        directory = os.path.dirname(self.file_path)
        self.text_file_path = os.path.join(directory, self.text_filename)

        self._canonical_name = get_canonical_name(self)

    def read_tags(self) -> list[str]:
        return fkutils.read_tags(self.text_file_path)


def build_concept_tree(src: str, parent: Optional[FkConcept] = None) -> FkConcept:
    concept = FkConcept(parent, src)

    files = os.listdir(src)
    for filename in files:
        file_path = os.path.join(src, filename)
        if os.path.isdir(file_path):
            child = build_concept_tree(file_path, concept)
            concept.add_child(child)

        if os.path.isfile(file_path) and fkutils.is_image(file_path):
            image = FkConceptImage(concept, file_path)
            concept.add_image(image)

    return concept


def get_canonical_name(fk: Union[FkConcept, FkConceptImage]) -> str:
    canonical_name: str = fk.filename if isinstance(fk, FkConceptImage) else fk.directory_name

    fkp = fk.concept if isinstance(fk, FkConceptImage) else fk.parent
    while fkp is not None:
        canonical_name = f"{fkp.directory_name}.{canonical_name}"
        fkp = fkp.parent

    return canonical_name


def get_concept_hierarchy(
        fk: Union[FkConcept, FkConceptImage],
        depth: int = None
) -> List[Union[FkConcept, FkConceptImage]]:
    concept = fk if isinstance(fk, FkConcept) else fk.concept
    hierarchy: List[FkConcept | FkConceptImage] = [concept]

    parent = concept.parent
    while parent is not None:
        hierarchy.append(parent)
        parent = parent.parent

    hierarchy.reverse()

    if depth is None or depth == 0:
        return hierarchy
    elif depth < 0:
        return hierarchy[:depth or None]
    else:
        return hierarchy[depth:]


# noinspection PyProtectedMember
def copy(
        src: Union[FkConcept, FkConceptImage],
        destination: FkConcept,
        filter_fn: Callable[[Union[FkConcept, FkConceptImage]], bool] = None
):
    if isinstance(src, FkConceptImage):
        dst_image = FkConceptImage(destination, src.file_path)
        if filter_fn is None or filter_fn(dst_image):
            destination.add_image(dst_image)
        return

    if isinstance(src, FkVirtualConcept):
        dst_concept = FkVirtualConcept(destination, src._name, src._tags)
    else:
        dst_concept = FkConcept(destination, src.directory_path)

    if filter_fn is None or filter_fn(dst_concept):
        destination.add_child(dst_concept)

    for image in src.images:
        copy(image, dst_concept)

    for concept in src.children:
        copy(concept, dst_concept)

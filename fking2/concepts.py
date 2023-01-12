from __future__ import annotations

import os

import fking2.utils as fkutils


class FkConcept:
    def __init__(self, parent: FkConcept | None, directory_path: str):
        self.parent = parent
        self.children: list[FkConcept] = []
        self.images: list[FkConceptImage] = []

        self.directory_path = directory_path
        self.tags_file_path = os.path.join(directory_path, "__prompt.txt")
        self.special_tags_file_path = os.path.join(directory_path, "__special.json")

        self.directory_name = os.path.basename(directory_path)
        self.name = self.directory_name.replace('_', ' ').title()

        self.canonical_name = get_canonical_name(self)

    def add_child(self, child: FkConcept):
        self.children.append(child)

    def add_image(self, image: FkConceptImage):
        self.add_image(image)

    def read_tags(self) -> list[str]:
        return fkutils.read_tags(self.tags_file_path)

    def read_special_tags(self):
        pass  # TODO


class FkConceptImage:
    def __init__(self, concept: FkConcept, file_path: str):
        self.concept = concept

        self.file_path = file_path
        self.filename = os.path.basename(file_path)

        self.text_file_path = os.path.join(self.concept.directory_path, f"{os.path.splitext(self.filename)[0]}.txt")
        self.text_filename = os.path.basename(self.text_file_path)

        self.canonical_name = get_canonical_name(self)

    def read_tags(self) -> list[str]:
        return fkutils.read_tags(self.text_file_path)


def get_canonical_name(fk: FkConcept | FkConceptImage) -> str:
    canonical_name: str = fk.filename if fk is FkConceptImage else fk.directory_name

    fkp = fk.concept if fk is FkConceptImage else fk.parent
    while fkp is not None:
        canonical_name = f"{fkp.directory_name}.{canonical_name}"
        fkp = fkp.parent

    return canonical_name

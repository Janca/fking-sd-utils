import math
import os
import shutil
from tkinter import messagebox

from PIL import Image

from fking.fking_captions import Concept, ConceptImage
from fking.fking_utils import normalize_tags, write_tags


def load_concept_images(images: list[ConceptImage]) -> list[Image]:
    return [load_concept_image(image) for image in images]


def load_concept_image(image: ConceptImage) -> Image:
    return load_image(image.get_canonical_name())


def load_image(
        canonical: str,
        image_cache: dict[str, Image],
        concept_image: dict[str, ConceptImage],
        size: int = 512
) -> Image:
    if canonical in image_cache:
        print(f"Found image '{canonical}' in image cache.")
        return image_cache[canonical]

    print(f"Loading image '{canonical}' from disk")
    target_image = concept_image[canonical]
    target_image_path = target_image.path

    image = Image.open(target_image_path).resize((size, size), Image.Resampling.LANCZOS)
    image_cache[canonical] = image

    return image


def create_image_grid(images: list[Image]):
    rows = math.sqrt(len(images))
    rows = round(rows)

    cols = math.ceil(len(images) / rows)

    w, h = images[0].size
    grid = Image.new('RGB', size=(cols * w, rows * h), color='black')

    for i, img in enumerate(images):
        grid.paste(img, box=(i % cols * w, i // cols * h))

    return grid


def flatten_dataset(
        dst: str,
        concepts: dict[str, Concept],
        concept_images: dict[str, Image],
        current_dataset_tags: dict[str, list[str]]
):
    unique_prompts: list[str] = []
    unique_tags: list[str] = []

    dataset_dst = os.path.join(dst, "dataset")
    if os.path.exists(dataset_dst):
        confirmation = messagebox.askyesno(title="Confirmation",
                                           message="Are you sure you want to overwrite this directory?")

        if confirmation:
            shutil.rmtree(dataset_dst)

    os.makedirs(dataset_dst, exist_ok=True)

    for c_img in concept_images:
        concept_image = concept_images[c_img]

        tags, c_tags = get_image_tags(c_img, concepts, concept_images, current_dataset_tags)
        special_tags = concept_image.concept.special_tags
        tags = normalize_tags(c_tags + tags)

        filename = concept_image.get_filename(0)
        extension = concept_image.get_filename(1)

        img_path = concept_image.path
        tags_file_path = os.path.join(dataset_dst, f"{filename}.txt")

        shutil.copyfile(img_path, os.path.join(dataset_dst, f"{filename}{extension}"))
        str_tags, tags = write_tags(tags_file_path, tags, special_tags)

        if str_tags not in unique_prompts:
            unique_prompts.append(str_tags)

        for t in tags:
            if t not in unique_tags:
                unique_tags.append(t)

    unique_prompts_path = os.path.join(dst, "unique_concept_prompts.txt")
    with open(unique_prompts_path, "w+") as f:
        for str_tags in normalize_tags(unique_prompts):
            f.write(f"{str_tags}\r\n")
        f.close()

    unique_tags_path = os.path.join(dst, "unique_concept_tags.txt")
    write_tags(unique_tags_path, unique_tags)


def get_image_tags(
        canonical_img: str,
        concepts: dict[str, Concept],
        concept_images: dict[str, Image],
        current_dataset_tags: dict[str, list[str]]
) -> tuple[list[str], list[str]]:
    c_img = concept_images[canonical_img]
    img_concept: Concept = c_img.concept

    concept_tags, concept_parent_tags = get_concept_tags(img_concept.canonical_name, concepts, current_dataset_tags)
    c_tags = concept_parent_tags + concept_tags

    tags = c_img.tags if canonical_img not in current_dataset_tags else current_dataset_tags[canonical_img]
    return normalize_tags(tags), normalize_tags(c_tags)


def get_concept_tags(
        canonical_concept: str,
        concepts: dict[str, Concept],
        current_dataset_tags: dict[str, list[str]]
) -> tuple[list[str], list[str]]:
    target_concept = concepts[canonical_concept]

    parent_tags: (list[str], list[str]) = get_concept_tags(
            target_concept.parent.canonical_name,
            concepts,
            current_dataset_tags
    ) if target_concept.parent is not None else ([], [])

    return normalize_tags(
            target_concept.concept_tags
            if canonical_concept not in current_dataset_tags
            else current_dataset_tags[canonical_concept]
    ), normalize_tags(parent_tags[1] + parent_tags[0])

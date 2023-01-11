import math
import os
import shutil

from PIL import Image

from fking.fking_captions import CaptionedImage, Concept, ConceptImage
from fking.fking_utils import normalize_tags, write_tags


def load_image(concept_image: ConceptImage, image_cache: dict[str, Image], max_size: int) -> Image:
    c_img_name = concept_image.get_canonical_name()
    if c_img_name in image_cache:
        return image_cache[c_img_name]

    c_img = Image.open(concept_image.path).resize(size=(max_size, max_size), resample=Image.Resampling.LANCZOS)
    image_cache[c_img_name] = c_img

    return c_img


def load_concept_image(concept: Concept, image_cache: dict[str, Image], max_images: int, max_size: int) -> Image:
    c_name = concept.canonical_name
    if c_name in image_cache:
        return image_cache[c_name]

    concepts, concept_images = get_concept_child_hierarchy(concept)
    concepts = [c for c in concepts if len(c.images) > 0]

    image_per_concept = max(round(max_images / len(concepts)), 1)
    selected_images = []

    try:
        for c in concepts:
            c_img_len = len(c.images)
            for i in range(min(image_per_concept, c_img_len)):
                c_img = c.images[i]
                c_img_canonical = c_img.get_canonical_name()

                if c_img_canonical in image_cache:
                    selected_images.append(image_cache[c_img_canonical])
                else:
                    loaded_image = load_image(c_img, image_cache, max_size)
                    selected_images.append(loaded_image)

                if len(selected_images) >= max_images:
                    raise StopIteration
    except StopIteration:
        pass

    concept_grid = create_image_grid(selected_images, max_size)
    image_cache[c_name] = concept_grid

    return concept_grid


def create_image_grid(images: list[Image], target_size: int = 512):
    rows = math.sqrt(len(images))
    rows = round(rows)

    cols = math.ceil(len(images) / rows)

    w, h = images[0].size
    grid = Image.new('RGB', size=(cols * w, rows * h), color='black')

    for i, img in enumerate(images):
        grid.paste(img, box=(i % cols * w, i // cols * h))

    w, h = grid.size
    ratio = float(h) / float(w)

    if w > h:
        w = target_size
        h = int(target_size * ratio)
    elif w < h:
        h = target_size
        w = int(target_size * ratio)
    else:
        w = h = target_size

    if w != 512 or h != 512:
        max_size = max(grid.size)
        black_bg = Image.new("RGB", size=(max_size, max_size), color='black')
        black_bg.paste(grid)

        return black_bg.resize((target_size, target_size))

    return grid.resize((w, h))


def flatten_dataset(
        dst: str,
        dataset_dst: str,
        concepts: dict[str, Concept],
        concept_images: dict[str, Image],
        current_dataset_tags: dict[str, list[str]]
):
    unique_prompts: list[str] = []
    unique_tags: list[str] = []

    os.makedirs(dataset_dst, exist_ok=True)

    captioned_images = []
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

        captioned_image = CaptionedImage(concept_image.concept, img_path, tags)
        captioned_images.append(captioned_image)

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

    return captioned_images


def save_dataset(
        concepts: [dict, Concept],
        concept_images: [dict, ConceptImage],
        current_dataset_tags: dict[str, list[str]]
) -> int:
    touched = 0
    for modified in current_dataset_tags:
        if modified in concept_images:
            concept_image = concept_images[modified]
            parent_concept = concept_image.concept
            special_tags = parent_concept.special_tags

            m_tags = current_dataset_tags[modified]
            if len(m_tags) > 0:
                touched += 1
                img_dir = parent_concept.working_directory
                tags_txt_file = os.path.join(img_dir, f"{concept_image.get_filename(0)}.txt")
                write_tags(tags_txt_file, m_tags, special_tags)

        elif modified in concepts:
            concept = concepts[modified]
            c_name = concept.name.replace("_", " ")

            m_tags = current_dataset_tags[modified]
            r_tags = concept.raw_tags

            if "__folder__" in r_tags:
                for mt_idx in range(len(m_tags)):
                    mt = m_tags[mt_idx]
                    if mt == c_name:
                        m_tags[mt_idx] = "__folder__"
                        break

            if len(m_tags) > 0:
                touched += 1
                w_dir = concept.working_directory
                tags_txt_file = os.path.join(w_dir, "__prompt.txt")
                write_tags(tags_txt_file, m_tags)

    return touched


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


def get_concept_child_hierarchy(
        concept: Concept,
        include_self: bool = True
) -> tuple[list[Concept], list[ConceptImage]]:
    concepts: list[Concept] = [concept] if include_self else []
    concept_images: list[ConceptImage] = [concept.images] if include_self else []

    for child in concept.children:
        concepts.append(child)
        concept_images.extend(child.images)

        child_concepts, child_concept_images = get_concept_child_hierarchy(child, False)

        concepts.extend(child_concepts)
        concept_images.extend(child_concept_images)

    return concepts, concept_images

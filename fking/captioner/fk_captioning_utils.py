import math

from PIL import Image

from fking.fking_captions import ConceptImage


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

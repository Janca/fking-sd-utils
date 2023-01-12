import os


def normalize_tags(tags: list[str]) -> list[str]:
    unique_tags: list[str] = []
    for tag in tags:
        trimmed = tag.strip()
        if len(trimmed) <= 0 or trimmed in unique_tags:
            continue
        unique_tags.append(trimmed)
    return unique_tags


def read_tags(src: str) -> list[str]:
    if not os.path.exists(src):
        return []

    lines: list[str]
    with open(src) as f:
        lines = f.readlines()
        f.close()

    tags: list[str] = []
    for line in lines:
        tags.extend(line.split(','))

    return normalize_tags(tags)


def is_image(path: str) -> bool:
    if not os.path.isfile(path):
        return False

    ext = os.path.splitext(path)[1]
    return ext in [".png", ".jpg", ".jpeg"]

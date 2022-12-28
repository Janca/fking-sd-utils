import hashlib
import os
import pathlib


def read_tags_from_file(path: str) -> list[str]:
    if not os.path.exists(path):
        return []

    with open(path) as f:
        tags = []

        lines = f.readlines()
        for line in lines:
            tags.extend(line.split(','))

        f.close()

    return normalize_tags(tags)


def sha256_file_hash(path: str) -> str:
    file_bytes = pathlib.Path(path).read_bytes()
    return hashlib.sha256(file_bytes).hexdigest()


def normalize_tags(tags: list[str]) -> list[str]:
    u_tags = []

    for t in tags:
        stripped = t.strip()
        if len(stripped) <= 0:
            continue

        if stripped not in u_tags:
            u_tags.append(stripped)

    return u_tags


def write_tags(dst: str, tags: list[str]):
    with open(dst, 'w+') as f:
        tags = normalize_tags(tags)
        line = ", ".join(tags)

        print(f"Saving '{line}' to '{dst}'.")

        f.write(line)
        f.close()

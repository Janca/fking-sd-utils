import hashlib
import json
import os
import pathlib

from enum import Enum


class SpecialTagMergeMode(Enum):
    MERGE = 1
    REPLACE = 2
    KEEP_EXISTING = 3


__img_extensions = [".png", ".jpeg", ".jpg"]


def read_tags_from_file(path: str) -> list[str]:
    if not os.path.exists(path):
        return []

    with open(path) as f:
        tags = []

        lines = f.readlines()
        f.close()

    for line in lines:
        tags.extend(line.split(','))

    if len(tags) <= 0:
        print(f"\nWARNING: Prompt file at '{path}' is empty.\n")

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


def write_tags(
        dst: str,
        tags: list[str],
        special_tags: dict[str, tuple[SpecialTagMergeMode, list[str]]] = {}
) -> tuple[str, list[str]]:
    with open(dst, 'w+') as f:
        t_tags = find_and_replace_special_tags(tags, special_tags)
        line = ", ".join(t_tags)

        # print(f"Saving '{line}' to '{dst}'.")

        f.write(line)
        f.close()

        return line, t_tags


def read_special_tags_from_file(path: str) -> dict[str, tuple[SpecialTagMergeMode, list[str]]]:
    if not os.path.exists(path):
        return {}

    special_tags: dict[str, tuple[SpecialTagMergeMode, list[str]]] = {}

    with open(path) as f:
        special_tags_data = json.load(f)
        f.close()

    for special_tag in special_tags_data:
        special = special_tag['special_tag']
        tags = special_tag['tags'].split(',')
        mode = SpecialTagMergeMode.MERGE if 'merge_mode' not in special_tag else special_tag['merge_mode']

        s_tag = mode, normalize_tags(tags)
        special_tags[special] = s_tag

    return special_tags


def merge_special_tags(
        src: dict[str, tuple[SpecialTagMergeMode, list[str]]],
        dst: dict[str, tuple[SpecialTagMergeMode, list[str]]]
) -> dict[str, tuple[SpecialTagMergeMode, list[str]]]:
    merged: dict[str, tuple[SpecialTagMergeMode, list[str]]] = dst

    if len(dst) <= 0:
        return src

    for src_special in src:
        src_mode, src_tags = src[src_special]

        if src_special in merged:
            dst_mode, dst_tags = merged[src_special]

            if dst_mode is SpecialTagMergeMode.MERGE:
                tags = normalize_tags(src_tags + dst_tags)
                merged[src_special] = (dst_mode, tags)

            elif dst_mode is SpecialTagMergeMode.REPLACE:
                merged[src_special] = (dst_mode, src_tags)

            elif dst_mode is SpecialTagMergeMode.KEEP_EXISTING:
                pass

    return merged


def find_and_replace_special_tags(
        tags: list[str],
        special_tags: dict[str, tuple[SpecialTagMergeMode, list[str]]]
) -> list[str]:
    if len(special_tags) <= 0:
        return normalize_tags(tags)

    replaced_tags = []
    for t in tags:
        if t in special_tags:
            replaced_tags.extend(special_tags[t][1])
        else:
            replaced_tags.append(t)

    return normalize_tags(replaced_tags)


def fix_prompt_text_files(target: str):
    for root, dirs, files in os.walk(target):
        for child_dir in dirs:
            child_dir_path = os.path.join(root, child_dir)
            fix_prompt_text_files(child_dir_path)

        for file in files:
            if not file.startswith("__special") and file.endswith(".txt"):
                tag_file_path = os.path.join(root, file)
                tags = read_tags_from_file(tag_file_path)
                write_tags(tag_file_path, tags)


def generate_tag_list(src: str) -> list[str]:
    unique_tags = []

    for filename in os.listdir(src):
        if filename.endswith(".txt"):
            file_path = os.path.join(src, filename)
            tags = read_tags_from_file(file_path)
            unique_tags.extend(tags)

    return normalize_tags(unique_tags)


def generate_prompt_list(src: str) -> list[str]:
    unique_prompts = []

    for filename in os.listdir(src):
        if filename.endswith(".txt"):
            file_path = os.path.join(src, filename)

            tags = read_tags_from_file(file_path)
            prompt = ", ".join(tags).strip()

            if prompt not in unique_prompts:
                unique_prompts.append(prompt)

    return unique_prompts


def prompt_warning(warning: str) -> bool:
    print()
    sanity_check = input(f"{warning} [y/N] ")
    return sanity_check and sanity_check.lower() == "y"


def is_image(filename: str) -> bool:
    ext = os.path.splitext(filename)[1]
    return ext in __img_extensions

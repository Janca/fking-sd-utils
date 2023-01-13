import os
import sys

import tkinter as tk

from PIL import Image, ImageTk


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


def load_ico(relative_path: str):
    target_image = relative_path
    if not hasattr(sys, "frozen"):
        target_image = os.path.join(os.path.dirname(__file__), os.path.normpath(f"ui/{target_image}"))
    else:
        target_image = os.path.join(sys.prefix, target_image)
    return target_image


def get_ico(icon: str):
    ico = load_ico(icon)
    return tk.PhotoImage(file=ico)

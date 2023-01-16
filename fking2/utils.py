import os
import sys
import tkinter as tk
from typing import Callable, List, Optional, Tuple, TypeVar

from PIL import Image

T = TypeVar("T")


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


def write_tags(dst: str, tags: list[str]):
    with open(dst, "w+") as f:
        f.write(", ".join(tags))
        f.close()


def find_and_replace(tags: List[str], replacements: List[List[str]]) -> List[str]:
    r_tags: List[str] = []
    for t in tags:
        replaced = False

        for s, r in replacements:
            if s in t:
                replaced = True
                r_tags.append(t.replace(s, r))

        if not replaced:
            r_tags.append(t)

    return normalize_tags(r_tags)


def is_image(path: str) -> bool:
    if not os.path.isfile(path):
        return False

    ext = os.path.splitext(path)[1]
    return ext in [".png", ".jpg", ".jpeg"]


def find_image_resource(relative_path: str):
    target_image = relative_path
    if not hasattr(sys, "frozen"):
        target_image = os.path.join(os.path.dirname(__file__), os.path.normpath(f"ui/{target_image}"))
    else:
        target_image = os.path.join(sys.prefix, target_image)
    return target_image


def get_photo_image_resource(icon: str):
    ico = find_image_resource(icon)
    return tk.PhotoImage(file=ico)


def get_image_resource(icon: str):
    ico = find_image_resource(icon)
    return Image.open(ico)


def border_widget(
        root,
        fk: Callable[[tk.Frame], T],
        color: str = "#a0a0a0",
        thickness: int = 1,
        focus_color: str = "#0078d4"
) -> Tuple[tk.Frame, T]:
    f = tk.Frame(root, background=color, borderwidth=thickness)

    widget = fk(f)
    w_keys = widget.keys()
    widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    if "relief" in w_keys:
        widget.configure(relief=tk.FLAT)

    def on_focus(e):
        if "state" in w_keys and widget.cget("state") == tk.NORMAL:
            f.configure(background=focus_color)

    widget.bind("<FocusIn>", on_focus)
    widget.bind("<FocusOut>", lambda e: f.configure(background=color))

    return f, widget


def is_int(x: any) -> Tuple[bool, Optional[int]]:
    try:
        i = int(x)
        return True, i
    except ValueError:
        return False, None

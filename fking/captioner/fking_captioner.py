import os
import shutil
import sys
import tkinter as tk
from functools import cmp_to_key
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from fking.captioner.fk_captioning_utils import flatten_dataset, get_concept_tags, get_image_tags, load_concept_image, \
    load_image, save_dataset
from fking.fking_captions import Concept, ConceptImage, create_concept
from fking.fking_utils import is_image, normalize_tags

root = tk.Tk()

ico_img = "icon.ico"
if not hasattr(sys, "frozen"):
    ico_img = os.path.join(os.path.dirname(__file__), ico_img)
else:
    ico_img = os.path.join(sys.prefix, ico_img)

root.iconbitmap(ico_img)

root.resizable(False, False)
root.option_add('*tearOff', False)

working_directory: str | None = None
working_concept: Concept | None = None

concepts: dict[str, Concept] = {}
concept_images: dict[str, ConceptImage] = {}
sorted_concept_images: dict[str, ConceptImage] = {}
image_cache: dict[str, Image] = {}

current_dataset_tags: dict[str, list[str]] = {}

last_modified_tags: list[str] = []

image_preview_size = 604
transparent_img = ImageTk.PhotoImage(Image.new("RGBA", (image_preview_size, image_preview_size), (0, 0, 0, 0)))
active_img: None | ImageTk.PhotoImage = transparent_img

max_load_concept_images = 100  # 10x10 image grid
active_concept_image: ConceptImage | None = None

active_parent_tags: list[str] = []
active_img_tags: list[str] = []

active_title_fragment = None


def on_menu_item_open(event=None):
    global working_concept, working_directory

    src = filedialog.askdirectory()
    if src is None or len(src) <= 0:
        return

    __load_concept_tree(src)


def on_menu_item_flatten(event=None):
    if working_concept is None:
        return

    if __is_modified():
        if messagebox.askyesno(title="Save Dataset",
                               message="Would you like to save the dataset before flattening?"
                                       "\nThis action is not required, and is irreversible."):
            __save_dataset()

    dst_directory = filedialog.askdirectory()
    if dst_directory is None or len(dst_directory) <= 0:
        return

    dataset_directory = os.path.join(dst_directory, "dataset")
    if os.path.isdir(dataset_directory):
        if messagebox.askyesno(title="Overwrite Confirmation",
                               message="Are you sure you want to overwrite existing directory contents?"
                                       "\nThis action is irreversible."):
            shutil.rmtree(dataset_directory)

        else:
            messagebox.showinfo(title="Flattening Cancelled",
                                message="Cancelled flattening operation, no changes were written to disk.")

            return

    flattened_images = flatten_dataset(dst_directory, dataset_directory, concepts, concept_images, current_dataset_tags)
    flattened_images_len = len(flattened_images)
    del flattened_images

    messagebox.showinfo(
            title="Flatten Dataset Complete",
            message=f"Flattened {flattened_images_len:,} images.")


def on_menu_item_save(event=None):
    if working_concept is None:
        return

    if not messagebox.askyesno(
            title="Confirm Save",
            message="Saving will write changes to your dataset, are you sure you want to continue?"
                    "\nThis action is irreversible."
    ):
        return
    else:
        __save_dataset()


def on_tree_view_child_click(event):
    global label_image_preview, active_img

    treeview_selection = treeview_concept.selection()
    tree_sel = treeview_selection[0]

    tree_sel_extension = os.path.splitext(tree_sel)[1]
    if tree_sel_extension in [".png", ".jpg", ".jpeg"]:
        __set_active_image(tree_sel)

    elif tree_sel in concepts:
        __set_active_concept(tree_sel)


def on_apply_button(event):
    global last_modified_tags

    tree_selection = treeview_concept.selection()
    if len(tree_selection) <= 0:
        return

    tree_sel = tree_selection[0]
    tags = __tags_from_text_field()

    current_dataset_tags[tree_sel] = tags
    last_modified_tags = tags

    __set_title(active_title_fragment)


def on_next_button(event):
    def get_canonical_index(canonical_str, search: dict) -> int:
        keys = search.keys()
        index = -1

        for k in keys:
            index = index + 1
            if k == canonical_str:
                return index

        return index

    def get_canonical_from_index(index: int, search: dict) -> str:
        keys = list(search.keys())
        return keys[index]

    on_apply_button(event)

    tree_sel = treeview_concept.selection()
    if len(tree_sel) <= 0:
        return

    tree_sel = tree_sel[0]
    can_idx = get_canonical_index(tree_sel, sorted_concept_images)
    if can_idx <= -1:
        return

    next_idx = can_idx + 1

    if next_idx < len(sorted_concept_images):
        next_id = get_canonical_from_index(next_idx, sorted_concept_images)
        if next_id is not None:
            __open_tree_item(next_id)

    text_image_tags_field.focus_force()


def on_paste_button(event=None):
    if last_modified_tags is not None and len(last_modified_tags) > 0:
        __set_tags_text(last_modified_tags, active_parent_tags)


def on_request_exit(event=None):
    nl = '\n'
    if working_concept is None or messagebox.askyesno(
            title="Confirm Exit",
            message=f"Are you sure you want to exit? "
                    f"{f'{nl}You have unsaved changes.' if __is_modified() else ''}".strip()
    ):
        root.destroy()


def __is_modified() -> bool:
    for key in current_dataset_tags.keys():
        value = current_dataset_tags[key]
        if value is not None and len(value) > 0:
            return True

    return False


def __set_active_image(canonical_img: str):
    global active_img, active_img_tags, active_concept_image, active_parent_tags

    if canonical_img is None:
        del active_img
        del active_img_tags
        del active_concept_image
        del active_parent_tags
        return

    active_concept_image = concept_images[canonical_img]
    image_concept = active_concept_image.concept
    concept_raw_tags = image_concept.raw_tags

    print(f"Selected raw tags: {concept_raw_tags}")

    active_img_tags, active_parent_tags = get_image_tags(canonical_img, concepts, concept_images, current_dataset_tags)
    __set_tags_text(active_img_tags, active_parent_tags)

    image = load_image(active_concept_image, image_cache, image_preview_size)
    img_tk = ImageTk.PhotoImage(image)
    active_img = img_tk

    label_image_preview['image'] = active_img
    __set_title(f"'{os.path.relpath(active_concept_image.path, working_directory)}'")


def __set_active_concept(canonical_concept: str):
    global active_img_tags, active_parent_tags, active_img, active_concept_image

    active_img_tags = None
    active_concept_image = None

    target_concept = concepts[canonical_concept]
    concept_grid = load_concept_image(target_concept, image_cache, max_load_concept_images, image_preview_size)

    active_img = ImageTk.PhotoImage(concept_grid)
    label_image_preview["image"] = active_img

    active_img_tags, active_parent_tags = get_concept_tags(canonical_concept, concepts, current_dataset_tags)

    __set_tags_text(active_img_tags, active_parent_tags)
    path = os.path.relpath(target_concept.working_directory, working_directory)
    if path == ".":
        __set_title()
    else:
        __set_title(f"'{path}'")


def __set_title(title: str | None = None):
    global active_title_fragment
    if not title:
        __set_title("a fking hierarchical dataset editor")
    else:
        active_title_fragment = title
        modified_star = "*" if __is_modified() else ""
        root.title(f"{modified_star}fking captioner - {title}")


def __load_concept_tree(src_dir: str) -> Concept:
    global working_concept, working_directory

    working_directory = src_dir

    if working_directory is not None and len(working_directory) > 0:
        working_concept = create_concept("global", working_directory)
        __build_tree(working_concept)
    else:
        working_concept = None
        __clear_tree()

    return working_concept


def __open_tree_item(iid: str):
    treeview_concept.selection_clear()
    treeview_concept.selection_set(iid)
    treeview_concept.focus(iid)

    concept = sorted_concept_images[iid].concept if iid in sorted_concept_images else concepts[iid]

    # event listener is firing this
    # set_active_image(iid)

    while concept is not None:
        concept_iid = concept.canonical_name
        treeview_concept.item(concept_iid, open=True)
        concept = concept.parent


def __clear_tree():
    concepts.clear()
    concept_images.clear()
    current_dataset_tags.clear()
    sorted_concept_images.clear()
    image_cache.clear()
    last_modified_tags.clear()

    menu_file.entryconfig("Flatten Dataset", state=tk.DISABLED)
    menu_file.entryconfig("Save Dataset", state=tk.DISABLED)

    treeview_concept.delete(*treeview_concept.get_children())


def __build_tree(concept: Concept):
    __clear_tree()

    def build(c: Concept, p: Concept = None):
        concepts[c.canonical_name] = c

        tree_inserts: dict[str, tuple] = {c.canonical_name: (
            '' if p is None else p.canonical_name,
            tk.END,
            c.canonical_name,
            c.name.replace('_', ' ').title()
        )}

        for ch in c.children:
            children = build(ch, c)
            tree_inserts.update(children[1])

        for img in c.images:
            i_cname = img.get_canonical_name()
            concept_images[i_cname] = img

            tree_inserts[i_cname] = (
                c.canonical_name,
                tk.END,
                f"{c.canonical_name}.{img.get_filename()}",
                img.get_filename()
            )

        return c.canonical_name, tree_inserts

    def cmp_numeric(x, y):
        if x == y:
            return 0
        elif x < y:
            return -1
        else:
            return 1

    # best just to keep this bad boy collapsed
    def compare(a: str, b: str) -> int:
        def is_numeric(x) -> (bool, float):
            try:
                f = float(x)
                return True, f
            except ValueError:
                return False, None

        def filename(x: str, is_img: bool) -> (str, str, str):
            if is_img:
                i_split = x.split(".")
                i_len = len(i_split)

                return f"{i_split[i_len - 2]}.{i_split[i_len - 1]}", i_split[i_len - 2], f".{i_split[i_len - 1]}"
            else:
                if "." in x:
                    f = x[(x.rindex(".") + 1):]
                    return f, f, ''
                else:
                    return x, x, ''

        a_is_image = is_image(a)
        b_is_image = is_image(b)

        if not a_is_image and b_is_image:
            return -1
        elif a_is_image and not b_is_image:
            return 1
        elif b_is_image and not a_is_image:
            return -1
        else:
            a_filename, a_name, a_ext = filename(a, a_is_image)
            b_filename, b_name, b_ext = filename(b, b_is_image)

            a_numeric, a_val = is_numeric(a_name)
            b_numeric, b_val = is_numeric(b_name)

            if a_numeric and b_numeric:
                a_part = a[:a.rindex(a_filename) - 1]
                b_part = b[:b.rindex(b_filename) - 1]

                if a_part == b_part:
                    return cmp_numeric(a_val, b_val)
                elif a_part < b_part:
                    return -1
                else:
                    return 1
            elif a == b:
                return 0
            elif a < b:
                return -1
            else:
                return 1

    root_concept, tree_items = build(concept)
    alphabetized_keys = list(set(tree_items.keys()))
    alphabetized_keys.sort(key=cmp_to_key(compare))

    print(f"Alphabetized: {', '.join(alphabetized_keys)}")

    for a_key in alphabetized_keys:
        parent, position, iid, text = tree_items[a_key]
        if iid in concept_images:
            sorted_concept_images[iid] = concept_images[iid]
        treeview_concept.insert(parent, position, iid, text=text)

    __open_tree_item(root_concept)

    menu_file.entryconfig("Flatten Dataset", state=tk.NORMAL)
    menu_file.entryconfig("Save Dataset", state=tk.NORMAL)


def __save_dataset():
    tree_sel = treeview_concept.selection()
    if tree_sel and len(tree_sel) > 0:
        tree_sel = tree_sel[0]

    touched = save_dataset(concepts, concept_images, current_dataset_tags)

    if touched <= 0:
        messagebox.showinfo("Save Complete", "Contents unchanged, no changes were written to disk.")
    else:
        messagebox.showinfo("Save Complete", f"Modified {touched} file(s). Reloading changes from disk.")

        active_iid = active_concept_image.get_canonical_name() if active_concept_image else tree_sel
        __load_concept_tree(working_directory)
        __open_tree_item(active_iid)


def __tags_from_text_field():
    tt = text_image_tags_field.get(1.0, tk.END)
    return normalize_tags([t for t in tt.split(",")])


def __set_tags_text(tags: list[str], parent_tags: list[str] = None):
    if parent_tags is None:
        parent_tags = []

    tags = normalize_tags(tags)
    text_image_tags_field.delete(1.0, tk.END)
    text_image_tags_field.insert(tk.END, ", ".join(tags))

    parent_tags = normalize_tags(parent_tags)
    parent_tags_field.config(state=tk.NORMAL)
    parent_tags_field.delete(1.0, tk.END)
    parent_tags_field.insert(tk.END, ", ".join(parent_tags))
    parent_tags_field.config(state=tk.DISABLED)


padding_size = 8
padding_half_size = padding_size / 2
padding_quarter_size = padding_half_size / 2

__set_title()
menubar = tk.Menu(root)

menu_file = tk.Menu(menubar)
menubar.add_cascade(label="File", menu=menu_file)

menu_file.add_command(label="Open Dataset", command=on_menu_item_open, underline=True, accelerator="Ctrl+O")
menu_file.add_command(label="Save Dataset", command=on_menu_item_save, underline=True, accelerator="Ctrl+S")

menu_file.add_separator()
menu_file.add_command(label="Flatten Dataset", command=on_menu_item_flatten, underline=True, accelerator="Ctrl+L")

menu_file.entryconfig("Save Dataset", state=tk.DISABLED)
menu_file.entryconfig("Flatten Dataset", state=tk.DISABLED)

menu_file.add_separator()
menu_file.add_command(label="Quit", command=on_request_exit, underline=True, accelerator="Ctrl+Q")

root.bind_all("<Control-s>", on_menu_item_save)
root.bind_all("<Control-l>", on_menu_item_flatten)
root.bind_all("<Control-o>", on_menu_item_open)
root.bind_all("<Control-q>", on_request_exit)

root.protocol("WM_DELETE_WINDOW", on_request_exit)

treeview_concept = ttk.Treeview(height=20, selectmode="browse", padding=(0, 0))
treeview_concept.heading("#0", text="Concept Tree", anchor=tk.W)

treeview_concept.grid(row=0, column=0, sticky="news", padx=(padding_size, padding_half_size),
                      pady=(padding_size, padding_half_size))

treeview_concept.bind('<<TreeviewSelect>>', on_tree_view_child_click)

root.grid_rowconfigure(0, minsize=image_preview_size, weight=1)
root.grid_rowconfigure(1, minsize=32)
root.grid_rowconfigure(2, minsize=32 - padding_size)
root.grid_rowconfigure(3, minsize=32 - padding_size)
root.grid_rowconfigure(4, minsize=32)
root.grid_rowconfigure(5, minsize=32 - padding_size)
root.grid_rowconfigure(6, minsize=32 - padding_size)

root.grid_columnconfigure(0, minsize=256)
root.grid_columnconfigure(1, minsize=image_preview_size - 124, weight=1)
root.grid_columnconfigure(2, minsize=124)

label_image_preview = ttk.Label(padding=(0, 0), borderwidth=1, relief="solid")
label_image_preview["image"] = transparent_img
label_image_preview.grid(row=0, column=1, columnspan=2, padx=(padding_half_size, padding_size),
                         pady=(padding_size, padding_half_size), sticky="news")

parent_tags_field = tk.Text(height=1, wrap=tk.WORD)
parent_tags_field.config(state=tk.DISABLED)

parent_tags_field.grid(row=1, rowspan=3, column=0, columnspan=3, stick="news", padx=padding_size,
                       pady=(padding_half_size, padding_half_size))

text_image_tags_field = tk.Text(height=1, wrap=tk.WORD)
text_image_tags_field.grid(row=4, rowspan=3, column=0, columnspan=2, sticky="news",
                           padx=(padding_size, padding_half_size), pady=(padding_half_size, padding_size))

button_paste = tk.Button(text="Paste Last")
button_paste.grid(row=4, column=2, sticky="news", padx=(padding_half_size, padding_half_size),
                  pady=(padding_half_size, 0))

button_paste.bind("<Button-1>", on_paste_button)

button_save = tk.Button(text="Apply")
button_save.grid(row=5, column=2, sticky="news", padx=(padding_half_size, padding_half_size),
                 pady=0)

button_save.bind("<Button-1>", on_apply_button)

button_next = tk.Button(text="Next")
button_next.grid(row=6, column=2, sticky="news", padx=(padding_half_size, padding_half_size), pady=(0, padding_size))

button_next.bind("<Button-1>", on_next_button)


def show_ui():
    root.focus_force()
    root.config(menu=menubar)
    root.mainloop()

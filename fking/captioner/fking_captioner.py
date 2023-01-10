import os
import tkinter as tk
from functools import cmp_to_key
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from fking.captioner.fk_captioning_utils import flatten_dataset, get_concept_tags, get_image_tags, load_image
from fking.fking_captions import Concept, ConceptImage, create_concept
from fking.fking_utils import is_image, normalize_tags

root = tk.Tk()
root.iconbitmap("icon.ico")
root.resizable(False, False)
root.option_add('*tearOff', False)

working_directory: str | None = None
working_concept: Concept | None = None

concepts: dict[str, Concept] = {}
concept_images: dict[str, ConceptImage] = {}
image_cache: dict[str, Image] = {}

modified_tags: dict[str, list[str]] = {}
current_dataset_tags: dict[str, list[str]] = {}

last_modified_tags: list[str] = []

active_img: None | ImageTk.PhotoImage = None

active_concept_image: ConceptImage | None = None

active_parent_tags: list[str] = []
active_img_tags: list[str] = []


def set_active_image(canonical_img: str):
    global active_img, active_img_tags, active_concept_image, active_parent_tags

    active_concept_image = concept_images[canonical_img]

    active_img_tags, active_parent_tags = get_image_tags(canonical_img, concepts, concept_images, current_dataset_tags)
    set_tags_text(active_img_tags, active_parent_tags)

    image = load_image(canonical_img, image_cache, concept_images)
    img_tk = ImageTk.PhotoImage(image)
    active_img = img_tk

    label_image_preview['image'] = active_img
    set_title(f"'{os.path.relpath(active_concept_image.path, working_directory)}'")


def set_active_concept(canonical_concept: str):
    global active_img_tags, active_parent_tags

    target_concept = concepts[canonical_concept]
    active_img_tags, active_parent_tags = get_concept_tags(canonical_concept, concepts, current_dataset_tags)

    set_tags_text(active_img_tags, active_parent_tags)
    path = os.path.relpath(target_concept.working_directory, working_directory)
    if path == ".":
        set_title()
    else:
        set_title(f"'{path}'")


def set_title(title: str | None = None):
    if not title:
        set_title("a fking hierarchical dataset editor")
    else:
        root.title(f'fking captioner - {title}')


def on_menu_item_open(event=None):
    global working_concept, working_directory

    working_directory = filedialog.askdirectory()
    if working_directory is not None and len(working_directory) > 0:
        working_concept = create_concept("global", working_directory)
        build_tree(working_concept)
    else:
        working_concept = None
        clear_tree()


def on_menu_item_flatten(event=None):
    dst_directory = filedialog.askdirectory()
    if dst_directory is not None and len(dst_directory) > 0:
        flatten_dataset(dst_directory, concepts, concept_images, current_dataset_tags)


def on_menu_item_save(event=None):
    pass


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


def on_tree_view_child_click(event):
    global label_image_preview, active_img

    treeview_selection = treeview_concept.selection()
    tree_sel = treeview_selection[0]

    tree_sel_extension = os.path.splitext(tree_sel)[1]
    if tree_sel_extension in [".png", ".jpg", ".jpeg"]:
        set_active_image(tree_sel)

    elif tree_sel in concepts:
        set_active_concept(tree_sel)


def on_save_button(event):
    global last_modified_tags, modified_tags

    tree_selection = treeview_concept.selection()
    if len(tree_selection) <= 0:
        return

    tree_sel = tree_selection[0]
    tags = tags_from_text_field()

    current_dataset_tags[tree_sel] = tags
    last_modified_tags = tags


def tags_from_text_field():
    tt = text_image_tags_field.get(1.0, tk.END)
    return normalize_tags([t for t in tt.split(",")])


def on_next_button(event):
    on_save_button(event)

    tree_sel = treeview_concept.selection()
    if len(tree_sel) <= 0:
        return

    tree_sel = tree_sel[0]
    can_idx = get_canonical_index(tree_sel, concept_images)
    next_idx = can_idx + 1

    if next_idx < len(concept_images):
        next_id = get_canonical_from_index(next_idx, concept_images)
        if next_id is not None:
            treeview_concept.selection_clear()
            treeview_concept.selection_set(next_id)
            treeview_concept.focus(next_id)

            concept = concept_images[next_id].concept

            while concept is not None:
                concept_iid = concept.canonical_name
                treeview_concept.item(concept_iid, open=True)
                concept = concept.parent

    text_image_tags_field.focus_force()


def on_paste_button(event=None):
    if last_modified_tags is not None and len(last_modified_tags) > 0:
        set_tags_text(last_modified_tags, active_parent_tags)


def on_request_exit(event=None):
    if messagebox.askyesno(title="Confirm Exit", message="Are you sure you want to exit?"):
        exit()


def clear_tree():
    concepts.clear()
    concept_images.clear()
    menu_file.entryconfig("Flatten Dataset", state=tk.DISABLED)
    treeview_concept.delete(*treeview_concept.get_children())


def build_tree(concept: Concept):
    clear_tree()

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

    # best just to keep this bad boy collapsed
    def compare(a: str, b: str) -> int:
        def is_numeric(x) -> (bool, float):
            try:
                f = float(x)
                return True, f
            except ValueError:
                print(f"{x} is not float")
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

        if a_is_image and not b_is_image:
            return 1
        elif b_is_image and not a_is_image:
            return -1
        else:
            a_filename, a_name, a_ext = filename(a, a_is_image)
            b_filename, b_name, b_ext = filename(b, b_is_image)

            a_numeric, a_val = is_numeric(a_name)
            b_numeric, b_val = is_numeric(b_name)

            if a_numeric and b_numeric:
                print(f"Comparing {a} and {b} numerically")
                if a_val == b_val:
                    return compare(a_ext[1:], b_ext[1:])
                elif a_val < b_val:
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
        treeview_concept.insert(parent, position, iid, text=text)

    treeview_concept.item(root_concept, open=True)

    menu_file.entryconfig("Flatten Dataset", state=tk.NORMAL)
    menu_file.entryconfig("Save Dataset", state=tk.NORMAL)


def set_tags_text(tags: list[str], parent_tags: list[str] = None):
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

set_title()
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

root.grid_rowconfigure(0, minsize=512, weight=1)
root.grid_rowconfigure(1, minsize=32)
root.grid_rowconfigure(2, minsize=32 - padding_size)
root.grid_rowconfigure(3, minsize=32 - padding_size)
root.grid_rowconfigure(4, minsize=32)
root.grid_rowconfigure(5, minsize=32 - padding_size)
root.grid_rowconfigure(6, minsize=32 - padding_size)

root.grid_columnconfigure(0, minsize=256)
root.grid_columnconfigure(1, minsize=512 - 124, weight=1)
root.grid_columnconfigure(2, minsize=124)

label_image_preview = ttk.Label()
label_image_preview.grid(row=0, column=1, columnspan=2, padx=(padding_half_size, padding_size),
                         pady=(padding_size, padding_half_size))

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

button_save.bind("<Button-1>", on_save_button)

button_next = tk.Button(text="Next")
button_next.grid(row=6, column=2, sticky="news", padx=(padding_half_size, padding_half_size), pady=(0, padding_size))

button_next.bind("<Button-1>", on_next_button)


def show_ui():
    root.pack_slaves()
    root.config(menu=menubar)
    root.mainloop()

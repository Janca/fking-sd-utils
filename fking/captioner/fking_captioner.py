import os.path
import os.path
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

from PIL import Image, ImageTk

from fking.captioner.fk_captioning_utils import load_image
from fking.fking_captions import Concept, ConceptImage, create_concept
from fking.fking_utils import normalize_tags

root = tk.Tk()
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
active_img_tags: list[str] = []


def set_active_image(canonical_img: str):
    global active_img, active_img_tags, active_concept_image

    active_concept_image = concept_images[canonical_img]

    active_img_tags, parent_img_tags = get_image_tags(canonical_img)
    set_tags_text(active_img_tags, parent_img_tags)

    image = load_image(canonical_img, image_cache, concept_images)
    img_tk = ImageTk.PhotoImage(image)
    active_img = img_tk

    label_image_preview['image'] = active_img
    set_title(f"'{os.path.relpath(active_concept_image.path, working_directory)}'")


def set_active_concept(canonical_concept: str):
    target_concept = concepts[canonical_concept]

    target_concept_tags, parent_concept_tags = get_concept_tags(canonical_concept)

    set_tags_text(target_concept_tags, parent_concept_tags)

    print(f"Parent tags: {', '.join(parent_concept_tags)}")

    path = os.path.relpath(target_concept.working_directory, working_directory)
    if path == ".":
        set_title()
    else:
        set_title(f"'{path}'")


def get_image_tags(canonical_img: str) -> (list[str], list[str]):
    c_img = concept_images[canonical_img]
    img_concept: Concept = c_img.concept

    concept_tags, concept_parent_tags = get_concept_tags(img_concept.canonical_name)
    c_tags = concept_parent_tags + concept_tags

    tags = c_img.tags if canonical_img not in current_dataset_tags else current_dataset_tags[canonical_img]
    return normalize_tags(tags), normalize_tags(c_tags)


def get_concept_tags(canonical_concept: str) -> (list[str], list[str]):
    target_concept = concepts[canonical_concept]

    parent_tags: (list[str], list[str]) = get_concept_tags(
        target_concept.parent.canonical_name) \
        if target_concept.parent is not None \
        else ([], [])

    return normalize_tags(target_concept.concept_tags
                          if canonical_concept not in current_dataset_tags
                          else current_dataset_tags[canonical_concept]), \
        normalize_tags(parent_tags[1] + parent_tags[0])


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


def on_menu_item_flatten():
    pass


def on_tree_view_child_click(event):
    global label_image_preview, active_img

    treeview_selection = treeview_concept.selection()
    tree_sel = treeview_selection[0]

    tree_sel_extension = os.path.splitext(tree_sel)[1]
    if tree_sel_extension in [".png", ".jpg", ".jpeg"]:
        set_active_image(tree_sel)

    elif tree_sel in concepts:
        set_active_concept(tree_sel)


def diff_tags(canonical) -> list[str]:
    global last_modified_tags, modified_tags

    def unique_tags(src: list[str], dst: list[str]) -> list[str]:
        return [t for t in src if t not in dst]

    def text_tags():
        tt = text_image_tags_field.get(1.0, tk.END)
        return normalize_tags([t for t in tt.split(",")])

    text_tags = text_tags()

    if canonical in concept_images:
        tags = concept_images[canonical].tags

        if len(text_tags) < len(tags):
            return []
        else:
            return unique_tags(text_tags, tags)

    elif canonical in concepts:
        tags = concepts[canonical].concept_tags
        return unique_tags(text_tags, tags)

    else:
        return []


def on_save_button(event):
    global last_modified_tags, modified_tags

    tree_selection = treeview_concept.selection()
    if len(tree_selection) <= 0:
        return

    tree_sel = tree_selection[0]
    current_dataset_tags[tree_sel] = tags_from_text_field()

    print(f"Applied: {', '.join(current_dataset_tags[tree_sel])}")


def tags_from_text_field():
    tt = text_image_tags_field.get(1.0, tk.END)
    return normalize_tags([t for t in tt.split(",")])


def on_next_button(event):
    on_save_button(event)


def clear_tree():
    concepts.clear()
    concept_images.clear()
    treeview_concept.delete(*treeview_concept.get_children())


def build_tree(concept: Concept):
    clear_tree()

    def build_child(c: Concept, parent: Concept = None):
        concepts[c.canonical_name] = c
        ti = treeview_concept.insert('' if parent is None else parent.canonical_name,
                                     'end', c.canonical_name, text=c.name.replace('_', ' ').title())

        for ch in c.children:
            build_child(ch, c)

        for img in c.images:
            i_cname = img.get_canonical_name()
            concept_images[i_cname] = img

            treeview_concept.insert(c.canonical_name, 'end',
                                    f"{c.canonical_name}.{img.get_filename()}", text=img.get_filename())

        return ti

    tree_item = build_child(concept)
    treeview_concept.item(tree_item, open=True)


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

menu_file.add_command(label="Open Dataset", command=on_menu_item_open, underline=True, accelerator='Ctrl+O')

menu_file.add_command(label="Flatten Dataset", command=on_menu_item_flatten)
menu_file.entryconfig("Flatten Dataset", state=tk.DISABLED)

root.bind_all('<Control-o>', on_menu_item_open)

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

button_save = tk.Button(text="Apply")
button_save.grid(row=5, column=2, sticky="news", padx=(padding_half_size, padding_half_size),
                 pady=0)

button_save.bind("<Button-1>", on_save_button)

button_next = tk.Button(text="Next")
button_next.grid(row=6, column=2, sticky="news", padx=(padding_half_size, padding_half_size), pady=(0, padding_size))

button_next.bind("<Button-1>", on_next_button)

root.pack_slaves()
root.config(menu=menubar)
root.mainloop()
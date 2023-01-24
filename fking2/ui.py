import hashlib
import math
import os.path
import shutil
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk as ttk
from typing import Dict, List, Optional, Union

import PIL
import tkinterdnd2
from PIL import ImageTk
from PIL.Image import Image

import fking2.app as fkapp
import fking2.concepts as fkconcepts
import fking2.dialogs as fkdiag
import fking2.utils as fkutils
from fking2.app import FkApp
from fking2.concepts import FkConcept, FkConceptImage, FkVirtualConcept
from fking2.dataset import FkDataset


class FkFrame:
    _root: tkinterdnd2.TkinterDnD
    _frame: tk.Frame
    _menubar: tk.Menu
    _menu_file: tk.Menu
    _edit_menu: tk.Menu

    _treeview_concepts: ttk.Treeview
    _button_concept_tree_new_concept: tk.Button
    _button_concept_tree_new_image: tk.Button
    _button_concept_tree_refresh: tk.Button
    _button_concept_tree_edit: tk.Button

    _button_tag_editor_paste: tk.Button
    _button_tag_editor_apply: tk.Button
    _button_tag_editor_previous: tk.Button
    _button_tag_editor_next: tk.Button

    _combobox_preview_size: ttk.Combobox

    _previous_preview_size: str = " 512px"
    _values_combobox_preview_size: list[str] = [
        " 512px", " 640px", " 768px"
    ]

    _preview_concept_images_max = {
        _values_combobox_preview_size[0]: 81,
        _values_combobox_preview_size[1]: 100,
        _values_combobox_preview_size[2]: 122,
    }

    _label_image_preview: tk.Label
    _image_transparent_image: Optional[tk.PhotoImage]

    _textfield_parent_tags: tk.Text
    _textfield_tags: tk.Text

    _toolbar_concept_tools: tk.Frame

    _active_datum: Optional[FkDataset.IWorkingDatum]

    _active_image: Optional[Image]
    _active_preview_image: Optional[ImageTk.PhotoImage]

    _image_cache: Dict[str, Dict[str, Image]]

    _label_status_bar_status: tk.Label
    _label_status_bar_datum_info: tk.Label

    _current_status: tk.StringVar
    _last_status: Optional[str]
    _last_status_temp: bool

    _datum_info: tk.StringVar

    _last_tags: Union[List[str], None] = None

    def __init__(self, app: FkApp):
        super().__init__()
        self._app = app

        self.set_preferences()

        self._image_transparent_image = None
        self._active_datum = None
        self._active_image = None
        self._image_cache = {}

        self._last_status = None
        self._last_status_temp = False

        self.__init_frame()
        self.__init_grid()
        self.__init_components()
        self.__init_status_bar()

    def __init_frame(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.withdraw()

        self._root.resizable(False, False)
        self._root.option_add('*tearOff', False)

        self._frame = tk.Frame(self._root, padx=6, pady=6)

        self._menubar = tk.Menu(self._root)
        self._root.config(menu=self._menubar)

        self._menu_file = tk.Menu(self._menubar)
        self._menubar.add_cascade(label="File", menu=self._menu_file)

        self._menu_file.add_command(label="New Dataset", command=self.__on_menu_item_new_dataset,
                                    underline=True, accelerator="Ctrl+N")

        self._menu_file.add_separator()
        self._menu_file.add_command(label="Open Dataset", command=self.__on_menu_item_open_dataset,
                                    underline=True, accelerator="Ctrl+O")

        self._menu_file.add_separator()
        self._menu_file.add_command(label="Save Dataset", command=self.__on_menu_item_save_dataset,
                                    underline=True, accelerator="Ctrl+S")

        self._menu_file.add_command(label="Save As...", command=self.__on_menu_item_save_dataset)

        self._menu_file.add_separator()
        self._menu_file.add_command(label="Flatten Dataset", command=self.__on_menu_item_flatten_dataset,
                                    underline=True, accelerator="Ctrl+L")

        self._menu_file.add_separator()
        self._menu_file.add_command(label="Close Dataset", command=self.__on_menu_item_close_dataset,
                                    underline=True, accelerator="Ctrl+W")

        self._menu_file.add_separator()
        self._menu_file.add_command(label="Quit", command=self.__on_menu_item_exit,
                                    underline=True, accelerator="Ctrl+Q")

        self._root.bind_all("<Control-s>", self.__on_menu_item_save_dataset)
        self._root.bind_all("<Control-l>", self.__on_menu_item_flatten_dataset)
        self._root.bind_all("<Control-o>", self.__on_menu_item_open_dataset)
        self._root.bind_all("<Control-q>", self.request_exit)
        #
        self._root.protocol("WM_DELETE_WINDOW", self.request_exit)

        ico_img = fkutils.find_image_resource("icon.ico")
        self._root.iconbitmap(ico_img)

        self.update_dataset_dependant_menu_state()

    def __init_grid(self):
        # PREVIEW IMAGE
        self._frame.grid_rowconfigure(0, minsize=self._app.preferences.image_preview_size, weight=1)
        # BOTTOM TOOLBAR
        self._frame.grid_rowconfigure(1, minsize=24 + 6, weight=1)
        # TAG EDITOR
        self._frame.grid_rowconfigure(2, weight=0)
        # STATUS BAR
        self._frame.grid_rowconfigure(3, weight=0)

        # CONCEPT TREE
        self._frame.grid_columnconfigure(0, minsize=256, weight=0)
        # CONCEPT TREE SCROLLBAR
        self._frame.grid_columnconfigure(1, weight=0)
        # PREVIEW IMAGE
        self._frame.grid_columnconfigure(2, minsize=self._app.preferences.image_preview_size, weight=1)

    def __init_components(self):
        self._frame.pack()

        self._treeview_concepts = ttk.Treeview(self._frame, selectmode="browse", padding=(0, 0))
        self._treeview_concepts.heading("#0", text="Concept Tree", anchor=tk.W)
        self._treeview_concepts.grid(row=0, column=0, sticky="news")

        treeview_scrollbar = ttk.Scrollbar(self._frame, orient="vertical", command=self._treeview_concepts.yview)
        treeview_scrollbar.grid(row=0, column=1, sticky="nes")

        self._treeview_concepts.configure(yscrollcommand=treeview_scrollbar.set)
        self._treeview_concepts.bind("<<TreeviewSelect>>", self.__on_treeview_concept_item_selected)

        # noinspection PyProtectedMember
        tkinterdnd2.TkinterDnD._require(self._root)
        # noinspection PyUnresolvedReferences
        self._treeview_concepts.drop_target_register(tkinterdnd2.DND_FILES)
        # noinspection PyUnresolvedReferences
        self._treeview_concepts.dnd_bind("<<Drop>>", self.__on_concept_tree_file_drop)

        self._label_image_preview = ttk.Label(self._frame, padding=(0, 0), borderwidth=1, relief="solid")
        self._label_image_preview.grid(row=0, column=2, sticky="news", padx=(6, 0))

        self._toolbar_concept_tools = tk.Frame(self._frame, borderwidth=1, relief=tk.FLAT)
        self._toolbar_concept_tools.grid(row=1, column=0, sticky="news", pady=(6, 0))

        self._new_concept_ico = fkutils.get_photo_image_resource("folder-new.png")
        self._button_concept_tree_new_concept = tk.Button(self._toolbar_concept_tools, image=self._new_concept_ico,
                                                          height=24, width=24, relief="flat",
                                                          command=self.__on_button_new_concept)

        # self._new_image_ico = fkutils.get_photo_image_resource("insert-image.png")
        # self._button_concept_tree_new_image = tk.Button(self._toolbar_concept_tools, image=self._new_image_ico,
        #                                                 height=24, width=24, relief="flat",
        #                                                 command=self.__on_button_dnd_zone)

        self._edit_ico = fkutils.get_photo_image_resource("edit-rename.png")
        self._button_concept_tree_edit = tk.Button(self._toolbar_concept_tools, image=self._edit_ico,
                                                   height=24, width=24, relief="flat")

        self._refresh_ico = fkutils.get_photo_image_resource("refresh.png")

        self._button_concept_tree_refresh = tk.Button(self._toolbar_concept_tools, image=self._refresh_ico,
                                                      height=24, width=24, relief="flat")

        self._button_concept_tree_new_concept.pack(side=tk.LEFT)
        # self._button_concept_tree_new_image.pack(side=tk.LEFT)
        self._button_concept_tree_edit.pack(side=tk.LEFT)
        self._button_concept_tree_refresh.pack(side=tk.RIGHT)

        frame_tag_editor = tk.Frame(self._frame)
        frame_tag_editor.grid(row=2, column=0, columnspan=3, sticky=tk.NSEW, pady=(6, 0))

        frame_tag_editor.grid_rowconfigure(0, weight=0)
        frame_tag_editor.grid_rowconfigure(1, weight=0)

        frame_tag_editor.grid_columnconfigure(0, weight=1)
        frame_tag_editor.grid_columnconfigure(1, minsize=148, weight=0)

        frame_parent_tags, self._textfield_parent_tags = fkutils.border_widget(
            frame_tag_editor,
            lambda tkf: tk.Text(tkf, height=4, wrap=tk.WORD, relief="flat"),
            focus_color="#a0a0a0"
        )

        frame_tags, self._textfield_tags = fkutils.border_widget(
            frame_tag_editor,
            lambda tkf: tk.Text(tkf, height=6, wrap=tk.WORD, relief="flat")
        )

        self._textfield_parent_tags.configure(state=tk.DISABLED)

        frame_parent_tags.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
        frame_tags.grid(row=1, column=0, sticky=tk.NSEW, pady=(6, 0))

        frame_tag_editor_actions = tk.Frame(frame_tag_editor)
        frame_tag_editor_actions.grid(row=1, column=1, sticky=tk.NSEW, padx=(6, 0), pady=(6, 0))

        frame_tag_editor_actions.grid_rowconfigure(0, weight=0)
        frame_tag_editor_actions.grid_rowconfigure(1, weight=0)
        frame_tag_editor_actions.grid_rowconfigure(2, weight=0)

        frame_tag_editor_actions.grid_columnconfigure(0, weight=0)
        frame_tag_editor_actions.grid_columnconfigure(1, weight=0)

        self._paste_ico = fkutils.get_photo_image_resource("paste.png")
        self._apply_ico = fkutils.get_photo_image_resource("dialog-ok-apply.png")
        self._previous_ico = fkutils.get_photo_image_resource("left.png")
        self._next_ico = fkutils.get_photo_image_resource("right.png")

        self._button_tag_editor_paste = tk.Button(frame_tag_editor_actions, compound=tk.LEFT,
                                                  image=self._paste_ico, text="Paste", padx=3)

        self._button_tag_editor_apply = tk.Button(frame_tag_editor_actions, text="Apply",
                                                  image=self._apply_ico, padx=3, compound=tk.LEFT)

        self._button_tag_editor_previous = tk.Button(frame_tag_editor_actions, compound=tk.LEFT, height=20,
                                                     image=self._previous_ico, text="Prev", padx=3)

        self._button_tag_editor_next = tk.Button(frame_tag_editor_actions, compound=tk.RIGHT, height=20,
                                                 image=self._next_ico, text="Next", padx=3)

        self._button_tag_editor_paste.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._button_tag_editor_apply.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._button_tag_editor_previous.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._button_tag_editor_next.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        self._button_tag_editor_paste.bind("<Button-1>", self.__on_button_paste)
        self._button_tag_editor_apply.bind("<Button-1>", self.__on_button_apply)
        self._button_tag_editor_previous.bind("<Button-1>", self.__on_button_previous)
        self._button_tag_editor_next.bind("<Button-1>", self.__on_button_next)

        frame_preview_size = tk.Frame(self._frame)
        self._combobox_preview_size = ttk.Combobox(
            frame_preview_size,
            width=6,
            values=self._values_combobox_preview_size,
            justify=tk.CENTER
        )

        preview_size_index = self._values_combobox_preview_size.index(self._previous_preview_size)
        self._combobox_preview_size.current(preview_size_index)
        self._combobox_preview_size.configure(state="readonly")
        self._combobox_preview_size.configure(justify=tk.RIGHT)

        self._combobox_preview_size.bind("<<ComboboxSelected>>", self.__on_combobox_preview_size)

        self._combobox_preview_size.pack(side=tk.RIGHT, fill=tk.Y, expand=True, pady=4)

        label_preview_size = tk.Label(frame_preview_size, text="Preview Size:", padx=3)
        label_preview_size.pack(side=tk.RIGHT, fill=tk.Y, expand=True)

        self.__bind_status_text(label_preview_size, "Set previewer size")

        frame_preview_size.grid(row=1, column=2, sticky="NSE", pady=(6, 0))

        frame_status_bar = tk.Frame(self._frame)

        self._current_status = tk.StringVar(self._frame)
        self._datum_info = tk.StringVar(self._frame)

        self._label_status_bar_status = tk.Label(frame_status_bar, justify=tk.LEFT, anchor=tk.W,
                                                 textvariable=self._current_status)

        self._label_status_bar_datum_info = tk.Label(frame_status_bar, justify=tk.RIGHT, anchor=tk.E,
                                                     textvariable=self._datum_info)

        self._label_status_bar_status.pack(side=tk.LEFT)
        self._label_status_bar_datum_info.pack(side=tk.RIGHT)

        frame_status_bar.grid(row=3, column=0, columnspan=3, pady=(6, 0), sticky=tk.NSEW)

    def __init_status_bar(self):
        widgets = [
            [self._button_concept_tree_new_concept, "Create new child concept"],
            # [self._button_concept_tree_new_image, "Add images to selected concept"],
            [self._button_concept_tree_edit, "Edit selected concept"],
            [self._button_concept_tree_refresh, "Refresh concept tree"],
            [self._button_tag_editor_paste, "Paste tags from previously selected datum"],
            [self._button_tag_editor_apply, "Apply tags to selected datum"],
            [self._button_tag_editor_next, "Apply tags and go to next datum"],
            [self._button_tag_editor_previous, "Apply tags and go to previous datum"],
            [self._combobox_preview_size, "Set previewer size"],

            [self._menu_file, "File menu"]
        ]

        for widget, status_text in widgets:
            self.__bind_status_text(widget, status_text)

    def set_status(self, status: str):
        self._last_status = self._current_status.get()
        self._current_status.set(status)

    def set_datum_info(self, datum: FkDataset.IWorkingDatum):
        if isinstance(datum, FkDataset.WorkingImage):
            img_dimensions = datum.get_meta('image_dimensions')
            if img_dimensions:
                w, h = img_dimensions
                self._datum_info.set(f"Dimensions: ({w}x{h})")
        else:
            self._datum_info.set('')

    def set_preferences(self):
        preferences = self._app.preferences
        self._previous_preview_size = f" {preferences.image_preview_size}px"

    def show(self):
        self._root.overrideredirect(False)
        self._root.deiconify()

        self.set_title()

        self.set_ui_state(tk.DISABLED)
        self.clear_image_preview()
        self.set_status("Ready")

        self._root.mainloop()

    def set_textfield_tags(self, tags: list[str], parent_tags: list[str]):
        current_state = self._textfield_tags.cget("state")
        self._textfield_tags.configure(state=tk.NORMAL)
        self._textfield_tags.delete(1.0, tk.END)

        self._textfield_parent_tags.configure(state=tk.NORMAL)
        self._textfield_parent_tags.delete(1.0, tk.END)

        if len(tags) > 0:
            str_tags = ', '.join(tags)
            self._textfield_tags.insert(tk.END, str_tags)

        if len(parent_tags) > 0:
            str_parent_tags = ', '.join(parent_tags)
            self._textfield_parent_tags.insert(tk.END, str_parent_tags)

        self._textfield_tags.configure(state=current_state)
        self._textfield_parent_tags.configure(state=tk.DISABLED)

    def set_title(self, fragment: str = None):
        if fragment is None:
            self.set_title("a fking hierarchical dataset editor")
        else:
            modified = self._app.working_dataset is not None and self._app.working_dataset.modified
            modified_star = '*' if modified else ''
            version = f"v{fkapp.version}"
            self._root.title(f"{modified_star}fking captioner {version} - {fragment}")

    def set_ui_state(self, state: Union[tk.NORMAL, tk.DISABLED]):
        self._button_concept_tree_new_concept.configure(state=state)
        # self._button_concept_tree_new_image.configure(state=state)
        self._button_concept_tree_edit.configure(state=state)
        self._button_concept_tree_refresh.configure(state=state)

        self._button_tag_editor_paste.configure(state=state)
        self._button_tag_editor_apply.configure(state=state)
        self._button_tag_editor_next.configure(state=state)
        self._button_tag_editor_previous.configure(state=state)

        self._textfield_tags.configure(state=state)

    def set_concept_tools_ui_state(self, state: Union[tk.NORMAL, tk.DISABLED]):
        self._button_concept_tree_new_concept.configure(state=state)
        # self._button_concept_tree_new_image.configure(state=state)
        self._button_concept_tree_edit.configure(state=state)

        self._button_tag_editor_paste.configure(state=state)
        self._button_tag_editor_apply.configure(state=state)
        self._button_tag_editor_next.configure(state=state)
        self._button_tag_editor_previous.configure(state=state)

        self._textfield_tags.configure(state=state)

    def update_dataset_dependant_menu_state(self):
        state = tk.NORMAL if self._dataset is not None else tk.DISABLED
        self._menu_file.entryconfig("Save Dataset", state=state)

        if state != tk.DISABLED and self._dataset.root.virtual:
            self._menu_file.entryconfig("Save As...", state=tk.DISABLED)
        else:
            self._menu_file.entryconfig("Save As...", state=state)

        self._menu_file.entryconfig("Flatten Dataset", state=state)
        self._menu_file.entryconfig("Close Dataset", state=state)

    def refresh_concept_tree(self):
        self.set_status("Refreshing concept tree...")
        dataset = self._dataset

        self._treeview_concepts.delete(*self._treeview_concepts.get_children())

        if dataset is None:
            self.set_status("Ready")
            return

        datum_keys = dataset.keys
        print('\n'.join(datum_keys))

        concept_count = 0
        image_count = 0

        for key in datum_keys:
            datum = dataset.get(key)
            parent_concept: Optional[FkConcept] = None
            if isinstance(datum, FkDataset.WorkingConcept):
                parent_concept = datum.concept.parent
                concept_count = concept_count + 1
            elif isinstance(datum, FkDataset.WorkingImage):
                parent_concept = datum.concept
                image_count = image_count + 1
            self._treeview_concepts.insert(
                '' if parent_concept is None else parent_concept.canonical_name,
                tk.END,
                datum.canonical_name,
                text=datum.name
            )

        self.update_dataset_dependant_menu_state()
        self.set_status(f"Loaded '{concept_count}' concept(s) and '{image_count}' image(s)")

    def refresh_image_preview(self):
        self.set_status("Loading preview...")
        if self._active_datum is None:
            self.clear_image_preview()
            self.set_status("Ready")
        else:
            image = self.load_image(self._active_datum.canonical_name)
            if image is None:
                self.clear_image_preview()
                self.set_status("Ready")
                return

            fix_to_top = True if isinstance(self._active_datum, FkDataset.WorkingConcept) else False
            self._active_image = fit_image_to_canvas(image, self._preferences.image_preview_size, True, fix_to_top)
            self._active_preview_image = ImageTk.PhotoImage(self._active_image)
            self._label_image_preview.configure(image=self._active_preview_image)
            self.set_status("Ready")

    def open_datum(self, canonical_name: str):
        self._treeview_concepts.selection_clear()

        concept = self._dataset.get(canonical_name).concept

        while concept is not None:
            iid = concept.canonical_name
            self._treeview_concepts.item(iid, open=True)
            concept = concept.parent

        self._treeview_concepts.selection_set(canonical_name)
        self._treeview_concepts.focus(canonical_name)
        self._treeview_concepts.see(canonical_name)

    def set_selected_datum(self, canonical_name: str):
        dataset = self._dataset
        datum = dataset.get(canonical_name)
        if datum is None:
            return

        self._active_datum = datum
        tag, parent_tags = dataset.get_tags(datum.canonical_name)

        self.set_ui_state(tk.NORMAL)
        self.set_textfield_tags(tag, parent_tags)

        self.refresh_image_preview()
        self.set_datum_info(datum)

        self._textfield_tags.focus()
        # self.set_title(f"'{fragment}'")

    def clear_dataset(self):
        self._app.set_working_dataset(None)
        self._image_cache.clear()

        self._active_datum = None

        self.refresh_image_preview()
        self.refresh_concept_tree()

    def clear_image_preview(self):
        transparent_image = get_transparency_image(
            self._app.preferences.image_preview_size,
            self._app.preferences.image_preview_size
        )

        self._image_transparent_image = ImageTk.PhotoImage(transparent_image)
        self._label_image_preview.configure(image=self._image_transparent_image)

    def load_image(self, canonical_name: str, size: Union[int, None] = None) -> Union[Image, None]:
        datum = self._dataset.get(canonical_name)
        if datum is None:
            return None

        target_size = self._preferences.image_preview_size if size is None else size
        str_target_size = str(target_size)

        if str_target_size in self._image_cache:
            if canonical_name in self._image_cache[str_target_size]:
                return self._image_cache[str_target_size][canonical_name]

        if isinstance(datum, FkDataset.WorkingConcept):
            target_size = self._combobox_preview_size.current()
            target_size = self._values_combobox_preview_size[target_size]

            max_concept_images = self._preview_concept_images_max[target_size]
            target_size_int = self._preferences.image_preview_size

            concept_grid = self.get_concept_image_grid(datum, max_concept_images, target_size_int)

            if str_target_size not in self._image_cache:
                self._image_cache[str_target_size] = {}

            # concept_grid = fit_image_to_canvas(concept_grid, target_size_int)
            self._image_cache[str_target_size][canonical_name] = concept_grid
            return concept_grid
        elif isinstance(datum, FkDataset.WorkingImage):
            image_path = datum.image.file_path
            image = load_image_from_disk(image_path)

            datum.set_meta("image_dimensions", (image.width, image.height))
            if str_target_size not in self._image_cache:
                self._image_cache[str_target_size] = {}

            image = fit_image_to_canvas(image, target_size)
            self._image_cache[str_target_size][canonical_name] = image
            return image
        else:
            raise ValueError(f"from unexpected datum type: '{type(datum)}'")

    def get_concept_image_grid_2(self, datum: FkDataset.WorkingConcept, max_concept_images: int,
                                 size: Union[int, None]):
        size = self._app.preferences.image_preview_size if size is None else size
        files = {}

        for child in datum.concept.children:
            canonical = child.canonical_name
            if canonical not in files:
                files[canonical] = []

            files[canonical].extend(child.images)

        if len(files) <= 0:
            return get_transparency_image(size, size)

        images = []
        y = max_concept_images // len(files) + (max_concept_images % len(files) != 0)
        for concept, images in files.items():
            s_images = images[:y]
            images.extend(s_images)

        if len(images) <= 0:
            return get_transparency_image(size, size)

        images = [self.load_image(img.canonical_name, size) for img in images]
        return image_grid(images, size)

    def get_concept_image_grid(self, datum: FkDataset.IWorkingDatum, max_concept_images: int, canvas_size: int):

        concepts, concept_images = hierarchy(datum.concept, True)
        concepts = [c for c in concepts if len(c.images) > 0]

        concept_len = len(concepts)
        if concept_len <= 0:
            return get_transparency_image(canvas_size, canvas_size)

        images_per_concept = max(round(max_concept_images / concept_len), 1)
        selected_images = []

        diff = max_concept_images - images_per_concept
        if diff > 0:
            images_per_concept = round(images_per_concept)

        try:
            for c in concepts:
                c_img_len = len(c.images)
                for i in range(min(images_per_concept, c_img_len)):
                    c_image = c.images[i]
                    c_img_canonical = c_image.canonical_name
                    image = self.load_image(c_img_canonical, canvas_size)
                    selected_images.append(image)

                    if len(selected_images) >= max_concept_images:
                        raise StopIteration
        except StopIteration:
            pass

        if len(selected_images) <= 0:
            return get_transparency_image(canvas_size, canvas_size)

        return image_grid(selected_images, canvas_size)

    def cache_image_set(self, size: int):
        def do_cache(pbd):
            """
            :type pbd fking2.dialogs._ProgressDialog
            :return:
            """
            dataset = self._dataset
            keys = dataset.keys
            total = len(keys)
            current = 0

            concept_keys: List[str] = []
            for key in keys:
                datum = dataset.get(key)
                if isinstance(datum, FkDataset.WorkingConcept):
                    concept_keys.append(key)
                else:
                    pbd.update_progressbar(f"Caching image...", current, total)
                    self.set_status(f"Caching image '{datum.canonical_name}'...")
                    self.load_image(datum.canonical_name, size)
                    current = current + 1

            for key in concept_keys:
                datum = dataset.get(key)
                pbd.update_progressbar(f"Caching image...", current, total)
                self.set_status(f"Caching image '{datum.canonical_name}'...")
                self.load_image(datum.canonical_name, size)
                current = current + 1

            self.set_status("Ready")

        return do_cache

    def request_exit(self, *args):
        if self._dataset is None or not self._dataset.modified:
            self._root.destroy()
            return

        if tkinter.messagebox.askyesno(
                title="Confirm Exit",
                message="Your dataset has changes not written to disk."
                        "\nAre you sure you want to exit?"
        ):
            self._root.destroy()

    @property
    def _dataset(self):
        return self._app.working_dataset

    @property
    def _preferences(self):
        return self._app.preferences

    @property
    def _current_tree_selection(self) -> Union[str, None]:
        treeview_selection = self._treeview_concepts.selection()
        return None if len(treeview_selection) <= 0 else treeview_selection[0]

    @property
    def textfield_tags(self) -> List[str]:
        text_tags = self._textfield_tags.get(1.0, tk.END)
        if text_tags is None or len(text_tags) <= 0:
            return []

        split_tags = text_tags.split(',')
        return fkutils.normalize_tags(split_tags)

    def __on_menu_item_new_dataset(self, *args):
        self.set_status("Creating dataset...")
        name, tags = fkdiag.create_new_dataset(self._root)

        if name is None:
            self.set_status(self._last_status)
            return

        root_concept = FkVirtualConcept(None, name, tags)
        working_set = FkDataset(root_concept)

        self._app.set_working_dataset(working_set)
        self.refresh_concept_tree()

        self.open_datum(root_concept.canonical_name)

        self.set_ui_state(tk.NORMAL)
        self.set_status(f"Dataset '{root_concept.name}' created")

    def __on_menu_item_open_dataset(self, *args):
        if self._dataset is not None and self._dataset.modified:
            if tkinter.messagebox.askyesno(
                    title="Save Current Dataset",
                    message="You have unsaved changes."
                            "\nWould you like to save before opening a new dataset?"
                            "\n\nThis action is irreversible."
            ) and not self.__on_menu_item_save_dataset(*args):
                return False

        self.set_status("Opening dataset...")
        dataset_directory = tkinter.filedialog.askdirectory(parent=self._root, title="Open Dataset Directory")

        if not dataset_directory:
            self.set_status(self._last_status)
            return False

        self.clear_dataset()

        def do_open(pbd):
            pbd.update_progressbar("Opening dataset...")
            root_concept = fkconcepts.build_concept_tree(dataset_directory)
            dataset = FkDataset(root_concept)

            self._app.set_working_dataset(dataset)
            self.refresh_concept_tree()

        cache_image_size = self._preferences.image_preview_size
        do_cache = self.cache_image_set(cache_image_size)
        fkdiag.show_progress_bar(self._root, do_open, do_cache)
        self.open_datum(self._dataset.root.canonical_name)
        return True

    def __on_menu_item_flatten_dataset(self, *args):
        dataset = self._dataset
        if dataset is None:
            return

        # TODO add option to for saving dataset before flattening
        self.set_status("Flattening dataset...")

        dst_directory = tkinter.filedialog.askdirectory(
            parent=self._root,
            title="Select Directory for Output"
        )

        if dst_directory is None or len(dst_directory) <= 0:
            self.set_status("Ready")
            return

        dataset_directory = os.path.join(dst_directory, "dataset")
        if os.path.isdir(dataset_directory):
            if tkinter.messagebox.askyesno(
                    title="Overwrite Confirmation",
                    message="Are you sure you want to overwrite the existing directory contents?"
                            "\n\nThis action is irreversible."
            ):
                shutil.rmtree(dataset_directory)
            else:
                tkinter.messagebox.showinfo(
                    title="Flattening Cancelled",
                    message="Cancelled flattening operation, no changes were written to disk."
                )

                self.set_status("Ready")
                return

        def do_flatten(pbd):
            """
            :type pbd fking2.dialogs._ProgressDialog
            :return:
            """

            pbd.update_progressbar("Flattening dataset...")
            os.makedirs(dataset_directory, exist_ok=True)

            pbd.update_progressbar("Flattening dataset...", 0, images_len)
            for i, image in enumerate(images):
                self.set_status(f"Flattening '{image.canonical_name}'...")
                pbd.update_progressbar("Flattening image...", i + 1, images_len)
                tags, parent_tags = dataset.get_tags(image.canonical_name)

                out_tags = []
                out_tags.extend(parent_tags)
                out_tags.extend(tags)

                out_tags = fkutils.normalize_tags(out_tags)

                u_name = hashlib.sha256(image.canonical_name.encode()).hexdigest()
                img_ext = os.path.splitext(image.image.filename)[1]

                dst_image = os.path.join(dataset_directory, u_name + img_ext)
                dst_tags_file = os.path.join(dataset_directory, u_name + ".txt")

                # print(f"Copying {image.image.file_path} to {dst_image}")
                shutil.copyfile(image.image.file_path, dst_image)

                if len(out_tags) <= 0:
                    continue

                fkutils.write_tags(dst_tags_file, out_tags)

        images = dataset.images
        images_len = len(images)
        if images_len <= 0:
            return

        fkdiag.show_progress_bar(self._root, do_flatten)
        tkinter.messagebox.showinfo(
            title="Flatten Dataset Complete",
            message=f"Flattened {images_len:,} image(s)."
        )

        self.set_status("Ready")

    def __on_menu_item_save_dataset(self, *args):
        if self._dataset is None:
            return False

        if not self._dataset.modified:
            return False

        if self._dataset.virtual:
            dst_directory = tkinter.filedialog.askdirectory(title="Save Dataset")
            if dst_directory is None or len(dst_directory) <= 0:
                return
        else:
            dst_directory = self._dataset.directory_path

        self.set_ui_state(tk.DISABLED)
        dataset = self._dataset

        def do_save(pbd):
            """
            :type pbd: fking2.dialogs._ProgressDialog
            :return:
            """
            pbd.update_progressbar("Saving Dataset...")

            datum_keys = dataset.keys
            length = len(datum_keys)

            pbd.update_progressbar("Saving Dataset...", 0, length)

            for i, datum_key in enumerate(datum_keys):
                pbd.update_progressbar("Saving Dataset...", i, length)
                datum = dataset.get(datum_key)

                if isinstance(datum, FkDataset.WorkingConcept):
                    relpath = datum.concept.directory_path.partition(dataset.directory_path)[2][1:]
                    dst_path = os.path.join(dst_directory, relpath)
                    if not os.path.isdir(dst_path):
                        os.makedirs(dst_path, exist_ok=True)

                    if not datum.modified:
                        continue

                    concept_tags = fkutils.normalize_tags(datum.tags)
                    if len(concept_tags) > 0:
                        tags_path = os.path.join(dst_path, "__prompt.txt")
                        fkutils.write_tags(tags_path, concept_tags)

                if isinstance(datum, FkDataset.WorkingImage):
                    filename = datum.image.filename
                    relpath = datum.concept.directory_path.partition(dataset.directory_path)[2][1:]
                    dst_path = os.path.join(dst_directory, relpath, filename)

                    if not os.path.isfile(dst_path):
                        shutil.copyfile(datum.image.file_path, dst_path)

                    if not datum.modified:
                        continue

                    filename = datum.image.text_filename
                    relpath = datum.image.concept.directory_path.partition(dataset.directory_path)[2][1:]
                    tags_path = os.path.join(dst_directory, relpath, filename)

                    if datum.modified or not os.path.isfile(tags_path):
                        fkutils.write_tags(tags_path, datum.tags)

        fkdiag.show_progress_bar(self._root, do_save)
        self.set_ui_state(tk.NORMAL)
        return True

    def __on_menu_item_close_dataset(self, *args):
        dataset = self._dataset
        if dataset is None:
            return

        if not dataset.modified or tkinter.messagebox.askyesno(
                title="Confirm Close",
                message="You dataset contains changes not written to disk."
                        "\nAre you sure you want to close?"
        ):
            self.clear_dataset()
            self.update_dataset_dependant_menu_state()

    def __on_menu_item_exit(self, *args):
        self.request_exit()

    def __on_button_new_concept(self, *args):
        datum_selection = self._current_tree_selection
        if datum_selection is None:
            return

        selected_datum = self._dataset.get(datum_selection)
        if selected_datum is None:
            return

        target_concept = selected_datum.concept

        name, tags = fkdiag.create_new_concept(self._root, self._dataset, target_concept)
        if name is None or len(name) <= 0:
            return

        existing = self._dataset.get(name)
        if existing is not None:
            return

        virtual_concept = FkVirtualConcept(target_concept, name, tags)
        target_concept.add_child(virtual_concept)

        self._dataset.refresh()
        self.refresh_concept_tree()

        self.open_datum(virtual_concept.canonical_name)

    def __on_button_dnd_zone(self, *args):
        current_sel = self._current_tree_selection
        if current_sel is None:
            return

        datum = self._dataset.get(current_sel)
        datum_concept = datum.concept

        files = fkdiag.drag_and_drop(self._root)
        if files is None or len(files) <= 0:
            return

        for file in files:
            concept_image = FkConceptImage(datum_concept, file)
            datum_concept.add_image(concept_image)

        self._dataset.refresh()
        self.refresh_concept_tree()

        str_size = str(self._preferences.image_preview_size)
        del self._image_cache[str_size][datum_concept.canonical_name]
        self.load_image(datum_concept.canonical_name)

        self.set_selected_datum(datum.canonical_name)
        self.open_datum(datum.canonical_name)

    def __on_button_refresh(self, *args):
        pass

    def __on_combobox_preview_size(self, *args):
        selected_value = args[0].widget.get()[1:]
        selected_int_value = int(selected_value[:-2])
        current_size = self._app.preferences.image_preview_size
        current_sel = self._combobox_preview_size.current()

        active_datum = self._active_datum

        if selected_int_value != current_size:
            self._active_datum = None

            root_geometry = self._root.winfo_geometry()
            _, x, y = root_geometry.split('+')

            root_w = self._root.winfo_width()
            root_h = self._root.winfo_height()

            screen_width = self._root.winfo_screenwidth()
            screen_height = self._root.winfo_screenheight()

            diff = current_size - selected_int_value
            if (root_h - diff) > (screen_height - 98) or root_w - diff > screen_width:
                if not tkinter.messagebox.askyesno(
                        title="Dimension Out-of-Bounds",
                        message=f"Setting the image previewer to '{selected_value}' will cause the"
                                f"\nuser interface to continue past your screen edges."
                                f"\n\nWould you like to continue?"
                ):
                    if self._previous_preview_size is not None:
                        p_idx = self._values_combobox_preview_size.index(self._previous_preview_size)
                        self._combobox_preview_size.current(p_idx)

                    return

            self._app.preferences.image_preview_size = selected_int_value
            self._previous_preview_size = f" {selected_int_value}px"

            half_diff = int(diff / 2)

            x = max(0, (int(x) + half_diff))
            y = max(0, (int(y) + half_diff))

            cleared_cache = False
            if self._dataset is not None and tkinter.messagebox.askyesno(
                    title=f"fking captioner v{fkapp.version} - Rebuild Cache",
                    message="Would you like to rebuild the image cache?"
            ):
                str_size = str(selected_int_value)
                image_cache_keys = self._image_cache.keys()
                for key in image_cache_keys:
                    if key != str_size:
                        self._image_cache[key].clear()

                do_cache = self.cache_image_set(selected_int_value)
                fkdiag.show_progress_bar(self._root, do_cache)
                cleared_cache = True

            if not cleared_cache:
                self.clear_image_preview()

            self._root.geometry(f"+{x}+{y}")
            self.__init_grid()
            self._root.focus()

            self.refresh_image_preview()

            if active_datum is not None:
                self._active_datum = active_datum
                self.open_datum(self._active_datum.canonical_name)

    def __on_treeview_concept_item_selected(self, *args):
        treeview_selection = self._current_tree_selection
        if treeview_selection is None:
            return

        self.set_selected_datum(treeview_selection)

    def __on_button_paste(self, *args):
        datum = self._active_datum
        if datum is None:
            return

        last_tags = self._last_tags
        if last_tags is None or len(last_tags) <= 0:
            return

        textfield_state = self._textfield_tags.cget("state")
        if textfield_state != tk.NORMAL:
            return

        tags, parent_tags = self._dataset.get_tags(datum.canonical_name)
        self.set_textfield_tags(last_tags, parent_tags)

    def __on_button_apply(self, *args):
        datum = self._active_datum
        if datum is None:
            return

        tags = self.textfield_tags
        self._dataset.apply_tags(datum.canonical_name, tags)

    def __on_button_previous(self, *args):
        if self._dataset is None:
            return

        current_sel = self._current_tree_selection
        if current_sel is None or len(current_sel) <= 0:
            return

        def prev_entry_treeview(treeview: ttk.Treeview, current_iid: str) -> Union[str, None]:
            prev_iid = treeview.prev(current_iid)
            if prev_iid:
                prev_children = treeview.get_children(prev_iid)
                if prev_children:
                    sub_children = treeview.get_children(prev_children[-1])
                    if sub_children:
                        return sub_children[-1]
                    return prev_children[-1]
                return prev_iid

            parent_iid = treeview.parent(current_iid)
            if parent_iid:
                return parent_iid

            return None

        tree_prev_iid = prev_entry_treeview(self._treeview_concepts, current_sel)
        if tree_prev_iid:
            self.__on_button_apply(*args)
            self.open_datum(tree_prev_iid)

    def __on_button_next(self, *args):
        if self._dataset is None:
            return

        current_sel = self._current_tree_selection
        if current_sel is None or len(current_sel) <= 0:
            return

        def next_entry_treeview(treeview, current_iid):
            child_iid = treeview.get_children(current_iid)
            if child_iid:
                return child_iid[0]
            next_iid = treeview.next(current_iid)
            if next_iid:
                return next_iid
            parent_iid = treeview.parent(current_iid)
            if parent_iid:
                next_sibling_iid = treeview.next(parent_iid)
                if next_sibling_iid:
                    return next_sibling_iid
                else:
                    parent_parent_iid = treeview.parent(parent_iid)
                    if parent_parent_iid:
                        next_sibling_iid = treeview.next(parent_parent_iid)
                        if next_sibling_iid:
                            return next_sibling_iid
                        else:
                            return next_entry_treeview(treeview, parent_parent_iid)
            return None

        next_tree_iid = next_entry_treeview(self._treeview_concepts, current_sel)
        if next_tree_iid:
            self.__on_button_apply(*args)
            self.open_datum(next_tree_iid)

    def __on_concept_tree_file_drop(self, *args):
        dataset = self._dataset
        if dataset is None:
            return

        datum = self._active_datum
        if datum is None:
            return

        def find_images(path: str) -> list[str]:
            if os.path.isfile(path) and fkutils.is_image(path):
                return [path]

            if os.path.isdir(path):
                images: list[str] = []

                for filename in os.listdir(path):
                    images.extend(find_images(os.path.join(path, filename)))

                return images

            return []

        target_concept = datum.concept
        dnd_files = self._root.splitlist(args[0].data)

        def do_dnd(pbd):
            """
            :type pbd: fking2.dialogs._ProgressDialog
            :return:
            """
            self.set_status(f"Adding images to '{target_concept.canonical_name}'...")
            pbd.update_progressbar("Scanning for images...")

            temp_root = FkVirtualConcept(target_concept.parent, target_concept.directory_name,
                                         target_concept.read_tags())

            for file in dnd_files:
                if os.path.isfile(file) and fkutils.is_image(file):
                    img = FkConceptImage(temp_root, file)
                    temp_root.add_image(img)
                elif os.path.isdir(file):
                    child_concept = fkconcepts.build_concept_tree(file, temp_root)
                    temp_root.add_child(child_concept)

            if len(temp_root.children) > 0:
                temp_root.copy_to(target_concept, lambda e: not self._dataset.contains(e.canonical_name))
            else:
                for image in temp_root.images:
                    if not self._dataset.contains(image.canonical_name):
                        fkconcepts.copy(image, target_concept)

            pbd.update_progressbar("Refreshing dataset...")
            self._dataset.refresh()

            pbd.update_progressbar("Rebuilding dataset tree...")
            self.refresh_concept_tree()

            self.set_status("Caching images...")
            concepts, images = hierarchy(target_concept, True)
            current_previewer_size = str(self._preferences.image_preview_size)
            concepts = [c for c in concepts if c.canonical_name not in self._image_cache[current_previewer_size]]
            images = [i for i in images if i.canonical_name not in self._image_cache[current_previewer_size]]

            total = len(images) + len(concepts) + 1
            for i, image in enumerate(images, start=1):
                pbd.update_progressbar(f"Caching image...", i, total)
                self.set_status(f"Caching image '{image.canonical_name}'...")
                self.load_image(image.canonical_name)

            for i, concept in enumerate(concepts, start=len(images)):
                pbd.update_progressbar(f"Caching image...", i, total)
                self.set_status(f"Caching image '{concept.canonical_name}'...")
                self.load_image(concept.canonical_name)

            self.set_status("Caching image...")
            pbd.update_progressbar("Caching image...", total, total)
            str_size = str(self._preferences.image_preview_size)
            del self._image_cache[str_size][target_concept.canonical_name]
            self.load_image(target_concept.canonical_name)
            self.set_status("Ready")

        fkdiag.show_progress_bar(self._root, do_dnd)
        self.set_selected_datum(target_concept.canonical_name)
        self.open_datum(datum.canonical_name)

    def __bind_status_text(self, widget: tk.Widget, status: str):
        widget_keys = widget.keys()

        def on_enter():
            if "state" in widget_keys:
                c_state = str(widget.cget("state"))
                if c_state in [tk.NORMAL, "readonly"]:
                    self.set_status(status)

            else:
                self.set_status(status)

        def on_leave():
            if self._last_status_temp:
                self.set_status("Ready")
            elif "state" in widget_keys:
                c_state = str(widget.cget("state"))
                if c_state in [tk.NORMAL, "readonly"]:
                    self.set_status(self._last_status)
            else:
                self.set_status(self._last_status)

        widget.bind("<Enter>", lambda e: on_enter())
        widget.bind("<Leave>", lambda e: on_leave())


def get_transparency_image(width: int = 768, height: int = 768) -> Image:
    canvas = PIL.Image.new("RGBA", size=(width, height), color=(0, 0, 0, 1))
    transparent_img = fkutils.get_image_resource("transparent_grid.png")

    ti_width = transparent_img.width
    ti_height = transparent_img.height

    ti_x_repeats = round(width / ti_width)
    ti_y_repeats = round(height / ti_height)

    for x in range(ti_x_repeats):
        for y in range(ti_y_repeats):
            canvas.paste(transparent_img, (x * ti_width, y * ti_height))

    return canvas


def load_image_from_disk(src: str) -> Union[Image, None]:
    if os.path.isfile(src) and fkutils.is_image(src):
        return PIL.Image.open(src)
    else:
        return None


# noinspection PyUnresolvedReferences
def fit_image_to_canvas(
        image: Image,
        canvas_size: int,
        transparency_background: bool = False,
        fixed_to_top: bool = False
) -> Image:
    transparent_canvas: Image = get_transparency_image(canvas_size, canvas_size) if transparency_background \
        else PIL.Image.new("RGBA", size=(canvas_size, canvas_size), color=(0, 0, 0, 0))

    width, height = image.size
    ratio = width / height

    if ratio != 1.0:
        if ratio > 1:
            width = canvas_size
            height = canvas_size / ratio
        else:
            width = canvas_size * ratio
            height = canvas_size

        image = image.resize(size=(int(width), int(height)), resample=PIL.Image.Resampling.LANCZOS)
    elif width != canvas_size:
        image = image.resize(size=(canvas_size, canvas_size), resample=PIL.Image.Resampling.LANCZOS)

    width, height = image.size

    x = (canvas_size / 2) - (width / 2)
    y = 0 if fixed_to_top else (canvas_size / 2) - (height / 2)

    mask = image if image.mode == transparent_canvas.mode else image.convert(transparent_canvas.mode)
    transparent_canvas.paste(image, box=(int(x), int(y)), mask=mask)

    return transparent_canvas


def image_grid(images: List[Image], canvas_size: int) -> Image:
    images_length = len(images)

    rows = round(math.sqrt(images_length))
    cols = math.ceil(images_length / rows)

    w = h = canvas_size
    canvas = PIL.Image.new("RGBA", size=(w * cols, h * rows), color=(0, 0, 0, 0))

    for i, img in enumerate(images):
        canvas.paste(img, box=(i % cols * w, i // cols * h))

    return fit_image_to_canvas(canvas, canvas_size, False, True)


def hierarchy(concept: FkConcept, include_self: bool = False):
    _concepts: List[FkConcept] = [concept] if include_self else []
    _concept_images: List[FkConceptImage] = concept.images[:] if include_self else []

    for child in concept.children:
        _concepts.append(child)
        _concept_images.extend(child.images)

        child_concepts, child_images = hierarchy(child)

        _concepts.extend(child_concepts)
        _concept_images.extend(child_images)

    return _concepts, _concept_images

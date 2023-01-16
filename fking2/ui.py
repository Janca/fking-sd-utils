import os.path
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk as ttk
from typing import Dict, Optional, Union

import PIL
from PIL import ImageTk
from PIL.Image import Image

import fking2.app as fkapp
import fking2.concepts as fkconcepts
import fking2.dialogs as fkdiag
import fking2.utils as fkutils
from fking2.app import FkApp
from fking2.concepts import FkConcept, FkVirtualConcept
from fking2.dataset import FkDataset


class FkFrame:
    _root: tk.Tk
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

        self._menu_file.add_command(label="Save Dataset", underline=True, accelerator="Ctrl+S")

        self._menu_file.add_separator()
        self._menu_file.add_command(label="Flatten Dataset", underline=True, accelerator="Ctrl+L")

        self._menu_file.entryconfig("Save Dataset", state=tk.DISABLED)
        self._menu_file.entryconfig("Flatten Dataset", state=tk.DISABLED)

        self._menu_file.add_separator()
        self._menu_file.add_command(label="Quit", underline=True, accelerator="Ctrl+Q")

        # root.bind_all("<Control-s>", on_menu_item_save)
        # root.bind_all("<Control-l>", on_menu_item_flatten)
        # root.bind_all("<Control-o>", on_menu_item_open)
        # root.bind_all("<Control-q>", on_request_exit)
        #
        # root.protocol("WM_DELETE_WINDOW", on_request_exit)

        ico_img = fkutils.find_image_resource("icon.ico")
        self._root.iconbitmap(ico_img)

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

        self._label_image_preview = ttk.Label(self._frame, padding=(0, 0), borderwidth=1, relief="solid")
        self._label_image_preview.grid(row=0, column=2, sticky="news", padx=(6, 0))

        self._toolbar_concept_tools = tk.Frame(self._frame, borderwidth=1, relief=tk.FLAT)
        self._toolbar_concept_tools.grid(row=1, column=0, sticky="news", pady=(6, 0))

        self._new_concept_ico = fkutils.get_photo_image_resource("folder-new.png")
        self._button_concept_tree_new_concept = tk.Button(self._toolbar_concept_tools, image=self._new_concept_ico,
                                                          height=24, width=24, relief="flat",
                                                          command=self.__on_button_new_concept)

        self._new_image_ico = fkutils.get_photo_image_resource("insert-image.png")
        self._button_concept_tree_new_image = tk.Button(self._toolbar_concept_tools, image=self._new_image_ico,
                                                        height=24, width=24, relief="flat",
                                                        command=self.__on_button_dnd_zone)

        self._edit_ico = fkutils.get_photo_image_resource("edit-rename.png")
        self._button_concept_tree_edit = tk.Button(self._toolbar_concept_tools, image=self._edit_ico,
                                                   height=24, width=24, relief="flat")

        self._refresh_ico = fkutils.get_photo_image_resource("refresh.png")

        self._button_concept_tree_refresh = tk.Button(self._toolbar_concept_tools, image=self._refresh_ico,
                                                      height=24, width=24, relief="flat")

        self._button_concept_tree_new_concept.pack(side=tk.LEFT)
        self._button_concept_tree_new_image.pack(side=tk.LEFT)
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
            [self._button_concept_tree_new_image, "Add images to selected concept"],
            [self._button_concept_tree_edit, "Edit selected concept"],
            [self._button_concept_tree_refresh, "Refresh concept tree"],
            [self._button_tag_editor_paste, "Paste tags from previously selected datum"],
            [self._button_tag_editor_apply, "Apply tags to selected datum"],
            [self._button_tag_editor_next, "Apply tags and go to next datum"],
            [self._button_tag_editor_previous, "Apply tags and go to previous datum"],
            [self._combobox_preview_size, "Set previewer size"],
            [self._treeview_concepts, "Concept tree"],

            [self._menu_file, "File menu"]
        ]

        for widget, status_text in widgets:
            self.__bind_status_text(widget, status_text)

    def set_status(self, status: str, temp=False):
        if not self._last_status_temp:
            self._last_status = self._current_status.get()
        self._last_status_temp = temp
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
        self._button_concept_tree_new_image.configure(state=state)
        self._button_concept_tree_edit.configure(state=state)
        self._button_concept_tree_refresh.configure(state=state)

        self._button_tag_editor_paste.configure(state=state)
        self._button_tag_editor_apply.configure(state=state)
        self._button_tag_editor_next.configure(state=state)
        self._button_tag_editor_previous.configure(state=state)

        self._textfield_tags.configure(state=state)

    def set_concept_tools_ui_state(self, state: Union[tk.NORMAL, tk.DISABLED]):
        self._button_concept_tree_new_concept.configure(state=state)
        self._button_concept_tree_new_image.configure(state=state)
        self._button_concept_tree_edit.configure(state=state)

        self._button_tag_editor_paste.configure(state=state)
        self._button_tag_editor_apply.configure(state=state)
        self._button_tag_editor_next.configure(state=state)
        self._button_tag_editor_previous.configure(state=state)

        self._textfield_tags.configure(state=state)

    def refresh_concept_tree(self):
        dataset = self._dataset
        if dataset is None:
            return

        self._treeview_concepts.delete(*self._treeview_concepts.get_children())

        datum_keys = dataset.keys()

        for key in datum_keys:
            datum = dataset.get(key)
            parent_concept: Optional[FkConcept] = None
            if isinstance(datum, FkDataset.WorkingConcept):
                parent_concept = datum.concept.parent
            elif isinstance(datum, FkDataset.WorkingImage):
                parent_concept = datum.concept

            self._treeview_concepts.insert(
                    '' if parent_concept is None else parent_concept.canonical_name,
                    tk.END,
                    datum.canonical_name,
                    text=datum.name
            )

        self._menu_file.entryconfig("Flatten Dataset", state=tk.NORMAL)
        self._menu_file.entryconfig("Save Dataset", state=tk.NORMAL)

    def refresh_image_preview(self):
        if self._active_datum is None:
            self.clear_image_preview()
        else:
            image = self.load_image(self._active_datum.canonical_name)
            if image is None:
                return

            self._active_image = image
            self._active_preview_image = ImageTk.PhotoImage(self._active_image)
            self._label_image_preview.configure(image=self._active_preview_image)

    def open_datum(self, canonical_name: str):
        self._treeview_concepts.selection_clear()
        self._treeview_concepts.selection_set(canonical_name)
        self._treeview_concepts.focus(canonical_name)

        concept = self._dataset.get(canonical_name).concept

        while concept is not None:
            iid = concept.canonical_name
            self._treeview_concepts.item(iid, open=True)
            concept = concept.parent

    def set_selected_datum(self, canonical_name: str):
        dataset = self._dataset
        datum = dataset.get(canonical_name)
        if datum is None:
            return

        self._active_datum = datum
        tag, parent_tags = dataset.get_tags(datum.canonical_name)

        self.set_concept_tools_ui_state(tk.NORMAL)
        self.set_textfield_tags(tag, parent_tags)

        self.refresh_image_preview()
        self.set_datum_info(datum)

    def clear_image_preview(self):
        transparent_image = get_transparency_image(
                self._app.preferences.image_preview_size,
                self._app.preferences.image_preview_size
        )

        self._image_transparent_image = ImageTk.PhotoImage(transparent_image)
        self._label_image_preview.configure(image=self._image_transparent_image)

    def load_image(self, canonical_name: str) -> Union[Image, None]:
        datum = self._dataset.get(canonical_name)
        if datum is None:
            return None

        target_size = self._preferences.image_preview_size
        str_target_size = str(target_size)

        if str_target_size in self._image_cache:
            if canonical_name in self._image_cache[str_target_size]:
                return self._image_cache[str_target_size][canonical_name]

        if isinstance(datum, FkDataset.WorkingConcept):
            print("This is a concept...TODO later")
            pass
        elif isinstance(datum, FkDataset.WorkingImage):
            image_path = datum.image.file_path
            image = load_image_from_disk(image_path)

            datum.set_meta("image_dimensions", (image.width, image.height))

            return fit_image_to_canvas(image, target_size)
        else:
            raise ValueError(f"from unexpected datum type: '{type(datum)}'")

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

    def __on_menu_item_new_dataset(self):
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

    def __on_menu_item_open_dataset(self):
        self.set_status("Opening dataset...", True)
        dataset_directory = tkinter.filedialog.askdirectory(parent=self._root, title="Open Dataset Directory")

        if not dataset_directory:
            self.set_status(self._last_status)
            return

        root_concept = fkconcepts.build_concept_tree(dataset_directory)
        dataset = FkDataset(root_concept)

        self._app.set_working_dataset(dataset)
        self.refresh_concept_tree()

        self.open_datum(root_concept.canonical_name)
        self.set_status(f"Opened dataset '{root_concept.name}'", True)

    def __on_button_new_concept(self):
        datum_selection = self._current_tree_selection
        if datum_selection is None:
            return

        selected_datum = self._dataset.get(datum_selection)
        if selected_datum is None:
            return

        target_concept = selected_datum.concept

        name, tags = fkdiag.create_new_concept(self._root)
        virtual_concept = FkVirtualConcept(target_concept, name, tags)
        target_concept.add_child(virtual_concept)

        self._dataset.refresh()
        self.refresh_concept_tree()

        self.open_datum(virtual_concept.canonical_name)

    def __on_button_dnd_zone(self):
        fkdiag.drag_and_drop(self._root)

    def __on_combobox_preview_size(self, event):
        selected_value = event.widget.get()[1:]
        selected_int_value = int(selected_value[:-2])
        current_size = self._app.preferences.image_preview_size
        current_sel = self._combobox_preview_size.current()

        if selected_int_value != current_size:
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

            self.__init_grid()

            self.refresh_image_preview()

            self._root.geometry(f"+{x}+{y}")
            self._root.focus()

    def __on_treeview_concept_item_selected(self, event=None):
        treeview_selection = self._current_tree_selection
        if treeview_selection is None:
            return

        self.set_selected_datum(treeview_selection)

    def __bind_status_text(self, widget: tk.Misc, status: str):
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
    if os.path.exists(src) and fkutils.is_image(src):
        return PIL.Image.open(src)
    else:
        return None


def fit_image_to_canvas(image: Image, canvas_size: int) -> Image:
    transparent_canvas = get_transparency_image(canvas_size, canvas_size)

    width = image.width
    height = image.height

    ratio = float(width) / float(height)
    print(width, height, ratio)

    if ratio == 1.0:
        if width == canvas_size:
            transparent_canvas.paste(image, box=(0, 0))
        if width < canvas_size:
            image = image.resize(size=(canvas_size, canvas_size), resample=PIL.Image.Resampling.LANCZOS)
            transparent_canvas.paste(image, box=(0, 0))
    else:
        if width < height:
            height_ratio = float(canvas_size / height)
            target_height = round(height * height_ratio)
            target_width = round(width * height_ratio)
        else:
            width_ratio = float(canvas_size / width)
            target_width = round(width * width_ratio)
            target_height = round(height * width_ratio)

        half_size = canvas_size / 2

        x = round(half_size - (target_width / 2))
        y = round(half_size - (target_height / 2))

        image = image.resize(size=(target_width, target_height))
        transparent_canvas.paste(image, box=(x, y))

    return transparent_canvas

import os
import sys
import tkinter as tk
import tkinter.ttk as ttk

import fking2.app as fkapp
from fking2.app import FkApp


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

    _label_image_preview: tk.Label

    _textfield_parent_tags: tk.Text
    _textfield_tags: tk.Text

    _toolbar_concept_tools: tk.Frame

    def __init__(self, app: FkApp):
        super().__init__()
        self._app = app

        self.__init_frame()
        self.__init_grid()
        self.__init_components()

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

        self._menu_file.add_command(label="Open Dataset", underline=True, accelerator="Ctrl+O")
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

        ico_img = load_ico("icon.ico")
        self._root.iconbitmap(ico_img)

    def __init_grid(self):
        # PREVIEW IMAGE
        self._frame.grid_rowconfigure(0, minsize=self._app.preferences.image_preview_size - 30, weight=1)
        # BOTTOM TOOLBAR
        self._frame.grid_rowconfigure(1, minsize=24 + 6, weight=1)
        # TAG EDITOR
        self._frame.grid_rowconfigure(2, weight=0)

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

        self._label_image_preview = ttk.Label(self._frame, padding=(0, 0), borderwidth=1, relief="solid")
        self._label_image_preview.grid(row=0, rowspan=2, column=2, sticky="news", padx=(6, 0))

        self._toolbar_concept_tools = tk.Frame(self._frame, borderwidth=1, relief=tk.FLAT)
        self._toolbar_concept_tools.grid(row=1, column=0, sticky="news", pady=(6, 0))

        self._new_concept_ico = get_ico("new-folder.png")
        self._button_concept_tree_new_concept = tk.Button(self._toolbar_concept_tools, image=self._new_concept_ico,
                                                          height=24, width=24, relief="flat")

        self._new_image_ico = get_ico("new-image.png")
        self._button_concept_tree_new_image = tk.Button(self._toolbar_concept_tools, image=self._new_image_ico,
                                                        height=24, width=24, relief="flat")

        self._edit_ico = get_ico("edit.png")
        self._button_concept_tree_edit = tk.Button(self._toolbar_concept_tools, image=self._edit_ico,
                                                   height=24, width=24, relief="flat")

        self._refresh_ico = get_ico("refresh.png")
        self._button_concept_tree_refresh = tk.Button(self._toolbar_concept_tools, image=self._refresh_ico,
                                                      height=24, width=24, relief="flat")

        self._button_concept_tree_new_concept.pack(side=tk.LEFT)
        self._button_concept_tree_new_image.pack(side=tk.LEFT)
        self._button_concept_tree_refresh.pack(side=tk.RIGHT)
        self._button_concept_tree_edit.pack(side=tk.RIGHT)

        frame_tag_editor = tk.Frame(self._frame)
        frame_tag_editor.grid(row=2, column=0, columnspan=3, sticky="news", pady=(6, 0))

        frame_tag_editor.grid_rowconfigure(0, weight=0)
        frame_tag_editor.grid_rowconfigure(1, weight=0)

        frame_tag_editor.grid_columnconfigure(0, weight=1)
        frame_tag_editor.grid_columnconfigure(1, minsize=148, weight=0)

        self._textfield_parent_tags = tk.Text(frame_tag_editor, height=4, wrap=tk.WORD)
        self._textfield_parent_tags.grid(row=0, column=0, columnspan=2, sticky="news")

        self._textfield_tags = tk.Text(frame_tag_editor, height=6, wrap=tk.WORD)
        self._textfield_tags.grid(row=1, column=0, sticky="news", pady=(6, 0))

        frame_tag_editor_actions = tk.Frame(frame_tag_editor)
        frame_tag_editor_actions.grid(row=1, column=1, sticky="news", padx=(6, 0), pady=(6, 0))

        frame_tag_editor_actions.grid_rowconfigure(0, weight=0)
        frame_tag_editor_actions.grid_rowconfigure(1, weight=0)
        frame_tag_editor_actions.grid_rowconfigure(2, weight=0)

        frame_tag_editor_actions.grid_columnconfigure(0, weight=0)
        frame_tag_editor_actions.grid_columnconfigure(1, weight=0)

        self._paste_ico = get_ico("paste.png")
        self._previous_ico = get_ico("left.png")
        self._next_ico = get_ico("right.png")

        self._button_tag_editor_paste = tk.Button(frame_tag_editor_actions, compound=tk.LEFT,
                                                  image=self._paste_ico, text="Paste", padx=3)

        self._button_tag_editor_apply = tk.Button(frame_tag_editor_actions, text="Apply")

        self._button_tag_editor_previous = tk.Button(frame_tag_editor_actions, compound=tk.LEFT, height=20,
                                                     image=self._previous_ico, padx=3)

        self._button_tag_editor_next = tk.Button(frame_tag_editor_actions, compound=tk.RIGHT, height=20,
                                                 image=self._next_ico, padx=3)

        self._button_tag_editor_paste.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._button_tag_editor_apply.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._button_tag_editor_previous.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._button_tag_editor_next.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def show(self):
        self._root.overrideredirect(False)
        self._root.deiconify()

        self.set_title()
        self._root.mainloop()

    def set_title(self, fragment: str = None):
        if fragment is None:
            self.set_title("a fking hierarchical dataset editor")
        else:
            modified = self._app.working_dataset is not None and self._app.working_dataset.modified
            modified_star = '*' if modified else ''
            version = f"v{fkapp.version}"
            self._root.title(f"{modified_star}fking captioner {version} - {fragment}")


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

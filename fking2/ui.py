import os
import sys
import tkinter as tk
import tkinter.ttk as ttk

from fking2.app import FkApp


class FkFrame(tk.Tk):
    menubar: tk.Menu
    menu_file: tk.Menu

    treeview_concepts: ttk.Treeview
    label_image_preview: tk.Label

    textfield_parent_tags: tk.Text
    textfield_tags: tk.Text

    def __init__(self, app: FkApp):
        super().__init__()
        self.app = app

        self.__init_frame()
        self.__init_grid()
        self.__init_components()

    def __init_frame(self):
        self.resizable(False, False)
        self.option_add('*tearOff', False)

        def init_menubar():
            self.menubar = tk.Menu(self)
            self.config(menu=self.menubar)

            self.menu_file = tk.Menu(self.menubar)
            self.menubar.add_cascade(label="File", menu=self.menu_file)

            self.menu_file.add_command(label="Open Dataset", underline=True, accelerator="Ctrl+O")
            self.menu_file.add_command(label="Save Dataset", underline=True, accelerator="Ctrl+S")

            self.menu_file.add_separator()
            self.menu_file.add_command(label="Flatten Dataset", underline=True, accelerator="Ctrl+L")

            self.menu_file.entryconfig("Save Dataset", state=tk.DISABLED)
            self.menu_file.entryconfig("Flatten Dataset", state=tk.DISABLED)

            self.menu_file.add_separator()
            self.menu_file.add_command(label="Quit", underline=True, accelerator="Ctrl+Q")

            # root.bind_all("<Control-s>", on_menu_item_save)
            # root.bind_all("<Control-l>", on_menu_item_flatten)
            # root.bind_all("<Control-o>", on_menu_item_open)
            # root.bind_all("<Control-q>", on_request_exit)
            #
            # root.protocol("WM_DELETE_WINDOW", on_request_exit)

        def init_frame_icon():
            ico_img = "icon.ico"
            if not hasattr(sys, "frozen"):
                ico_img = os.path.join(os.path.dirname(__file__), ico_img)
            else:
                ico_img = os.path.join(sys.prefix, ico_img)
            self.iconbitmap(ico_img)

        init_menubar()
        init_frame_icon()

    def __init_grid(self):
        pass

    def __init_components(self):
        pass

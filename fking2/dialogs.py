import os.path
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from tkinter import simpledialog
from typing import Optional

import tkinterdnd2

import fking2.app as fkapp
import fking2.utils as fkutils


class _NewDatasetDialog(simpledialog.Dialog):
    _textfield_dataset_name: tk.Text
    _textfield_dataset_working_path: tk.Text
    _textfield_dataset_prompt: tk.Text

    _str_variable_dataset_working_path: tk.StringVar
    _button_browse_directory: tk.Button

    _button_ok: tk.Button
    _button_cancel: tk.Button
    _ico_browse: tk.PhotoImage

    name: Optional[str] = None
    working_directory: Optional[str] = None
    root_tags: Optional[list[str]] = None
    _working_directory: Optional[str] = None

    def body(self, master: tk.Frame):
        self.resizable(False, False)

        img_ico = fkutils.find_image_resource("icon.ico")
        self.iconbitmap(img_ico)
        self.title(f"fking captioner v{fkapp.version} - Create Dataset")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, minsize=24, weight=0)

        frame_textfield_dataset_name, self._textfield_dataset_name = fkutils.border_widget(
                master,
                lambda tkf: tk.Text(tkf, width=32, height=1, relief=tk.FLAT, wrap=tk.NONE)
        )

        frame_textfield_dataset_working_path, self._textfield_dataset_working_path = fkutils.border_widget(
                master,
                lambda tkf: tk.Text(tkf, width=32, height=1, relief=tk.FLAT, wrap=tk.NONE)
        )

        tk.Label(
                master,
                text="Dataset Name",
                anchor=tk.W,
                justify=tk.LEFT
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W)

        frame_textfield_dataset_name.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

        # tk.Label(
        #     master,
        #     text="Save Directory",
        #     anchor=tk.W,
        #     justify=tk.LEFT
        # ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        # frame_textfield_dataset_working_path.grid(row=3, column=0, sticky=tk.W)

        self._textfield_dataset_working_path.configure(state=tk.DISABLED)

        self._ico_browse = fkutils.get_photo_image_resource("folder.png")
        self._button_browse_directory = tk.Button(master, command=self.__on_button_browse, height=24, width=24,
                                                  relief="flat",
                                                  overrelief="flat", compound=tk.LEFT, image=self._ico_browse, padx=3)

        # self._button_browse_directory.grid(row=3, column=1, padx=(3, 0))

        tk.Label(
                master,
                text="Dataset Prompt (Optional)",
                anchor=tk.W,
                justify=tk.LEFT
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(3, 0))

        frame_textfield_dataset_prompt, self._textfield_dataset_prompt = fkutils.border_widget(
                master,
                lambda tkf: tk.Text(tkf, width=32, height=4, wrap=tk.WORD, relief=tk.FLAT)
        )

        frame_textfield_dataset_prompt.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)

        return self._textfield_dataset_name

    def buttonbox(self):
        frame = tk.Frame(self, padx=0, pady=0)

        self._button_ok = tk.Button(frame, text="OK", width=16, command=self.__on_ok_button)
        self._button_ok.grid(row=0, column=1, padx=(3, 0), pady=(0, 6))

        self._button_cancel = tk.Button(frame, text="Cancel", width=10, command=self.__on_cancel_button)
        self._button_cancel.grid(row=0, column=0, pady=(0, 6))

        frame.pack(side=tk.RIGHT, padx=6, pady=0)

        def move_focus(target: tk.Misc):
            target.focus()
            return "break"

        self._textfield_dataset_name.bind("<Tab>", lambda e: move_focus(self._textfield_dataset_prompt))
        self._textfield_dataset_prompt.bind("<Tab>", lambda e: move_focus(self._button_ok))
        self._button_ok.bind("<Tab>", lambda e: move_focus(self._button_cancel))
        self._button_cancel.bind("<Tab>", lambda e: move_focus(self._textfield_dataset_name))

    def __on_ok_button(self):
        textfield_name = self._textfield_dataset_name.get(1.0, tk.END).strip()
        textfield_name_len = len(textfield_name)

        if textfield_name_len <= 0:
            tkinter.messagebox.showerror(title="Invalid Dataset Name",
                                         message="Please input a valid dataset name.")
        else:
            self.name = textfield_name.replace(" ", "_").lower()
            # self.working_directory = self._working_directory.strip()

            textfield_tags = self._textfield_dataset_prompt.get(1.0, tk.END).strip().split(',')
            tags = fkutils.normalize_tags(textfield_tags)
            self.root_tags = tags

            self.destroy()

    def __on_cancel_button(self):
        self.name = None
        self.working_directory = None
        self._working_directory = None
        self.root_tags = None

        self.destroy()

    def __on_button_browse(self):
        target_directory = tkinter.filedialog.askdirectory()
        if len(target_directory) <= 0:
            self._working_directory = None
            return

        abs_directory = os.path.abspath(target_directory)

        self._textfield_dataset_working_path.configure(state=tk.NORMAL)
        self._textfield_dataset_working_path.delete(1.0, tk.END)
        self._textfield_dataset_working_path.insert(tk.END, abs_directory)
        self._textfield_dataset_working_path.configure(state=tk.DISABLED)

        self._working_directory = abs_directory
        if len(os.listdir(abs_directory)) > 0:
            return

        textfield_name = self._textfield_dataset_name.get(1.0, tk.END).strip()
        if len(textfield_name) <= 0:
            directory_name = os.path.basename(abs_directory)
            self._textfield_dataset_name.insert(tk.END, directory_name)


class _NewConceptDialog(simpledialog.Dialog):
    _textfield_concept_name: tk.Text
    _textfield_concept_tags: tk.Text

    name: str = None
    tags: list[str] = None

    _button_ok: tk.Button
    _button_cancel: tk.Button

    def body(self, master):
        self.resizable(False, False)

        img_ico = fkutils.find_image_resource("icon.ico")
        self.iconbitmap(img_ico)
        self.title(f"fking captioner v{fkapp.version} - Create Concept")

        tk.Label(master, text="Concept Name", anchor=tk.W, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        self.grid_columnconfigure(0, minsize=196, weight=0)
        self.grid_columnconfigure(1, weight=0)

        frame_textfield_concept_name, self._textfield_concept_name = fkutils.border_widget(
                master,
                lambda tkf: tk.Text(tkf, height=1, width=48)
        )

        frame_textfield_concept_name.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

        tk.Label(
                master,
                text="Concept Tags",
                anchor=tk.W,
                justify=tk.LEFT
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        frame_textfield_concept_tags, self._textfield_concept_tags = fkutils.border_widget(
                master,
                lambda tkf: tk.Text(tkf, height=6, width=48)
        )

        self._textfield_concept_tags.insert(tk.END, "__folder__")
        frame_textfield_concept_tags.grid(row=3, column=0, sticky=tk.NSEW)

        scrollbar_textfield_concept_tags = tk.Scrollbar(master, orient=tk.VERTICAL,
                                                        command=self._textfield_concept_tags.yview)

        self._textfield_concept_tags.config(yscrollcommand=scrollbar_textfield_concept_tags.set)

        scrollbar_textfield_concept_tags.grid(row=3, column=1, sticky=tk.NSEW)

        return self._textfield_concept_name

    def buttonbox(self):
        frame = tk.Frame(self, padx=0, pady=0)

        self._button_ok = tk.Button(frame, text="OK", width=16, command=self.__on_ok_button)
        self._button_ok.grid(row=0, column=1, padx=(3, 0), pady=(0, 6))

        self._button_cancel = tk.Button(frame, text="Cancel", width=10, command=self.__on_cancel_button)
        self._button_cancel.grid(row=0, column=0, pady=(0, 6))

        frame.pack(side=tk.RIGHT, padx=6, pady=0)

    def __on_ok_button(self):
        textfield_name = self._textfield_concept_name.get(1.0, tk.END)
        textfield_tags = self._textfield_concept_tags.get(1.0, tk.END).split(',')

        self.name = textfield_name.strip()
        self.tags = fkutils.normalize_tags(textfield_tags)

        self.destroy()

    def __on_cancel_button(self):
        self.destroy()


class _ConceptImageDropZoneDialog(simpledialog.Dialog):
    _button_ok: tk.Button
    _button_cancel: tk.Button

    _drop_ico: tk.PhotoImage
    _label_dnd_zone: tk.Label
    _label_image_count: tk.Label

    _image_count: tk.StringVar

    _images: list[str] = []
    images: list[str] = None

    # noinspection PyUnresolvedReferences
    def body(self, master):
        # noinspection PyProtectedMember
        tkinterdnd2.TkinterDnD._require(self)
        self.resizable(False, False)

        tk.Label(master, text="Concept Name", anchor=tk.W, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        self.grid_columnconfigure(0, minsize=196, weight=0)

        img_ico = fkutils.find_image_resource("icon.ico")
        self.iconbitmap(img_ico)
        self.title(f"fking captioner v{fkapp.version} - Drop Images")

        frame_dnd_zone = tk.Frame(master, background="#a0a0a0", padx=1, pady=1)

        self._drop_ico = fkutils.get_photo_image_resource("drop.png")
        self._label_dnd_zone = tk.Label(frame_dnd_zone, width=256, height=256, image=self._drop_ico,
                                        text="Drop Image(s)", compound=tk.CENTER)

        self._label_dnd_zone.drop_target_register(tkinterdnd2.DND_FILES)
        self._label_dnd_zone.dnd_bind('<<Drop>>', self.on_drop_zone)

        self._label_dnd_zone.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        frame_dnd_zone.grid(row=0, column=0)

        self._image_count = tk.StringVar()
        self._image_count.set("Image Count: 0")

        self._label_image_count = tk.Label(master, textvariable=self._image_count, anchor=tk.E, justify=tk.RIGHT)
        self._label_image_count.grid(row=1, column=0, sticky=tk.E)

    def on_drop_zone(self, event):
        def find_images(path: str) -> list[str]:
            if os.path.isfile(path) and fkutils.is_image(path):
                return [path]

            if os.path.isdir(path):
                images: list[str] = []

                for filename in os.listdir(path):
                    images.extend(find_images(os.path.join(path, filename)))

                return images

            return []

        files = self.tk.splitlist(event.data)
        for file in files:
            if fkutils.is_image(file):
                self._images.append(file)
            else:
                c_images = find_images(file)
                self._images.extend(c_images)

        img_count = len(self._images)
        self._image_count.set(f"Image Count: {img_count}")

    def buttonbox(self):
        frame = tk.Frame(self, padx=0, pady=0)

        self._button_ok = tk.Button(frame, text="OK", width=16, command=self.__on_ok_button)
        self._button_ok.grid(row=0, column=1, padx=(3, 0), pady=(0, 6))

        self._button_cancel = tk.Button(frame, text="Cancel", width=10, command=self.__on_cancel_button)
        self._button_cancel.grid(row=0, column=0, pady=(0, 6))

        frame.pack(side=tk.RIGHT, padx=6, pady=0)

    def __on_ok_button(self):
        self.images = self._images[:]
        self.destroy()

    def __on_cancel_button(self):
        self._images.clear()
        self._image_count.set("Image Count: 0")

        self.destroy()


def create_new_dataset(root: tk.Tk):
    ndd = _NewDatasetDialog(root)
    return ndd.name, ndd.root_tags


def create_new_concept(root: tk.Tk):
    ncd = _NewConceptDialog(root)
    return ncd.name, ncd.tags


def drag_and_drop(root: tk.Tk):
    dnd = _ConceptImageDropZoneDialog(root)
    return dnd.images

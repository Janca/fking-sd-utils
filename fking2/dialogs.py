from __future__ import annotations

import os.path
import threading
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk as ttk
from tkinter import simpledialog
from typing import Optional, Union, Callable

import tkinterdnd2

import fking2.app as fkapp
import fking2.utils as fkutils
from fking2.concepts import FkConcept
from fking2.dataset import FkDataset


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

        fkutils.setup_tab_focus(
            self._textfield_dataset_name,
            self._textfield_dataset_prompt,
            self._button_ok,
            self._button_cancel
        )

        fkutils.setup_bind(
            "<Return>", self.__on_ok_button, True,
            self._textfield_dataset_name,
            self._textfield_dataset_prompt,
            self._button_ok
        )

    def __on_ok_button(self):
        textfield_name = self._textfield_dataset_name.get(1.0, tk.END).strip()
        textfield_name_len = len(textfield_name)

        if textfield_name_len <= 0:
            tkinter.messagebox.showerror(
                title="Invalid Dataset Name",
                message="Please input a valid dataset name."
            )
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

    def __init__(self, parent: tk.Misc, dataset: FkDataset, concept: FkConcept) -> None:
        self._dataset = dataset
        self._concept = concept
        super().__init__(parent)

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

        fkutils.setup_tab_focus(
            self._textfield_concept_name,
            self._textfield_concept_tags,
            self._button_ok,
            self._button_cancel
        )

        fkutils.setup_bind(
            "<Return>",
            self.__on_ok_button,
            True,
            self._textfield_concept_name,
            self._textfield_concept_tags,
            self._button_ok
        )

    def __on_ok_button(self):
        textfield_name = self._textfield_concept_name.get(1.0, tk.END).strip()
        if textfield_name is None or len(textfield_name) <= 0:
            return

        name = textfield_name.replace(' ', '_').lower()
        canonical_name = f"{self._concept.canonical_name}.{name}"
        existing_datum = self._dataset.contains(canonical_name)
        if existing_datum:
            tkinter.messagebox.showerror(
                title="Concept Exists",
                message=f"A concept with the name '{textfield_name}' exists."
            )

            return

        textfield_tags = self._textfield_concept_tags.get(1.0, tk.END).split(',')

        self.name = textfield_name
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
            if os.path.isfile(file) and fkutils.is_image(file):
                self._images.append(file)
            elif os.path.isdir(file):
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


class _ProgressDialog(simpledialog.Dialog):
    _button_ok: tk.Button
    _button_cancel: tk.Button

    _progressbar: ttk.Progressbar
    _progress_status_text: tk.StringVar
    _progress_steps_text: tk.StringVar

    thread: threading.Thread

    def __init__(self, parent: Union[tk.Misc, None], *args: Callable[[_ProgressDialog], None]) -> None:
        self._tasks = args

        super().__init__(parent)

    def body(self, master: tk.Frame):
        self.resizable(False, False)
        self.overrideredirect(True)

        master.configure(borderwidth=1, relief=tk.FLAT, background="#a0a0a0")
        frame = tk.Frame(master, borderwidth=16, relief=tk.FLAT)
        frame.pack()

        self._progress_status_text = tk.StringVar(frame)
        tk.Label(frame, textvariable=self._progress_status_text,
                 justify=tk.LEFT, anchor=tk.W).grid(row=0, column=0, sticky=tk.W)

        self._progress_steps_text = tk.StringVar(frame)
        tk.Label(frame, textvariable=self._progress_steps_text,
                 justify=tk.RIGHT, anchor=tk.E).grid(row=0, column=1, sticky=tk.E)

        self._progressbar = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=296, mode="indeterminate")
        self._progressbar.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, pady=(3, 0))

        self.thread = threading.Thread(target=self.next)
        self.thread.start()

        self.monitor()

    def buttonbox(self):
        pass

    def next(self):
        for task in self._tasks:
            task(self)

    def monitor(self):
        if self.thread.is_alive():
            self.after(100, self.monitor)
            return

        self.destroy()

    def update_progressbar(self, message: str, value: int = -1, max_value: int = -1):
        self._progress_status_text.set(message)

        if max_value > 0:
            self._progressbar["mode"] = "determinate"
            self._progressbar["value"] = max(0, value)
            self._progressbar["maximum"] = max_value

            if value >= max_value:
                self._progressbar.stop()

            self._progress_steps_text.set(f"{value:,}/{max_value:,}")
        else:
            self._progressbar["value"] = 0
            self._progressbar["maximum"] = 100
            self._progressbar["mode"] = "indeterminate"
            self._progressbar.start()


def create_new_dataset(root: tk.Tk):
    ndd = _NewDatasetDialog(root)
    return ndd.name, ndd.root_tags


def create_new_concept(root: tk.Tk, dataset: FkDataset, concept: FkConcept):
    ncd = _NewConceptDialog(root, dataset, concept)
    return ncd.name, ncd.tags


def drag_and_drop(root: tk.Tk):
    dnd = _ConceptImageDropZoneDialog(root)
    return dnd.images


def show_progress_bar(root: tk.Tk, *args: Callable[[_ProgressDialog], None]):
    _ProgressDialog(root, *args)

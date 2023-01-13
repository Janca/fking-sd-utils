import os.path
import tkinter as tk
from tkinter import simpledialog

import tkinterdnd2

import fking2.app as fkapp
import fking2.utils as fkutils


class _NewConceptDialog(simpledialog.Dialog):
    textfield_concept_name: tk.Text
    textfield_concept_tags: tk.Text

    name: str = None
    tags: list[str] = None

    _button_ok: tk.Button
    _button_cancel: tk.Button

    def body(self, master):
        self.resizable(False, False)

        tk.Label(master, text="Concept Name", anchor=tk.W, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        self.grid_columnconfigure(0, minsize=196, weight=0)
        self.grid_columnconfigure(1, weight=0)

        img_ico = fkutils.load_ico("icon.ico")
        self.iconbitmap(img_ico)
        self.title(f"fking captioner v{fkapp.version} - Create Concept")

        self.textfield_concept_name = tk.Text(master, height=1, width=48)
        self.textfield_concept_name.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

        tk.Label(master, text="Concept Tags", anchor=tk.W, justify=tk.LEFT).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(6, 0)
        )

        self.textfield_concept_tags = tk.Text(master, height=6, width=48)
        self.textfield_concept_tags.insert(tk.END, "__folder__")
        self.textfield_concept_tags.grid(row=3, column=0, sticky=tk.NSEW)

        scrollbar_textfield_concept_tags = tk.Scrollbar(master, orient=tk.VERTICAL,
                                                        command=self.textfield_concept_tags.yview)

        self.textfield_concept_tags.config(yscrollcommand=scrollbar_textfield_concept_tags.set)

        scrollbar_textfield_concept_tags.grid(row=3, column=1, sticky=tk.NSEW)

        return self.textfield_concept_name

    def buttonbox(self):
        frame = tk.Frame(self, padx=0, pady=0)

        self._button_ok = tk.Button(frame, text="OK", width=16, command=self.__on_ok_button)
        self._button_ok.grid(row=0, column=1, padx=(3, 0), pady=(0, 6))

        self._button_cancel = tk.Button(frame, text="Cancel", width=10, command=self.__on_cancel_button)
        self._button_cancel.grid(row=0, column=0, pady=(0, 6))

        frame.pack(side=tk.RIGHT, padx=6, pady=0)

    def __on_ok_button(self):
        textfield_name = self.textfield_concept_name.get(1.0, tk.END)
        textfield_tags = self.textfield_concept_tags.get(1.0, tk.END).split(',')

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

        img_ico = fkutils.load_ico("icon.ico")
        self.iconbitmap(img_ico)
        self.title(f"fking captioner v{fkapp.version} - Drop Images")

        frame_dnd_zone = tk.Frame(master, background="#a0a0a0", padx=1, pady=1)

        self._drop_ico = fkutils.get_ico("drop.png")
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


def create_new_concept(root: tk.Tk):
    ncd = _NewConceptDialog(root)
    return ncd.name, ncd.tags


def drag_and_drop(root: tk.Tk):
    dnd = _ConceptImageDropZoneDialog(root)
    return dnd.images

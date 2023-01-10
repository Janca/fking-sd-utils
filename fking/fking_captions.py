import os
import shutil
import textwrap

from fking.fking_utils import merge_special_tags, read_special_tags_from_file, read_tags_from_file, \
    find_and_replace_special_tags, normalize_tags, sha256_file_hash, write_tags


class FkingImage:
    def __init__(self, concept, path: str, tags: list[str]):
        self.concept = concept
        self.path = path
        self.tags = tags

    def get_filename(self, part: 0 | 1 | -1 = -1) -> str:
        if part == -1:
            return os.path.basename(self.path)
        else:
            return os.path.splitext(os.path.basename(self.path))[part]

    def get_canonical_name(self) -> str:
        return f"{self.concept.canonical_name}.{self.get_filename()}"


class CaptionedImage(FkingImage):
    def __init__(self, concept, path: str, tags: list[str]):
        super().__init__(concept, path, tags)


class ConceptImage(FkingImage):
    def __init__(self, concept, path, tags: list[str] = []) -> None:
        super().__init__(concept, path, tags)

    def generate_tags(self):
        c_tags = self.tags[:]

        parent: Concept = self.concept
        while parent is not None:
            p_tags = parent.concept_tags[:]
            p_tags.reverse()

            c_tags.extend(p_tags)
            parent = parent.parent

        u_tags = []
        for t in c_tags:
            t = t.strip()
            if t not in u_tags:
                u_tags.append(t)

        u_tags.reverse()
        return u_tags

    def build(self) -> tuple[str, list[str]]:
        tags = self.generate_tags()
        return self.path, normalize_tags(tags)


class Concept:
    """
    :type name: str
    :type working_directory: str
    :type concept_tags: list[str]
    :type parent: Concept|None
    """

    def __init__(self, name: str, working_directory: str, parent=None) -> None:
        self.name = name
        self.parent = parent
        self.working_directory = working_directory

        tags_file_path = os.path.join(working_directory, "__prompt.txt")

        self.raw_tags = read_tags_from_file(tags_file_path)
        self.concept_tags = self.raw_tags[:]

        self.concept_tags = [
            t if '__folder__' not in t else t.replace('__folder__', self.name.replace('_', ' '))
            for t in self.raw_tags
        ]

        print(f"CONCEPT TAGS FOR {name}; {(','.join(self.concept_tags))}")

        for t in self.concept_tags:
            if t.startswith("__") and not t.endswith("__"):
                print(f"\nWARNING: You have an incomplete special tag '{t}' in prompt file '{tags_file_path}'.\n")

        special_tags_file_path = os.path.join(working_directory, "__special.txt")
        self.special_tags = read_special_tags_from_file(special_tags_file_path)

        self.children: list[Concept] = []
        self.images: list[ConceptImage] = []

        self.canonical_name = name

        __parent = parent
        while __parent is not None:
            __parent_special_tags = parent.special_tags if parent is not None else {}
            self.special_tags = merge_special_tags(__parent_special_tags, self.special_tags)

            self.canonical_name = f"{__parent.name}.{self.canonical_name}"
            __parent = __parent.parent

    def add_child(self, child):
        self.children.append(child)

    def add_image(self, image: ConceptImage):
        self.images.append(image)

    def flatten(self) -> list[CaptionedImage]:
        captioned_images = []

        for child in self.children:
            captioned_images.extend(child.flatten())

        special_tags = self.special_tags

        for img in self.images:
            path, tags = img.build()
            tags = find_and_replace_special_tags(tags, special_tags)

            captioned_img = CaptionedImage(self, path, tags)
            captioned_images.append(captioned_img)

        return captioned_images

    def write(self, dst: str) -> list[CaptionedImage]:
        images = self.flatten()
        output: list[CaptionedImage] = []

        os.makedirs(dst, exist_ok=True)

        for img in images:
            img_path = img.path

            img_hash = sha256_file_hash(img_path)
            img_extension = os.path.splitext(img_path)[1]

            img_dst_file_path = f"{img_hash}{img_extension}"
            img_dst_file_path = os.path.join(dst, img_dst_file_path)

            img_tags_txt_file_path = f"{img_hash}.txt"
            img_tags_txt_file_path = os.path.join(dst, img_tags_txt_file_path)

            if not os.path.exists(img_dst_file_path):
                shutil.copyfile(img_path, img_dst_file_path)

            out_tags = img.tags[:]
            if not os.path.exists(img_tags_txt_file_path):
                write_tags(img_tags_txt_file_path, out_tags)
            else:
                existing_tags = read_tags_from_file(img_tags_txt_file_path)
                out_tags.extend(existing_tags)

                write_tags(img_tags_txt_file_path, out_tags)

            out = CaptionedImage(self, img_dst_file_path, out_tags)
            output.append(out)

        return output


def create_concept(name: str, directory_path, parent_concept=None) -> Concept:
    concept = Concept(name, directory_path, parent_concept)

    files = os.listdir(directory_path)
    for filename in files:
        file = os.path.join(directory_path, filename)

        if os.path.isdir(file):
            child = create_concept(filename, file, concept)
            concept.add_child(child)

        if os.path.isfile(file):
            extension = os.path.splitext(file)[1]

            if extension in [".png", ".jpg", ".jpeg"]:
                matching_text_filename = filename.replace(extension, ".txt")
                text_file_path = os.path.join(
                    directory_path, matching_text_filename)

                img_tags = []
                if os.path.exists(text_file_path):
                    img_tags = read_tags_from_file(text_file_path)

                concept_img = ConceptImage(concept, file, img_tags)
                concept.add_image(concept_img)

    return concept


def print_concept_info(concept: Concept, recursive: bool = True, indent: int = 0):
    concept_str = " │ " * (max(0, indent - 1)) + " ├─"
    print(f"{concept_str}{concept.canonical_name}")

    indent_str = " │ " * indent

    if len(concept.raw_tags) > 0:
        idx = 0
        tags_wrap = textwrap.wrap(", ".join(concept.raw_tags))
        for i in tags_wrap:
            if idx == 0:
                print(f"{indent_str} ├─tags: {i}")
            else:
                print(f"{indent_str} │       {i}")
            idx += 1
    else:
        print(f"{indent_str} ├─tags: N/A")

    print(f"{indent_str} ├─images: {len(concept.images)}")

    if recursive:
        if len(concept.children) > 0:
            indent_str += " │ "

        print(indent_str)
        for child in concept.children:
            print_concept_info(child, recursive, indent + 1)

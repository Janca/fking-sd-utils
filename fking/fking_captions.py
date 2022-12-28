import os
import shutil

from fking.fking_utils import merge_special_tags, read_special_tags_from_file, read_tags_from_file, sha256_file_hash, \
    write_tags


class ConceptImage:
    def __init__(self, concept, path, tags: list[str] = []) -> None:
        self.concept = concept
        self.path = path
        self.tags = tags

    def generate_tags(self):
        c_tags = self.tags[:]

        parent: Concept = self.concept
        while parent is not None:
            p_tags = parent.concept_tags[:]
            # p_tags.reverse()

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
        return self.path, tags


class Concept:
    """
    :type name: str
    :type working_directory: str
    :type concept_tags: list[str]
    :type parent: Concept|None
    """

    def __init__(self, args, name: str, working_directory: str, parent=None) -> None:
        self.args = args
        self.name = name
        self.parent = parent
        self.working_directory = working_directory

        tags_file_path = os.path.join(working_directory, "__prompt.txt")
        self.concept_tags = read_tags_from_file(tags_file_path)
        self.concept_tags = [
            t if t != '__folder__' else self.name
            if args.preserve_underscores else self.name.replace('_', ' ')
            for t in self.concept_tags
        ]

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

    def build(self, dst: str) -> int:
        os.makedirs(dst, exist_ok=True)

        images_saved = 0

        for child in self.children:
            images_saved += child.build(dst)

        special_tags = self.special_tags

        for img in self.images:
            path, tags = img.build()

            extension = os.path.splitext(path)[1]
            file_hash = sha256_file_hash(path)

            filename = file_hash + extension
            file_dst = os.path.join(dst, filename)

            tags_filename = f"{file_hash}.txt"
            tags_dst_path = os.path.join(dst, tags_filename)

            if os.path.exists(file_dst):
                if os.path.exists(tags_dst_path):
                    existing_tags = read_tags_from_file(tags_dst_path)
                    write_tags(tags_dst_path, tags + existing_tags, special_tags)
                else:
                    write_tags(tags_dst_path, tags, special_tags)

            else:
                # print(f"Saving {img.path} to '{file_dst}'.")
                shutil.copyfile(img.path, file_dst)
                write_tags(tags_dst_path, tags, special_tags)

                images_saved += 1

        return images_saved


def create_concept(args, name: str, directory_path, parent_concept=None) -> Concept:
    concept = Concept(args, name, directory_path, parent_concept)

    files = os.listdir(directory_path)
    for filename in files:
        file = os.path.join(directory_path, filename)

        if os.path.isdir(file):
            child = create_concept(args, filename, file, concept)
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

    print(f"Concept: {concept.canonical_name}")
    print(f"    Images: {len(concept.images)}")
    return concept

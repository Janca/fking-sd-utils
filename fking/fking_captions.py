import os
import shutil

from fking.fking_utils import read_tags_from_file, sha256_file_hash, write_tags


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
        return self.path, tags


class Concept:
    """
    :type name: str
    :type working_directory: str
    :type concept_tags: list[str]
    :type parent: Concept|None
    """

    def __init__(self, name: str, working_directory: str, concept_tags: list[str], parent=None) -> None:
        self.name = name
        self.parent = parent
        self.working_directory = working_directory

        self.concept_tags = []
        for t in concept_tags:
            if t == "__folder__":
                self.concept_tags.append(name)
            else:
                self.concept_tags.append(t)

        self.children: list[Concept] = []
        self.images: list[ConceptImage] = []

    def add_child(self, child):
        self.children.append(child)

    def add_image(self, image: ConceptImage):
        self.images.append(image)

    def build(self, dst: str) -> int:
        os.makedirs(dst, exist_ok=True)

        images_saved = 0

        for child in self.children:
            images_saved += child.build(dst)

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
                    write_tags(tags_dst_path, tags + existing_tags)
                else:
                    write_tags(tags_dst_path, tags)

            else:
                print(f"Saving {img.path} to '{file_dst}'.")
                shutil.copyfile(img.path, file_dst)
                write_tags(tags_dst_path, tags)

                images_saved += 1

        return images_saved


def create_concept(name: str, directory_path, parent_concept=None) -> Concept:
    concept_prompt_file = os.path.join(directory_path, "__prompt.txt")

    tags = []
    if os.path.exists(concept_prompt_file):
        tags = read_tags_from_file(concept_prompt_file)

    print(f"Creating concept '{name}'...")
    concept = Concept(name, directory_path, tags, parent_concept)

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

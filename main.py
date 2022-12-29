import argparse
import os
import shutil
import time

from fking.fking_captions import create_concept, print_concept_info
from fking.fking_utils import fix_prompt_text_files, prompt_warning, generate_tag_list, write_tags, generate_prompt_list

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str)
parser.add_argument("-o", "--output", type=str, default=None)
parser.add_argument("--overwrite", default=False, dest="overwrite", action='store_true')
parser.add_argument("--preserve-underscores", default=False, dest="preserve_underscores", action='store_true')
parser.add_argument("--fix-prompts", default=False, dest="fix_prompts", action='store_true')
parser.add_argument("--no-tree", default=True, dest="tree", action="store_false")

args = parser.parse_args()

input_directory = args.input
output_directory = args.output

merge_directory = os.path.join(output_directory, "merged_dataset") if output_directory is not None else None

if args.overwrite and os.path.exists(output_directory):
    if prompt_warning(f"Output directory exists; are you sure you want to overwrite?\n  '{output_directory}'"):
        print()
        print("Sanity check succeeded!")

        print(f"Deleting output directory '{output_directory}', please wait...")
        shutil.rmtree(output_directory)
        pass

    else:
        print()
        print("Exiting... Nothing was changed.")
        exit()

if args.fix_prompts:
    if prompt_warning(f"Are you sure you want to normalize prompt files in input folder?\n  '{input_directory}'"
                      f"\n\nThis action is irreversible."):
        print()
        print("Sanity check succeeded!")

        print(f"Fixing prompts... this may take a while...")
        fix_prompt_text_files(input_directory)
        pass

    else:
        print()
        print("Exiting... Nothing was changed.")
        exit()

print()
print("Generating output... please wait...")
print()

start_time_millis = time.time() * 1000.0
global_concept = create_concept(args, "global", input_directory)

if args.tree:
    print_concept_info(global_concept)

if output_directory is not None:
    images = global_concept.flatten(merge_directory)

    unique_prompts = generate_prompt_list(merge_directory)
    unique_prompts_file_path = os.path.join(output_directory, "unique_prompt.txt")
    with open(unique_prompts_file_path, "w+") as f:
        f.writelines(up + "\n" for up in unique_prompts)
        f.close()

    unique_tags = sum([prompt.split(', ') for prompt in unique_prompts], [])
    unique_tags_file_path = os.path.join(output_directory, "unique_tags.txt")
    write_tags(unique_tags_file_path, unique_tags)

end_time_millis = time.time() * 1000.0

print(f"Complete. Generated {images} captioned images in {(end_time_millis - start_time_millis):0.2f} millis.")

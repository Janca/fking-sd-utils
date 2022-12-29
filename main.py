import argparse
import os
import shutil
import time

from fking.fking_captions import create_concept, print_concept_info

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str)
parser.add_argument("-o", "--output", type=str, default="output")
parser.add_argument("--overwrite", default=False, dest="overwrite", action='store_true')
parser.add_argument("--i-am-sure", default=False, dest="dummy_failsafe", action='store_true')
parser.add_argument("--preserve-underscores", default=False, dest="preserve_underscores", action='store_true')

args = parser.parse_args()

input_directory = args.input
output_directory = args.output

if args.overwrite and os.path.exists(output_directory):
    if not args.dummy_failsafe:
        print("You have not disabled the dummy check, dummy. You must include the flag '--i-am-sure' to be able to "
              "overwrite the output directory.")
        exit(-1)

    else:
        print()
        sanity_check = input(f"Output directory exists; are you sure you want to overwrite?"
                             f"\n  '{output_directory}' [y/N] ")

        if sanity_check and sanity_check.lower() == "y":
            print()
            print("Sanity check succeeded!")

            print(f"Deleting output directory '{output_directory}', please wait...")
            shutil.rmtree(output_directory)
            pass

        else:
            print()
            print("Skipped generation. Nothing was changed.")
            exit()

print()
print("Generating output... please wait...")
print()

start_time_millis = time.time() * 1000.0
global_concept = create_concept(args, "global", input_directory)

print_concept_info(global_concept)

images = global_concept.build(output_directory)
end_time_millis = time.time() * 1000.0

print(f"Complete. Generated {images} captioned images in {(end_time_millis - start_time_millis):0.2f} millis.")

import argparse
import os
import shutil
import time

from fking.fking_captions import create_concept

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str)
parser.add_argument("-o", "--output", type=str, default="output")
parser.add_argument("--overwrite", default=False, dest="overwrite", action='store_true')
parser.add_argument("--i-am-sure", default=False, dest="dummy_failsafe", action='store_true')

args = parser.parse_args()

input_directory = args.input
output_directory = args.output

if args.overwrite and os.path.exists(output_directory):
    if not args.dummy_failsafe:
        print("You have not disabled to dummy check, dummy. You must include the flag '--i-am-sure' to be able to "
              "overwrite the output directory.")
        exit(-1)

    shutil.rmtree(output_directory)

start_time_millis = time.time() * 1000.0

global_concept = create_concept("global", input_directory)

print("----------------------------------------------\n")
print("Generating output... please wait...")
images = global_concept.build(output_directory)

end_time_millis = time.time() * 1000.0
print(f"Complete. Generated {images} captioned images in {(end_time_millis - start_time_millis):0.2f} millis.")

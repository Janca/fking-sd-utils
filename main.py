import argparse

from fking.fking_captions import create_concept

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", type=str)
parser.add_argument("-o", "--output", type=str, default="output")

args = parser.parse_args()

input_directory = args.input
output_directory = args.output

global_concept = create_concept("global", input_directory)
images = global_concept.build(output_directory)

print("\r\n")
print(f"Complete. Generated {images} captioned images.")

# fking-sd-utils

**A fking StableDiffusion utility library**

A small collection of utilities to help your StableDiffusion/Dreambooth experience.
This library is currently focused on assisting with captioning concept images for training in TIs, Hypernetworks or
Dreambooth.

## Usage

The captioning util is a hierarchical based captioner, it will apply the tags of the parent directories to each of its
subdirectories and images.
Each directory can contain a text file named `__prompt.txt`, all text in this file will be prepended to all child
images, and subdirectories and their images.
Using `__folder__` in the `__prompt.txt` file will automatically use the parent directory's name.

**Example File Tree**

```commandline
D:\TEST\TRAINING_DATA
│   __prompt.txt
│
├───exterior
│   │   120160.png
│   │   120161.png
│   │   120162.png
│   │   148.png
│   │   149.png
│   │   54.png
│   │   __prompt.txt
│   │
│   ├───cityscape
│   │       120228.png
│   │       120229.png
│   │       120272.png
│   │       120273.png
│   │       120274.png
│   │       120275.png
│   │       __prompt.txt
|   |
│   ├───grasslands
│   │       120166.png
│   │       120167.png
│   │       120168.png
│   │       120169.png
│   │       __prompt.txt
│   │
│   └───mountains
│           120265.png
│           120266.png
│           __prompt.txt
```
## Run with no parameters to enable working through the UI.

```commandline
py main.py
```

![UI_Example_1](/ui_image_01.png)

**Utility Usage**

```commandline
py main.py --no-ui -i "input_directory" -o "output_directory"
```

### Extended Usage

You can also create text files named `__special.txt` in each directory, or just the root input folder is what I do, to
allow you to make quick S/R tags, for example:

```json
[
    {
        "special_tag":"__black_and_white__",
        "tags":"black and white, b&w, monochrome",
        "mode":1
    }
]
```

And any image file or `__prompt.txt` file using `__black_and_white__` will be replaced
with `black and white, b&w, monochrome`.
The modes indicate how it should handle if a parent in the hierarchy has the same special tag.

```
    1 - Merge tags with parent
    2 - Replace with parent
    3 - Keep current
```

By default, if `mode` is missing, it will use `merge`.

---

## Final Thoughts

Don't expect things not to be broken, Python isn't my strongest language, and I am not concerned with breaking changes,
I will be pushing whatever to this repo.
Feel free to make any pull requests you'd like. It would be nice to have some collaboration.

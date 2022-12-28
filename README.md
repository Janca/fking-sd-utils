# fking-sd-utils
**A fking StableDiffusion utility library**

A small collection of utilities to help your StableDiffusion/Dreambooth experience.
This library is currently focused on assisting with captioning concept images for training in TIs, Hypernetworks or Dreambooth.

## Usage
The captioning util is a hierarchical based captioner, it will apply the tags of the parent directories to each of its subdirectories and images.
Each directory can contain a text file named `__prompt.txt`, all text in this file will be prepended to all child images, and subdirectories and their images.
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

**Utility Usage**
```commandline
py main.py -i "input_directory" -o "output_directory"
```

**Example output from the above file structure**
```commandline
Saving D:\test\training_data\exterior\cityscape\120228.png to 'D:\test\output\9baafde2e93eecf8835d52b8555d0fb27fccc17f1af9e5f8086fd581312775bf.png'.
Saving 'test, exterior, cityscape' to 'D:\test\output\9baafde2e93eecf8835d52b8555d0fb27fccc17f1af9e5f8086fd581312775bf.txt'.
Saving D:\test\training_data\exterior\cityscape\120229.png to 'D:\test\output\272c892c784d3c34678381a2bd0495ee855fa080df5a02f98849514c165f7357.png'.
Saving 'test, exterior, cityscape' to 'D:\test\output\272c892c784d3c34678381a2bd0495ee855fa080df5a02f98849514c165f7357.txt'.
Saving D:\test\training_data\exterior\cityscape\120272.png to 'D:\test\output\b065dc591a6835d02e3c6fe0afd659bb9cce20aacd92ec4cc2ec00af786f6564.png'.
Saving 'test, exterior, cityscape' to 'D:\test\output\b065dc591a6835d02e3c6fe0afd659bb9cce20aacd92ec4cc2ec00af786f6564.txt'.
Saving D:\test\training_data\exterior\cityscape\120273.png to 'D:\test\output\ada8a0e3b0634ef152480e09cbc9bd8c164e7acc0ec5818266cc71fe957ee25c.png'.
Saving 'test, exterior, cityscape' to 'D:\test\output\ada8a0e3b0634ef152480e09cbc9bd8c164e7acc0ec5818266cc71fe957ee25c.txt'.
Saving D:\test\training_data\exterior\cityscape\120274.png to 'D:\test\output\da1648af6e3adf2e6c51776b8b31b5835b38f0e1a9cf0ccd8a63bdc2989af6bb.png'.
Saving 'test, exterior, cityscape' to 'D:\test\output\da1648af6e3adf2e6c51776b8b31b5835b38f0e1a9cf0ccd8a63bdc2989af6bb.txt'.
Saving D:\test\training_data\exterior\cityscape\120275.png to 'D:\test\output\e3e5e37c5d1e6b797504dcc40938ba3c572c8cf45a9da2bf3eece67ef16cf5c0.png'.
Saving 'test, exterior, cityscape' to 'D:\test\output\e3e5e37c5d1e6b797504dcc40938ba3c572c8cf45a9da2bf3eece67ef16cf5c0.txt'.
Saving D:\test\training_data\exterior\flora\120230.png to 'D:\test\output\815fd742acb082a20230a334551f493167ebc615e136065b44b2dfe5352d95ac.png'.
Saving 'test, exterior, flora' to 'D:\test\output\815fd742acb082a20230a334551f493167ebc615e136065b44b2dfe5352d95ac.txt'.
Saving D:\test\training_data\exterior\flora\120231.png to 'D:\test\output\83bfc303629bbb99391137384836036f46679d5dd654b6dea5e019d74fde891e.png'.
Saving 'test, exterior, flora' to 'D:\test\output\83bfc303629bbb99391137384836036f46679d5dd654b6dea5e019d74fde891e.txt'.
Saving D:\test\training_data\exterior\flora\120232.png to 'D:\test\output\a6cff07ba37d0ce64f9e65c92c2308f1a571246bb80350d9e7ee7d2cca7d1e56.png'.
Saving 'test, exterior, flora' to 'D:\test\output\a6cff07ba37d0ce64f9e65c92c2308f1a571246bb80350d9e7ee7d2cca7d1e56.txt'.
Saving D:\test\training_data\exterior\forest\10.png to 'D:\test\output\2a8d1a1aceb1fc170469dc1b7068e05fbbfd1ee491a057cd78ff5a9447e35a26.png'.
Saving 'test, exterior, forest' to 'D:\test\output\2a8d1a1aceb1fc170469dc1b7068e05fbbfd1ee491a057cd78ff5a9447e35a26.txt'.
Saving D:\test\training_data\exterior\forest\120239.png to 'D:\test\output\dbbe5cae795b32dcf26e49e2c3bf5c5367a519ff1a0ca810d55833d618197701.png'.
Saving 'test, exterior, forest' to 'D:\test\output\dbbe5cae795b32dcf26e49e2c3bf5c5367a519ff1a0ca810d55833d618197701.txt'.
Saving D:\test\training_data\exterior\forest\120240.png to 'D:\test\output\7e58bdf10cebd694b5e823a79dfbaa83e5d6e9e377537755a2fed00c2410390c.png'.
Saving 'test, exterior, forest' to 'D:\test\output\7e58bdf10cebd694b5e823a79dfbaa83e5d6e9e377537755a2fed00c2410390c.txt'.
Saving D:\test\training_data\exterior\forest\9.png to 'D:\test\output\e70d93d01a1e8a006629388f124fa41dbc1d9f4049802e34effaea419f4b1b9a.png'.
Saving 'test, exterior, forest' to 'D:\test\output\e70d93d01a1e8a006629388f124fa41dbc1d9f4049802e34effaea419f4b1b9a.txt'.
Saving D:\test\training_data\exterior\grasslands\120166.png to 'D:\test\output\f74bfd75fd29ed0626ac8cf3160e7285f09299ff0f1870dfb51915cb8f105183.png'.
Saving 'test, exterior, grasslands' to 'D:\test\output\f74bfd75fd29ed0626ac8cf3160e7285f09299ff0f1870dfb51915cb8f105183.txt'.
Saving D:\test\training_data\exterior\grasslands\120167.png to 'D:\test\output\d19b736bc13b82838779b4ea39628618f380ec110679a4935c4c40ae6e157ed5.png'.
Saving 'test, exterior, grasslands' to 'D:\test\output\d19b736bc13b82838779b4ea39628618f380ec110679a4935c4c40ae6e157ed5.txt'.
Saving D:\test\training_data\exterior\grasslands\120168.png to 'D:\test\output\67e02dc03b08275f796877ad52fc453adaa8aa97d9e106be6685bf1bbb3e679d.png'.
Saving 'test, exterior, grasslands' to 'D:\test\output\67e02dc03b08275f796877ad52fc453adaa8aa97d9e106be6685bf1bbb3e679d.txt'.
Saving D:\test\training_data\exterior\grasslands\120169.png to 'D:\test\output\6c9a654024002dbd2386ebbae0f025d7a5ca910bb06b49fd1822ff4cc2a5a088.png'.
Saving 'test, exterior, grasslands' to 'D:\test\output\6c9a654024002dbd2386ebbae0f025d7a5ca910bb06b49fd1822ff4cc2a5a088.txt'.
Saving D:\test\training_data\exterior\mountains\120265.png to 'D:\test\output\deb4e959cbe791732f1a83e207c5d923a6b40c970bcf6790f281059e3948bf9f.png'.
Saving 'test, exterior, mountains' to 'D:\test\output\deb4e959cbe791732f1a83e207c5d923a6b40c970bcf6790f281059e3948bf9f.txt'.
Saving D:\test\training_data\exterior\mountains\120266.png to 'D:\test\output\0ef764e909ad3e63e01a9435b11253f40483cf7f0f336fdea2224dece98365db.png'.
Saving 'test, exterior, mountains' to 'D:\test\output\0ef764e909ad3e63e01a9435b11253f40483cf7f0f336fdea2224dece98365db.txt'.
```
### Extended Usage
You can also create text files named `__special.txt` in each directory, or just the root input folder is what I do, to allow you to make quick S/R tags, for example:
```json
[
    {
        "special_tag":"__black_and_white__",
        "tags":"black and white, b&w, monochrome",
        "mode":1
    }
]
```

And any image file or `__prompt.txt` file using `__black_and_white__` will be replaced with `black and white, b&w, monochrome`.
The modes indicate how it should handle if a parent in the hierarchy has the same special tag.
```
    1 - Merge tags with parent
    2 - Replace with parent
    3 - Keep current
```

By default, if `mode` is missing, it will use `merge`.

---
## Final Thoughts
Don't expect things not to be broken, Python isn't my strongest language, and I am not concerned with breaking changes, I will be pushing whatever to this repo.
Feel free to make any pull requests you'd like. It would be nice to have some collaboration.

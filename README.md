# UnityPy
[![Discord server invite](https://discordapp.com/api/guilds/603359898507673630/embed.png)](https://discord.gg/C6txv7M)
[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/UnityPy.svg)](https://pypi.python.org/pypi/UnityPy)
[![Win/Mac/Linux](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-informational)]()
[![MIT](https://img.shields.io/pypi/l/UnityPy.svg)](https://github.com/K0lb3/UnityPy/blob/master/LICENSE)
![Test and Publish](https://github.com/K0lb3/UnityPy/workflows/Test%20and%20Publish/badge.svg)

A Unity asset extractor for Python based on [AssetStudio](https://github.com/Perfare/AssetStudio).

Next to extraction it also supports editing Unity assets.
So far following obj types can be edited:
  - Texture2D
  - Sprite(indirectly via linked Texture2D)
  - TextAsset
  - MonoBehaviour

If you need advice or if you want to talk about (game) data-mining,
feel free to join the [UnityPy Discord](https://discord.gg/C6txv7M).

1. [Installation](#installation)
2. [Example](#example)
3. [Important Classes](#important-classes)
4. [Important Object Types](#important-object-types)

## Installation

**Python 3.6.0 or higher is required**

```cmd
pip install UnityPy
```

or download/clone the git and use

```cmd
python setup.py install
```

### Notes

#### Windows

Visual C++ Redistributable is required for the brotli dependency.


## Example

The following is a simple example.


```python
import os
import UnityPy

def unpack_all_assets(source_folder : str, destination_folder : str):
    # iterate over all files in source folder
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            # generate file_path
            file_path = os.path.join(root, file_name)
            # load that file via UnityPy.load
            env = UnityPy.load(file_path)

            # iterate over internal objects
            for obj in env.objects:
                # process specific object types
                if obj.type in ["Texture2D", "Sprite"]:
                    # parse the object data
                    data = obj.read()

                    # create destination path
                    dest = os.path.join(destination_folder, data.name)

                    # make sure that the extension is correct
                    # you probably only want to do so with images/textures
                    dest, ext = os.path.splitext(dest)
                    dest = dest + ".png"

                    img = data.image
                    img.save(dest)

            # alternative way which keeps the original path
            for path,obj in env.container.items():
                if obj.type in ["Texture2D", "Sprite"]:
                    data = obj.read()
                    # create dest based on original path
                    dest = os.path.join(destination_folder, *path.split("/"))
                    # make sure that the dir of that path exists
                    os.makedirs(os.path.dirname(dest), exist_ok = True)
                    # correct extension
                    dest, ext = os.path.splitext(dest)
                    dest = dest + ".png"
                    data.image.save(dest)
```

You probably have to read [Important Classes](#important-classes)
and [Important Object Types](#important-object-types) to understand how it works.

People who have slightly advanced python skills should take a look at [examples/AssetBatchConverter.py](examples/AssetBatchConverter.py) for a more advanced example.
It can also be used as general template.


## Important Classes

### [Environment](UnityPy/environment.py)

Environment loads and parses the files that are given to it.
It can be initialized via:

* a file path - apk files can be loaded as well
* a folder path - loads all files in that folder (bad idea for folders with a lot of files)
* a stream - e.g. io.BytesIO, filestream,...
* a bytes object - will be loaded into a stream

UnityPy can detect itself if the file is a WebFile, BundleFile, Asset or APK itself.

The unpacked assets will be loaded into ``.files``, which is a dict consisting of ``asset-name : asset``.

The all objects of the loaded assets can be easily accessed via ``.objects``,
which itself is a simple recursive iterator.

```python
import io
import UnityPy

# all of the following would work
src = "file_path"
src = b"bytes"
src = io.BytesIO(b"Streamable")

env = UnityPy.load(src)

for obj in env.objects:
    ...

# saving an edited file
    # apply modifications to the objects
    # don't forget to use data.save()
    ...
with open(dst, "wb") as f:
    f.write(env.file.save())
```

### [Asset](UnityPy/files/SerializedFile.py)

Assets are a container that contains multiple objects.
One of these objects can be an AssetBundle, which contains a file path for some of the objects in the same asset.

All objects can be found in the ``.objects`` dict - ``{ID : object}``.

The objects which have a file path can be found in the ``.container`` dict - ``{path : object}``.

### [Object](UnityPy/files/ObjectReader.py)

Objects contain the *actual* files which, e.g. textures, text files, meshes, settings, ...

To acquire the actual data of an object it has to be read first, this happens via the ``.read()`` function. This isn't done automatically to save time because only a small part of the objects are of interest. Serialized objects can be set with raw data using ``.set_raw_data(data)`` or modified with ``.save()`` function if supported.

## Important Object Types

All object types can be found in [UnityPy/classes](UnityPy/classes/).

### [Texture2D](UnityPy/classes/Texture2D.py)

* ``.name``
* ``.image`` converts the texture into a ``PIL.Image``
* ``.m_Width`` - texture width (int)
* ``.m_Height`` - texture height (int)

__Export__
```python
from PIL import Image
for obj in env.objects:
    if obj.type == "Texture2D":
        # export texture
        data = image.read()
        data.image.save(path)
        # edit texture
        fp = os.path.join(replace_dir, data.name)
        pil_img = Image.open(fp)
        data.image = pil_img
        data.save()
```

### [Sprite](UnityPy/classes/Sprite.py)

Sprites are part of a texture and can have a separate alpha-image as well.
Unlike most other extractors (including AssetStudio) UnityPy merges those two images by itself.

* ``.name``
* ``.image`` - converts the merged texture part into a ``PIL.Image``
* ``.m_Width`` - sprite width (int)
* ``.m_Height`` - sprite height (int)

__Export__
```python
for obj in env.objects:
    if obj.type == "Sprite":
        data = image.read()
        data.image.save(path)
```

### [TextAsset](UnityPy/classes/TextAsset.py)

TextAssets are usually normal text files.

* ``.name``
* ``.script`` - binary data (bytes)
* ``.text`` - script decoded via UTF8 (str)

Some games save binary data as TextFile, so it's usually better to use ``.script``.

__Export__
```python
for obj in env.objects:
    if obj.type == "TextAsset":
        # export asset
        data = image.read()
        with open(path, "wb") as f:
            f.write(bytes(data.script))
        # edit asset
        fp = os.path.join(replace_dir, data.name)
        with open(fp, "rb") as f:
            data.script = f.read()
        data.save()
```

### [MonoBehaviour](UnityPy/classes/MonoBehaviour.py)

MonoBehaviour assets are usually used to save the class instances with their values.
If a type tree exists it can be used to read the whole data,
but if it doesn't, then it is usually necessary to investigate the class that loads the specific MonoBehaviour to extract the data.
([example](examples/CustomMonoBehaviour/get_scriptable_texture.py))

* ``.name``
* ``.script``
* ``.raw_data`` - data after the basic initialisation

__Export__
```python
import json

for obj in env.objects:
    if obj.type == "MonoBehaviour":
        # export
        if obj.serialized_type.nodes:
            # save decoded data
            tree = obj.read_typetree()
            fp = os.path.join(extract_dir, f"{data.name}.json"):
            with open(fp, "wt", encoding = "utf8") as f:
                json.dump(tree, f, ensure_ascii = False, indent = 4)
        else:
            # save raw relevant data (without Unity MonoBehaviour header)
            data = obj.read()
            fp = os.path.join(extract_dir, f"{data.name}.bin"):
            with open(fp, "wb") as f:
                f.write(data.raw_data)

        # edit
        if obj.serialized_type.nodes:
            tree = obj.read_typetree()
            # apply modifications to the data within the tree
            obj.save_typetree(tree)
        else:
            with open(replace_dir, data.name) as f:
                data.save(raw_data = f.read())
```

### [AudioClip](UnityPy/classes/AudioClip.py)

* ``.samples`` - ``{sample-name : sample-data}``

The samples are converted into the .wav format.
The sample-data is a .wav file in bytes.

```python
clip : AudioClip
for name, data in clip.samples.items():
    with open(name, "wb") as f:
        f.write(data)
```

### [Mesh](UnityPy/classes/Mesh.py)

* ``.export()`` - mesh exported as .obj (str)

The mesh is converted into an Wavefront .obj file.

```python
mesh : Mesh
with open(f"{mesh.name}.obj", "wt", newline = "") as f:
    # newline = "" is important
    f.write(mesh.export())
```

### [Font](UnityPy/classes/Font.py)

```python
if obj.type == "Font":
    font : Font = obj.read()
    if font.m_FontData:
        extension = ".ttf"
        if font.m_FontData[0:4] == b"OTTO":
            extension = ".otf"

    with open(os.path.join(path, font.name+extension), "wb") as f:
        f.write(font.m_FontData)
```

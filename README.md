# UnityPy

[![Discord server invite](https://discordapp.com/api/guilds/603359898507673630/embed.png)](https://discord.gg/C6txv7M)
[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/UnityPy.svg)](https://pypi.python.org/pypi/UnityPy)
[![Win/Mac/Linux](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-informational)]()
[![MIT](https://img.shields.io/github/license/K0lb3/UnityPy)](https://github.com/K0lb3/UnityPy/blob/master/LICENSE)
![Test](https://github.com/K0lb3/UnityPy/workflows/Test/badge.svg)

A Unity asset extractor for Python based on [AssetStudio](https://github.com/Perfare/AssetStudio).

Next to extraction, it also supports editing Unity assets.
So far following obj types can be edited:

-   Texture2D
-   Sprite(indirectly via linked Texture2D)
-   TextAsset
-   MonoBehaviour (and all other types that you have the typetree of)

If you need advice or if you want to talk about (game) data-mining,
feel free to join the [UnityPy Discord](https://discord.gg/C6txv7M).

If you're using UnityPy a commercial project,
a donation to a charitable cause or a sponsorship of this project is expected.

**As UnityPy is still in active development breaking changes can happen.**
Those changes are usually limited to minor versions (x.y) and not to patch versions (x.y.z).
So in case that you don't want to actively maintain your project,
make sure to make a note of the used UnityPy version in your README or add a check in your code.
e.g.

```python
if UnityPy.__version__ != '1.9.6':
    raise ImportError("Invalid UnityPy version detected. Please use version 1.9.6")
```

1. [Installation](#installation)
2. [Example](#example)
3. [Important Classes](#important-classes)
4. [Important Object Types](#important-object-types)
5. [Custom Fileystem](#custom-filesystem)
6. [Credits](#credits)

## Installation

**Python 3.7.0 or higher is required**

via pypi

```cmd
pip install UnityPy
```

from source

```cmd
git clone https://github.com/K0lb3/UnityPy.git
cd UnityPy
python -m pip install .
```

### Notes

#### Windows

Visual C++ Redistributable is required for the brotli dependency.
In case a new(ish) Python version is used, it can happen that the C-dependencies of UnityPy might not be precompiled for this version.
In such cases the user either has to report this as issue or follow the steps of [this issue](https://github.com/K0lb3/UnityPy/issues/223) to compile it oneself.
Another option for the user is downgrading Python to the latest version supported by UnityPy. For this see the python version badge at the top of the README.

### Crash without warning/error

The C-implementation of the typetree reader can directly crash python.
In case this happens, the usage of the C-typetree reader can be disabled by adding these two lines to your main file.

```python
from UnityPy.helpers import TypeTreeHelper
TypeTreeHelper.read_typetree_boost = False
```

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
                if obj.type.name in ["Texture2D", "Sprite"]:
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
                if obj.type.name in ["Texture2D", "Sprite"]:
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

People with slightly advanced python skills should look at [UnityPy/tools/extractor.py](UnityPy/tools/extractor.py) for a more advanced example.
It can also be used as a general template or as an importable tool.

### Setting the decryption key for Unity CN's AssetBundle encryption

The chinese version of Unity has its own inbuild option to encrypt AssetBundles/BundleFiles. As it's a feature of Unity itself, and not a game specific protection, it is included in UnityPy as well.
To enable encryption simply use `UnityPy.set_assetbundle_decrypt_key(key)`, with key being the value that the game that loads the budles passes to `AssetBundle.SetAssetBundleDecryptKey`.

## Important Classes

### [Environment](UnityPy/environment.py)

Environment loads and parses the given files.
It can be initialized via:

-   a file path - apk files can be loaded as well
-   a folder path - loads all files in that folder (bad idea for folders with a lot of files)
-   a stream - e.g., io.BytesIO, file stream,...
-   a bytes object - will be loaded into a stream

UnityPy can detect if the file is a WebFile, BundleFile, Asset, or APK.

The unpacked assets will be loaded into `.files`, a dict consisting of `asset-name : asset`.

All objects of the loaded assets can be easily accessed via `.objects`,
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

All objects can be found in the `.objects` dict - `{ID : object}`.

The objects with a file path can be found in the `.container` dict - `{path : object}`.

### [Object](UnityPy/files/ObjectReader.py)

Objects contain the _actual_ files, e.g., textures, text files, meshes, settings, ...

To acquire the actual data of an object it has to be read first. This happens via the `.read()` function. This isn't done automatically to save time because only a small part of the objects are of interest. Serialized objects can be set with raw data using `.set_raw_data(data)` or modified with `.save()` function, if supported.

## Important Object Types

All object types can be found in [UnityPy/classes](UnityPy/classes/).

### [Texture2D](UnityPy/classes/Texture2D.py)

-   `.m_Name`
-   `.image` converts the texture into a `PIL.Image`
-   `.m_Width` - texture width (int)
-   `.m_Height` - texture height (int)

**Export**

```python
from PIL import Image
for obj in env.objects:
    if obj.type.name == "Texture2D":
        # export texture
        data = obj.read()
        path = os.path.join(export_dir, f"{data.m_Name}.png")
        data.image.save(path)
        # edit texture
        fp = os.path.join(replace_dir, f"{data.m_Name}.png")
        pil_img = Image.open(fp)
        data.image = pil_img
        data.save()
```

### [Sprite](UnityPy/classes/Sprite.py)

Sprites are part of a texture and can have a separate alpha-image as well.
Unlike most other extractors (including AssetStudio), UnityPy merges those two images by itself.

-   `.m_Name`
-   `.image` - converts the merged texture part into a `PIL.Image`
-   `.m_Width` - sprite width (int)
-   `.m_Height` - sprite height (int)

**Export**

```python
for obj in env.objects:
    if obj.type.name == "Sprite":
        data = obj.read()
        path = os.path.join(export_dir, f"{data.m_Name}.png")
        data.image.save(path)
```

### [TextAsset](UnityPy/classes/TextAsset.py)

TextAssets are usually normal text files.

-   `.m_Name`
-   `.m_Script` - str

Some games save binary data as TextFile, so to convert the ``str`` back to bytes correctly ``m_Script.encode("utf-8", "surrogateescape")`` has to be used.

**Export**

```python
for obj in env.objects:
    if obj.type.name == "TextAsset":
        # export asset
        data = obj.read()
        path = os.path.join(export_dir, f"{data.m_Name}.txt")
        with open(path, "wb") as f:
            f.write(data.m_Script.encode("utf-8", "surrogateescape"))
        # edit asset
        fp = os.path.join(replace_dir, f"{data.m_Name}.txt")
        with open(fp, "rb") as f:
            data.m_Script = f.read().decode("utf-8", "surrogateescape"))
        data.save()
```

### [MonoBehaviour](UnityPy/classes/MonoBehaviour.py)

MonoBehaviour assets are usually used to save the class instances with their values.
If a type tree exists, it can be used to read the whole data,
but if it doesn't exist, then it is usually necessary to investigate the class that loads the specific MonoBehaviour to extract the data.
([example](examples/CustomMonoBehaviour/get_scriptable_texture.py))

-   `.m_Name`
-   `.m_Script`

**Export**

```python
import json

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        # export
        if obj.serialized_type.node:
            # save decoded data
            tree = obj.read_typetree()
            fp = os.path.join(extract_dir, f"{tree['m_Name']}.json")
            with open(fp, "wt", encoding = "utf8") as f:
                json.dump(tree, f, ensure_ascii = False, indent = 4)

        # edit
        if obj.serialized_type.node:
            tree = obj.read_typetree()
            # apply modifications to the data within the tree
            obj.save_typetree(tree)
        else:
            data = obj.read(check_read=False)
            with open(os.path.join(replace_dir, data.m_Name)) as f:
                data.save(raw_data = f.read())
```

### [AudioClip](UnityPy/classes/AudioClip.py)

-   `.samples` - `{sample-name : sample-data}`

The samples are converted into the .wav format.
The sample data is a .wav file in bytes.

```python
clip : AudioClip
for name, data in clip.samples.items():
    with open(name, "wb") as f:
        f.write(data)
```

### [Font](UnityPy/classes/Font.py)

```python
if obj.type.name == "Font":
    font : Font = obj.read()
    if font.m_FontData:
        extension = ".ttf"
        if font.m_FontData[0:4] == b"OTTO":
            extension = ".otf"

    with open(os.path.join(path, font.m_Name+extension), "wb") as f:
        f.write(font.m_FontData)
```

### [Mesh](UnityPy/classes/Mesh.py)

-   `.export()` - mesh exported as .obj (str)

The mesh will be converted to the Wavefront .obj file format.

```python
mesh : Mesh
with open(f"{mesh.m_Name}.obj", "wt", newline = "") as f:
    # newline = "" is important
    f.write(mesh.export())
```

### Renderer, MeshRenderer, SkinnedMeshRenderer

ALPHA-VERSION

-   `.export(export_dir)` - exports the associated mesh, materials, and textures into the given directory

The mesh and materials will be in the Wavefront formats.

```python
mesh_renderer : Renderer
export_dir: str

if mesh_renderer.m_GameObject:
    # get the name of the model
    game_object = mesh_renderer.m_GameObject.read()
    export_dir = os.path.join(export_dir, game_object.m_Name)
mesh_renderer.export(export_dir)
```

### [Texture2DArray](UnityPy/classes/Texture2DArray.py)

WARNING - not well tested

-   `.m_Name`
-   `.image` converts the texture2darray into a `PIL.Image`
-   `.m_Width` - texture width (int)
-   `.m_Height` - texture height (int)

**Export**

```python
import os
from PIL import Image
for obj in env.objects:
    if obj.type.name == "Texture2DArray":
        # export texture
        data = obj.read()
        for i, image in enumerate(data.images):
            image.save(os.path.join(path, f"{data.m_Name}_{i}.png"))
        # editing isn't supported yet!
```

## Custom-Filesystem

UnityPy uses [fsspec](https://github.com/fsspec/filesystem_spec) under the hood to manage all filesystem interactions.
This allows using various different types of filesystems without having to change UnityPy's code.
It also means that you can use your own custom filesystem to e.g. handle indirection via catalog files, load assets on demand from a server, or decrypt files.

Following methods of the filesystem have to be implemented for using it in UnityPy.

-   sep (not a function, just the seperator as character)
-   isfile(self, path: str) -> bool
-   isdir(self, path: str) -> bool
-   exists(self, path: str, \*\*kwargs) -> bool
-   walk(self, path: str, \*\*kwargs) -> Iterable[List[str], List[str], List[str]]
-   open(self, path: str, mode: str = "rb", \*\*kwargs) -> file ("rb" mode required, "wt" required for ModelExporter)
-   makedirs(self, path: str, exist_ok: bool = False) -> bool

## Credits

First of all,
thanks a lot to all contributors of UnityPy and all of its users.

Also,
many thanks to:

-   [Perfare](https://github.com/Perfare) for creating and maintaining and every contributor of [AssetStudio](https://github.com/Perfare/AssetStudio)
-   [ds5678](https://github.com/ds5678) for the [TypeTreeDumps](https://github.com/AssetRipper/TypeTreeDumps) and the [custom minimal Tpk format](https://github.com/AssetRipper/Tpk)
-   [Razmoth](https://github.com/Razmoth) for figuring out and sharing Unity CN's AssetBundle decryption ([src](https://github.com/Razmoth/PGRStudio)).
-   [nesrak1](https://github.com/nesrak1) for figuring out the [Switch texture swizzling](https://github.com/nesrak1/UABEA/blob/master/TexturePlugin/Texture2DSwitchDeswizzler.cs)
-   xiop_13690 (discord) for figuring out unsolved issues of the ManagedReferencesRegistry
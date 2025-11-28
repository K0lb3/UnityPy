# UnityPy

[![Discord server invite](https://discordapp.com/api/guilds/603359898507673630/embed.png)](https://discord.gg/C6txv7M)
[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/UnityPy.svg)](https://pypi.python.org/pypi/UnityPy)
[![Win/Mac/Linux](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-informational)]()
[![MIT](https://img.shields.io/github/license/K0lb3/UnityPy)](https://github.com/K0lb3/UnityPy/blob/master/LICENSE)
![Test](https://github.com/K0lb3/UnityPy/workflows/Test/badge.svg)

A Unity asset extractor for Python based on [AssetStudio](https://github.com/Perfare/AssetStudio).

Next to extraction, UnityPy also supports editing Unity assets.
Via the typetree structure all object types can be edited in their native forms.

```python
# modification via dict:
    raw_dict = obj.parse_as_dict()
    # modify raw dict
    obj.patch(raw_dict)
# modification via parsed class
    instance = obj.parse_as_object()
    # modify instance
    obj.patch(instance)
```

If you need advice or if you want to talk about (game) data-mining,
feel free to join the [UnityPy Discord](https://discord.gg/C6txv7M).

If you're using UnityPy for a commercial project,
a donation to a charitable cause or a sponsorship of this project is expected.

**As UnityPy is still in active development, breaking changes can happen.**
These changes are usually limited to minor versions (x.y) and not to patch versions (x.y.z).
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
5. [Configurations](#configurations)
6. [Credits](#credits)

## Installation

**Python 3.8 or higher is required.**

Install via PyPI:

```bash
pip install UnityPy
```

Install from source code:

```bash
git clone https://github.com/K0lb3/UnityPy.git
cd UnityPy
python -m pip install .
```

### Notes

#### Windows

Visual C++ Redistributable is required for the brotli dependency.
In case a new(ish) Python version is used, it can happen that the C-dependencies of UnityPy might not be precompiled for this version.
In such cases the user either has to report this as issue or follow the steps of [this issue](https://github.com/K0lb3/UnityPy/issues/223) to compile it oneself.
Another option for the user is downgrading Python to the latest version supported by UnityPy. For this see the Python version badge at the top of the README.

#### Crash without warning/error

The C-implementation of the typetree reader can directly crash Python.
In case this happens, the usage of the C-typetree reader can be disabled. Read [this section](#disable-typetree-c-implementation) for more details.

## Example

The following is a simple example.

```python
import os
import UnityPy

def unpack_all_assets(source_folder: str, destination_folder: str):
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
                    data = obj.parse_as_object()

                    # create destination path
                    dest = os.path.join(destination_folder, data.m_Name)

                    # make sure that the extension is correct
                    # you probably only want to do so with images/textures
                    dest, ext = os.path.splitext(dest)
                    dest = dest + ".png"

                    img = data.image
                    img.save(dest)

            # alternative way which keeps the original path
            for path,obj in env.container.items():
                if obj.type.name in ["Texture2D", "Sprite"]:
                    data = obj.parse_as_object()
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

Users with slightly advanced Python skills should look at [UnityPy/tools/extractor.py](UnityPy/tools/extractor.py) for a more advanced example.
It can also be used as a general template or as an importable tool.

## Important Classes

### Environment

[Environment](UnityPy/environment.py) loads and parses the given files.
It can be initialized via:

-   a file path - apk files can be loaded as well
-   a folder path - loads all files in that folder (bad idea for folders with a lot of files)
-   a stream - e.g., `io.BytesIO`, file stream,...
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

### Asset

Assets \([SerializedFile class](UnityPy/files/SerializedFile.py)\) are a container that contains multiple objects.
One of these objects can be an AssetBundle, which contains a file path for some of the objects in the same asset.

All objects can be found in the `.objects` dict - `{ID : object}`.

The objects with a file path can be found in the `.container` dict - `{path : object}`.

### Object

Objects \([ObjectReader class](UnityPy/files/ObjectReader.py)\) contain the _actual_ files, e.g., textures, text files, meshes, settings, ...

To acquire the actual data of an object it has to be parsed first.
This happens via the parse functions mentioned below.
This isn't done automatically to save time as only a small part of the objects are usually of interest.
Serialized objects can be set with raw data using `.set_raw_data(data)` or modified with `.save()` function, if supported.

For object types with ``m_Name`` you can use ``.peek_name()`` to only read the name of the parsed object without parsing it completely, which is way faster.

There are two general parsing functions, ``.parse_as_object()`` and ``.parse_as_dict()``.
``parse_as_dict`` parses the object data into a dict.
``parse_as_object`` parses the object data into a class. If the class is a Unity class, it's stub class from ``UnityPy.classes(.generated)`` will be used, if it's an unknown one, then it will be parsed into an ``UnknownObject``, which simply acts as interface for the otherwise parsed dict.
Some special classes, namely those below, have additional handlers added to their class for easier interaction with them.

The ``.patch(item)`` function can be used on all object (readers) to replace their data with the changed item, which has to be either a dict or of the class the object represents.

#### Example

```py
for obj in env.objects:
    if obj.type.name == "the type you want":
        if obj.peek_name() != "the specific object you want":
            continue
        # parsing
        instance = obj.parse_as_object()
        dic = obj.parse_as_dict()

        # modifying
        instance.m_Name = "new name"
        dic["m_Name"] = "new name"

        # saving
        obj.patch(instance)
        obj.patch(dic)
```

#### Legacy

Following functions are legacy functions that will be removed in the future when major version 2 hits.
The modern versions are equivalent to them and have a more correct type hints.

| Legacy        | Modern          |
|---------------|-----------------|
| read          | parse_as_object |
| read_typetree | parse_as_dict   |
| save_typetree | patch           |


## Important Object Types

Now UnityPy uses [auto generated classes](UnityPy/classes/generated.py) with some useful extension methods and properties defined in [legacy_patch](UnityPy/classes/legacy_patch/). You can search for a specific classes in the module `UnityPy.classes` with your IDE's autocompletion.

### Texture2D

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
        tex = obj.parse_as_object()
        path = os.path.join(export_dir, f"{tex.m_Name}.png")
        tex.image.save(path)
        # edit texture
        fp = os.path.join(replace_dir, f"{tex.m_Name}.png")
        pil_img = Image.open(fp)
        tex.image = pil_img
        tex.save()
```

### Sprite

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
        sprite = obj.parse_as_object()
        path = os.path.join(export_dir, f"{sprite.m_Name}.png")
        sprite.image.save(path)
```

### TextAsset

TextAssets are usually normal text files.

-   `.m_Name`
-   `.m_Script` - str

Some games save binary data as TextAssets.
As ``m_Script`` gets handled as str by default,
use ``m_Script.encode("utf-8", "surrogateescape")`` to retrieve the original binary data.

**Export**

```python
for obj in env.objects:
    if obj.type.name == "TextAsset":
        # export asset
        txt = obj.parse_as_object()
        path = os.path.join(export_dir, f"{txt.m_Name}.txt")
        with open(path, "wb") as f:
            f.write(txt.m_Script.encode("utf-8", "surrogateescape"))
        # edit asset
        fp = os.path.join(replace_dir, f"{txt.m_Name}.txt")
        with open(fp, "rb") as f:
            txt.m_Script = f.read().decode("utf-8", "surrogateescape")
        txt.save()
```

### MonoBehaviour

MonoBehaviour assets are usually used to save the class instances with their values.
The structure/typetree for these classes might not be contained in the asset files.
In such cases see the 2nd example (TypeTreeGenerator) below.

-   `.m_Name`
-   `.m_Script`
-   custom data

**Export**

```python
import json

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        # export
        # save decoded data
        tree = obj.parse_as_dict()
        fp = os.path.join(extract_dir, f"{tree['m_Name']}.json")
        with open(fp, "wt", encoding = "utf8") as f:
            json.dump(tree, f, ensure_ascii = False, indent = 4)

        # edit
        tree = obj.parse_as_dict()
        # apply modifications to the data within the tree
        obj.patch(tree)
```

**TypeTreeGenerator**

UnityPy can generate the typetrees of MonoBehaviours from the game assemblies using an optional package, ``TypeTreeGeneratorAPI``, which has to be installed via pip.
UnityPy will automatically try to generate the typetree of MonoBehaviours if the typetree is missing in the assets and ``env.typetree_generator`` is set.

```python
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

# create generator
GAME_ROOT_DIR: str
# e.g. r"D:\Program Files (x86)\Steam\steamapps\common\Aethermancer Demo"
GAME_UNITY_VERSION: str
# you can get the version via an object
# e.g. objects[0].assets_file.unity_version

generator = TypeTreeGenerator(GAME_UNITY_VERSION)
generator.load_local_game(GAME_ROOT_DIR)
# generator.load_local_game(root_dir: str) - for a Windows game
# generator.load_dll_folder(dll_dir: str) - for mono / non-il2cpp or generated dummies
# generator.load_dll(dll: bytes)
# generator.load_il2cpp(il2cpp: bytes, metadata: bytes)

env = UnityPy.load(fp)
# assign generator to env
env.typetree_generator = generator
for obj in objects:
    if obj.type.name == "MonoBehaviour":
        # automatically tries to use the generator in the background if necessary
        x = obj.parse_as_object()
```


### AudioClip

-   `.samples` - `{sample-name : sample-data}`

The samples are converted into the .wav format.
The sample data is a .wav file in bytes.

```python
clip: AudioClip
for name, data in clip.samples.items():
    with open(name, "wb") as f:
        f.write(data)
```

### Font

**Export**

```python
if obj.type.name == "Font":
    font: Font = obj.parse_as_object()
    if font.m_FontData:
        extension = ".ttf"
        if font.m_FontData[0:4] == b"OTTO":
            extension = ".otf"

    with open(os.path.join(path, font.m_Name+extension), "wb") as f:
        f.write(font.m_FontData)
```

### Mesh

-   `.export()` - mesh exported as .obj (str)

The mesh will be converted to the Wavefront .obj file format.

```python
mesh: Mesh
with open(f"{mesh.m_Name}.obj", "wt", newline = "") as f:
    # newline = "" is important
    f.write(mesh.export())
```

### Renderer, MeshRenderer, SkinnedMeshRenderer

ALPHA-VERSION

-   `.export(export_dir)` - exports the associated mesh, materials, and textures into the given directory

The mesh and materials will be in the Wavefront formats.

```python
mesh_renderer: Renderer
export_dir: str

if mesh_renderer.m_GameObject:
    # get the name of the model
    game_obj_reader = mesh_renderer.m_GameObject.deref()
    game_obj_name = game_obj_reader.peek_name()
    export_dir = os.path.join(export_dir, game_obj_name)
mesh_renderer.export(export_dir)
```

### Texture2DArray

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
        tex_arr = obj.parse_as_object()
        for i, image in enumerate(tex_arr.images):
            image.save(os.path.join(path, f"{tex_arr.m_Name}_{i}.png"))
        # editing isn't supported yet!
```

## Configurations

There're several configurations and interfaces that provide the customizability to UnityPy.

### Unity CN Decryption

The Chinese version of Unity has its own builtin option to encrypt AssetBundles/BundleFiles. As it's a feature of Unity itself, and not a game specific protection, it is included in UnityPy as well.
To enable encryption simply use the code as follow, with `key` being the value that the game that loads the bundles passes to `AssetBundle.SetAssetBundleDecryptKey`.

```python
import UnityPy
UnityPy.set_assetbundle_decrypt_key(key)
```

### Unity Fallback Version

In case UnityPy failed to detect the Unity version of the game assets, you can set a fallback version. e.g.

```python
import UnityPy.config
UnityPy.config.FALLBACK_UNITY_VERSION = "2.5.0f5"
```

### Disable Typetree C-Implementation

The [C-implementation](UnityPyBoost/) of typetree reader can boost the parsing of typetree by a lot. If you want to disable it and use pure Python reader, you can put the following 2 lines in your main file.

```python
from UnityPy.helpers import TypeTreeHelper
TypeTreeHelper.read_typetree_boost = False
```

### Custom Block (De)compression

Some game assets have non-standard compression/decompression algorithm applied on the block data. If you wants to customize the compression/decompression function, you can modify the corresponding function mapping. e.g.

```python
from UnityPy.enums.BundleFile import CompressionFlags
flag = CompressionFlags.LZHAM

from UnityPy.helpers import CompressionHelper
CompressionHelper.COMPRESSION_MAP[flag] = custom_compress
CompressionHelper.DECOMPRESSION_MAP[flag] = custom_decompress
```

-   `custom_compress(data: bytes) -> bytes` (where bytes can also be bytearray or memoryview)
-   `custom_decompress(data: bytes, uncompressed_size: int) -> bytes`

### Custom Filesystem

UnityPy uses [fsspec](https://github.com/fsspec/filesystem_spec) under the hood to manage all filesystem interactions.
This allows using various different types of filesystems without having to change UnityPy's code.
It also means that you can use your own custom filesystem to e.g. handle indirection via catalog files, load assets on demand from a server, or decrypt files.

Following methods of the filesystem have to be implemented for using it in UnityPy.

-   `sep` (not a function, just the separator as character)
-   `isfile(self, path: str) -> bool`
-   `isdir(self, path: str) -> bool`
-   `exists(self, path: str, **kwargs) -> bool`
-   `walk(self, path: str, **kwargs) -> Iterable[List[str], List[str], List[str]]`
-   `open(self, path: str, mode: str = "rb", **kwargs) -> file` ("rb" mode required, "wt" required for ModelExporter)
-   `makedirs(self, path: str, exist_ok: bool = False) -> bool`

## Credits

First of all,
thanks a lot to all contributors of UnityPy and all of its users.

Also, many thanks to:

-   [Perfare](https://github.com/Perfare) for creating and maintaining and every contributor of [AssetStudio](https://github.com/Perfare/AssetStudio)
-   [ds5678](https://github.com/ds5678) for the [TypeTreeDumps](https://github.com/AssetRipper/TypeTreeDumps) and the [custom minimal Tpk format](https://github.com/AssetRipper/Tpk)
-   [Razmoth](https://github.com/Razmoth) for figuring out and sharing Unity CN's AssetBundle decryption ([src](https://github.com/Razmoth/PGRStudio)).
-   [nesrak1](https://github.com/nesrak1) for figuring out the [Switch texture swizzling](https://github.com/nesrak1/UABEA/blob/master/TexturePlugin/Texture2DSwitchDeswizzler.cs)
-   xiop_13690 (discord) for figuring out unsolved issues of the ManagedReferencesRegistry

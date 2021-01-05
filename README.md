# UnityPy
[![Discord server invite](https://discordapp.com/api/guilds/603359898507673630/embed.png)](https://discord.gg/C6txv7M)
[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/UnityPy.svg)](https://pypi.python.org/pypi/UnityPy)
[![Win/Mac/Linux](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-informational)]()
[![MIT](https://img.shields.io/pypi/l/UnityPy.svg)](https://github.com/K0lb3/UnityPy/blob/master/LICENSE)
[![Build Status](https://travis-ci.com/K0lb3/UnityPy.svg?branch=master)](https://travis-ci.com/K0lb3/UnityPy)

A Unity asset extractor for Python based on [AssetStudio](https://github.com/Perfare/AssetStudio).

1. [Installation](#installation)
2. [Example](#example)
3. [Important Classes](#important-classes)
4. [Important Object Types](#important-object-types)
5. [Goals](#goals)
6. [Motivation](#motivation)
7. [Community](#community)

## Installation

**Python 3.6.0 or higher is required**

```cmd
pip install UnityPy
```

or download/clone the git and use

```cmd
python setup.py install
```

## Example

The following is a simple example.

```python
import os
from UnityPy import AssetsManager

def unpack_all_assets(source_folder : str, destination_folder : str):
    # iterate over all files in source folder
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            # generate file_path
            file_path = os.path.join(root, file_name)
            # load that file via AssetsManager
            am = AssetsManager(file_path)

            # iterate over all assets and named objects
            for asset in am.assets.values():
                for obj in asset.objects.values():
                    # only process specific object types
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
```

You probably have to read [Important Classes](#important-classes)
and [Important Object Types](#important-object-types) to understand how it works.

People who have slightly advanced python skills should take a look at [AssetBatchConverter.py](AssetBatchConverter.py) for a more advanced example.


## Important Classes

### [AssetsManager](UnityPy/AssetsManager.py)

AssetsManager loads and parses the files that are given to it.
It can be initialized via:

* a file path - apk files can be loaded as well
* a folder path - loads all files in that folder (bad idea for folders with a lot of files)
* a stream - e.g. io.BytesIO, filestream,...
* a bytes object - will be loaded into a stream

UnityPy can detect itself if the file is a WebFile, BundleFile, Asset or APK itself.

The unpacked assets will be loaded into ``.assets``, which is a dict consisting of ``asset-name : asset``.

```python
from UnityPy import AssetsManager
am = AssetsManager(src)

for asset_name, asset in am.assets.items():
    pass
```

### [Asset](UnityPy/files/SerializedFile.py)

Assets are a container that contains multiple objects.
One of these objects can be an AssetBundle, which contains a file path for some of the objects in the same asset.

All objects can be found in the ``.objects`` dict - ``{ID : object}``.

The objects which have a file path can be found in the ``.container`` dict - ``{path : object}``.

### [Object](UnityPy/ObjectReader.py)

Objects contain the *actual* files which, e.g. textures, text files, meshes, settings, ...

To acquire the actual data of an object it has to be read first, this happens via the ``.read()`` function. This isn't done automatically to save time because only a small part of the objects are of interest. Serialized objects can be set with raw data using ``.set_raw_data(data)`` or modified with ``.save()`` function if supported.

## Important Object Types

All object types can be found in [UnityPy/classes](UnityPy/classes/).

### [Texture2D](UnityPy/classes/Texture2D.py)

* ``.name``
* ``.image`` converts the texture into a ``PIL.Image``
* ``.m_Width`` - texture width (int)
* ``.m_Height`` - texture height (int)

### [Sprite](UnityPy/classes/Sprite.py)

Sprites are part of a texture and can have a separate alpha-image as well.
Unlike most other extractors (including AssetStudio) UnityPy merges those two images by itself.

* ``.name``
* ``.image`` - converts the merged texture part into a ``PIL.Image``
* ``.m_Width`` - sprite width (int)
* ``.m_Height`` - sprite height (int)

### [TextAsset](UnityPy/classes/TextAsset.py)

TextAssets are usually normal text files.

* ``.name``
* ``.script`` - binary data (bytes)
* ``.text`` - script decoded via UTF8 (str)

Some games save binary data as TextFile, so it's usually better to use ``.script``.

### [MonoBehaviour](UnityPy/classes/MonoBehaviour.py)

MonoBehaviour assets are usually used to save the class instances with their values.
If a type tree exists it can be used to read the whole data,
but if it doesn't, then it is usually necessary to investigate the class that loads the specific MonoBehaviour to extract the data.

* ``.name``
* ``.script``- binary data (bytes)

### [AudioClip](UnityPy/classes/AudioClip.py)

* ``.samples`` - ``{sample-name : sample-data}`` dict

The samples are converted into the .wav format.
The sample-data is a .wav file in bytes.

```python
clip : AudioClip
for name, data in clip.samples.items():
    with open(name, "wb") as f:
        f.write(data)
```

## Goals

### WIP

- [x] A documentation
- [x] The ability to edit assets (like in UABE)

### TODO

- [ ] Support for more object types
- [ ] Code optimization
- [ ] Speed-ups via C-extensions
- [ ] Multiprocessing

## Motivation

I'm an active data-miner and noticed that unitypack has problems with new unity assets.
The problem in unitypack isn't that easy to fix and the undocumented code is a bit hard to understand.
That's why I tried other tools like UABE and AssetStudio. Sadly none of these tools can be used like unitypack.
That's why I started this project.

## Community

### [Discord](https://discord.gg/C6txv7M)

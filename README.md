# UnityPy
[![Discord server invite](https://discordapp.com/api/guilds/603359898507673630/embed.png)](https://discord.gg/C6txv7M)
[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/UnityPy.svg)](https://pypi.python.org/pypi/UnityPy)
[![Win/Mac/Linux](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-informational)]()
[![MIT](https://img.shields.io/pypi/l/UnityPy.svg)](https://github.com/K0lb3/UnityPy/blob/master/LICENSE)
[![Build Status](https://travis-ci.com/K0lb3/UnityPy.svg?branch=master)](https://travis-ci.com/K0lb3/UnityPy)

A Unity asset extractor for Python based on [AssetStudio](https://github.com/Perfare/AssetStudio).

1. [Installation](https://github.com/K0lb3/UnityPy#installation)
2. [Example](https://github.com/K0lb3/UnityPy#example)
3. [Important Classes](https://github.com/K0lb3/UnityPy#important-classes)
4. [Important Object Types](https://github.com/K0lb3/UnityPy#important-object-types)
5. [Goals](https://github.com/K0lb3/UnityPy#goals)
6. [Motivation](https://github.com/K0lb3/UnityPy#motivation)
7. [Community](https://github.com/K0lb3/UnityPy#community)

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

You probably have to read [Important Classes](https://github.com/K0lb3/UnityPy#important-classes)
and [Important Object Types](https://github.com/K0lb3/UnityPy#important-object-types) to understand how it works.

People who have slightly advanced python skills should take a look at [AssetBatchConverter.py](https://github.com/K0lb3/UnityPy/blob/master/AssetBatchConverter.py) for a more advanced example.


## Important Classes

### [AssetsManager](https://github.com/K0lb3/UnityPy/blob/master/UnityPy/AssetsManager.py)

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

### [Asset]((https://github.com/K0lb3/UnityPy/blob/master/UnityPy/files/SerializedFile.py))

Assets are a container that contains multiple objects.
One of these objects can be an AssetBundle, which contains a file path for some of the objects in the same asset.

All objects can be found in the ``.objects`` dict - ``{ID : object}``.

The objects which have a file path can be found in the ``.container`` dict - ``{path : object}``.

### [Object]((https://github.com/K0lb3/UnityPy/blob/master/UnityPy/ObjectReader.py))

Objects contain the *actual* files which, e.g. textures, text files, meshes, settings, ...

To acquire the actual data of an object it has to be read first, this happens via the ``.read()`` function. This isn't done automatically to save time because only a small part of the objects are of interest.

## Important Object Types

All object types can be found in [UnityPy/classes](https://github.com/K0lb3/UnityPy/tree/master/UnityPy/classes).

### [Texture2D](https://github.com/K0lb3/UnityPy/blob/master/UnityPy/classes/Texture2D.py)

* ``.name``
* ``.image`` converts the texture into a ``PIL.Image``
* ``.m_Width`` - texture width (int)
* ``.m_Height`` - texture height (int)

### [Sprite](https://github.com/K0lb3/UnityPy/blob/master/UnityPy/classes/Sprite.py)

Sprites are part of a texture and can have a separate alpha-image as well.
Unlike most other extractors (including AssetStudio) UnityPy merges those two images by itself.

* ``.name``
* ``.image`` - converts the merged texture part into a ``PIL.Image``
* ``.m_Width`` - sprite width (int)
* ``.m_Height`` - sprite height (int)

### [TextAsset](https://github.com/K0lb3/UnityPy/blob/master/UnityPy/classes/TextAsset.py)

TextAssets are usually normal text files.

* ``.name``
* ``.script`` - binary data (bytes)
* ``.text`` - script decoded via UTF8 (str)

Some games save binary data as TextFile, so it's usually better to use ``.script``.

### [MonoBehaviour](https://github.com/K0lb3/UnityPy/blob/master/UnityPy/classes/MonoBehaviour.py)

MonoBehaviour assets are usually binary data that has to be decoded.
e.g. via msgpack, protobuf

* ``.name``
* ``.script``- binary data (bytes)

### [AudioClip](https://github.com/K0lb3/UnityPy/blob/master/UnityPy/classes/AudioClip.py)

* ``.samples`` - ``{sample-name : sample-data}`` dict

## Goals

### WIP

* a documentation
* the ability to edit assets (like in UABE)

### planned

* support for more object types
* code optimization
* speed-ups via C-extensions
* multiprocessing

## Motivation

I'm an active data-miner and noticed that unitypack has problems with new unity assets.
The problem in unitypack isn't that easy to fix and the undocumented code is a bit hard to understand.
That's why I tried other tools like UABE and AssetStudio. Sadly none of these tools can be used like unitypack.
That's why I started this project.

## Community

[Discord](https://discord.gg/C6txv7M)

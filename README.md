# UnityPy
A unity asset extractor based on [unitypack](https://github.com/HearthSim/UnityPack) and [AssetStudio](https://github.com/Perfare/AssetStudio).

The basic structure is from AssetStudio and the object handling is from unitypack.

## Installation
```cmd
pip install UnityPy
```

## Usage
```python
from UnityPy.AssetManager import AssetManager

am = AssetManager()

# Load file via file path
am.LoadFile(fp)
# Load all files in a folder
am.LoadFolder(fp)

# Reads the objects of all loaded asset files
am.ReadAssets()

# the structure of the objects is the same as in unitypack
for assetsfile in am.assetsFileList:
    for id, obj in assetsFile.Objects.items():
        # the objects are already loaded, so you don't have to do data = obj.read()
        pass
````

## Goals
### near future
* clean-up of the code
* adding a documentation

### far future
* ability to edit assets (like in UABE)
* broader object type support
* code optimization
* multiprocessing

## Motivation
I'm an active data-miner and noticed that unitypack has problems with new unity assets.
The problem in unitypack isn't that easy to fix and the undocumented code is a bit hard to understand.
That's why I tried other tools like UABE and AssetStudio. Sadly none of these tools can be used like unitypack.
That's why I started this project.

## License
UnityPy is licensed under the terms of the MIT license. The full license text is available in the LICENSE file.

## Community
[Discord](https://discord.gg/C6txv7M)

# UnityPy
A unity asset extractor based on [unitypack](https://github.com/HearthSim/UnityPack) and [AssetStudio](https://github.com/Perfare/AssetStudio).

The basic structure is from AssetStudio and the object handling is from unitypack.

## Installation
```cmd
pip install UnityPy
```

## Usage
```python
from UnityPy import AssetManager

am = AssetManager()

# Load file via file path
am.load_file(fp)
# Load all files in a folder
am.load_folder(fp)

for name, asset in am.assets.items():
    for id, obj in asset.objects.items():
        data = obj.read()
````

## Goals
### near future
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

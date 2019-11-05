# UnityPy
A Unity asset extractor based on [AssetStudio](https://github.com/Perfare/AssetStudio).

## Installation

## UnityPy

### main module
```cmd
pip install UnityPy
```

or download/clone the git and use
```cmd
python setup.py install
```

### optional modules
It's highly recommended to install following modules to enjoy the full power of UnityPy.

All texture modules use [Cython](https://cython.org/),  so they won't work on some systems.

Windows users have to install [Microsoft Visual C++ 14.0 Build Tools Only](http://go.microsoft.com/fwlink/?LinkId=691126&fixForIE=.exe) to be able to use Cython.

* [python-fsb5](https://github.com/HearthSim/python-fsb5) - FSB Audio Sample Support
```cmd
pip install fsb5
```

* [decrunch](https://github.com/HearthSim/decrunch) - crunch texture support
```cmd
pip install decrunch
```
* [etcpack](https://github.com/K0lb3/etcpack) - ETC texture support
```cmd
pip install etcpack
```
* [pvrtc_decoder](https://github.com/K0lb3/pvrtc_decoder) - PVRTC Texture Support
```cmd
pip install pvrtc_decoder
```
* [astc_decomp](https://github.com/K0lb3/astc_decomp) - ASTC Texture Support
```cmd
pip install astc_decomp
```

## Usage
```python
from UnityPy import AssetsManager

am = AssetsManager()

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

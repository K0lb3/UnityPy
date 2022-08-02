from setuptools import setup, Extension, find_packages
import os
import re

INSTALL_DIR = os.path.dirname(os.path.realpath(__file__))
UNITYPYBOOST_DIR = os.path.join(INSTALL_DIR, "UnityPyBoost")

version = None
with open(os.path.join(INSTALL_DIR, "UnityPy", "__init__.py"), "rt") as f:
    version = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)

with open(os.path.join(INSTALL_DIR, "README.md"), "rt") as fh:
    long_description = fh.read()


def get_fmod_library():
    import platform

    # determine system - Windows, Darwin, Linux, Android
    system = platform.system()
    if system == "Linux" and "ANDROID_BOOTLOGO" in os.environ:
        system = "Android"
    # determine architecture
    machine = platform.machine()
    arch = platform.architecture()[0]

    lib_name = ""
    if system in ["Windows", "Darwin"]:
        lib_name = "fmod.dll" if system == "Windows" else "libfmod.dylib"
        if arch == "32bit":
            arch = "x86"
        elif arch == "64bit":
            arch = "x64"
    elif system == "Linux":
        lib_name = "libfmod.so"
        # Raspberry Pi and Linux on arm projects
        if "arm" in machine:
            if arch == "32bit":
                arch = "armhf" if machine.endswith("l") else "arm"
            elif arch == "64bit":
                return None
        elif arch == "32bit":
            arch = "x86"
        elif arch == "64bit":
            arch = "x86_64"
    else:
        return None

    return f"lib/FMOD/{system}/{arch}/{lib_name}"


setup(
    name="UnityPy",
    packages=find_packages(),
    #include_package_data=True,
    package_data={
        "UnityPy": [
            get_fmod_library(),
            "resources/uncompressed.tpk",
            "*.c",
            "*.h",
            "*.cpp",
            "*.hpp",
        ]
    },
    version=version,
    author="K0lb3",
    description="A pythonic port of AssetStudio by Perfare",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/K0lb3/UnityPy",
    download_url="https://github.com/K0lb3/UnityPy/tarball/master",
    keywords=[
        "python",
        "unity",
        "unity-asset",
        "python3",
        "data-minig",
        "unitypack",
        "assetstudio",
        "unity-asset-extractor",
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Games/Entertainment",
        "Topic :: Multimedia :: Graphics",
    ],
    install_requires=[
        # block compression/decompression
        "lz4",  # BundleFile block compression
        "brotli",  # WebFile compression
        # Texture & Sprite handling
        "Pillow",
        "texture2ddecoder",  # texture decompression
        "etcpak",  # ETC & DXT compression
        # raw typetree dumping
        "tabulate",
    ],
    ext_modules=[
        Extension(
            "UnityPy.UnityPyBoost",
            [
                f"UnityPyBoost/{f}"
                for f in os.listdir(UNITYPYBOOST_DIR)
                if f.endswith(".c")
            ],
            language="c",
            include_dirs=[UNITYPYBOOST_DIR],
        )
    ],
)

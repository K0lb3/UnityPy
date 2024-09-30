import os
import platform
import re
import subprocess

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

INSTALL_DIR = os.path.dirname(os.path.realpath(__file__))
UNITYPYBOOST_DIR = os.path.join(INSTALL_DIR, "UnityPyBoost")


class BuildExt(build_ext):
    def build_extensions(self):
        cpp_version_flag: str
        compiler = self.compiler
        # msvc - only ever used c++20, never c++2a
        if compiler.compiler_type == "msvc":
            cpp_version_flag = "/std:c++20"
        # gnu & clang
        elif compiler.compiler_type == "unix":
            res = subprocess.run(
                [compiler.compiler[0], "-v"],
                capture_output=True,
            )
            # for some reason g++ and clang++ return this as error
            text = (res.stdout or res.stderr).decode("utf-8")
            version = re.search(r"version\s+(\d+)\.", text)
            if version is None:
                raise Exception("Failed to determine compiler version")
            version = int(version.group(1))
            if version < 10:
                cpp_version_flag = "-std=c++2a"
            else:
                cpp_version_flag = "-std=c++20"
        else:
            cpp_version_flag = "-std=c++20"

        for ext in self.extensions:
            ext.extra_compile_args = [cpp_version_flag]

        build_ext.build_extensions(self)


def get_fmod_library():
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


unitypy_package_data = ["resources/uncompressed.tpk"]
fmod_lib = get_fmod_library()
if fmod_lib is not None:
    unitypy_package_data.append(fmod_lib)


# These packages are missing __init__.py so setuptools will warn about unspecified packages
extra_packages = [
    "UnityPy.resources",
    "UnityPy.tools",
    "UnityPy.tools.libil2cpp_helper",
]


setup(
    name="UnityPy",
    packages=find_packages() + extra_packages,
    package_data={"UnityPy": unitypy_package_data},
    ext_modules=[
        Extension(
            "UnityPy.UnityPyBoost",
            [
                f"UnityPyBoost/{f}"
                for f in os.listdir(UNITYPYBOOST_DIR)
                if f.endswith(".cpp")
            ],
            language="c++",
            include_dirs=[UNITYPYBOOST_DIR],
        )
    ],
    cmdclass={"build_ext": BuildExt},
)

import os
import re
import subprocess
from typing import Union

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext
from setuptools.command.sdist import sdist

try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:
    from wheel.bdist_wheel import bdist_wheel


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


class SDist(sdist):
    def make_distribution(self) -> None:
        # add all fmod libraries to the distribution
        for root, dirs, files in os.walk("UnityPy/lib/FMOD"):
            for file in files:
                fp = f"{root}/{file}"
                if fp not in self.filelist.files:
                    self.filelist.files.append(fp)
        return super().make_distribution()


BDIST_TAG_FMOD_MAP = {
    # Windows
    "win32": "x86",
    "win_amd64": "x64",
    "win_arm64": "arm",
    # Linux and Mac endings
    "arm64": "arm64",  # Mac
    "x86_64": "x64",
    "aarch64": "arm64",  # Linux
    "i686": "x86",
    "armv7l": "arm",  # armhf
}


def get_fmod_path(
    system: Union["Windows", "Linux", "Darwin"], arch: ["x64", "x86", "arm", "arm64"]
) -> str:
    if system == "Darwin":
        # universal dylib
        return "lib/FMOD/Darwin/libfmod.dylib"

    if system == "Windows":
        return f"lib/FMOD/Windows/{arch}/fmod.dll"

    if system == "Linux":
        if arch == "x64":
            arch = "x86_64"
        return f"lib/FMOD/Linux/{arch}/libfmod.so"

    raise NotImplementedError(f"Unsupported system: {system}")


class BDistWheel(bdist_wheel):
    def run(self):
        platform_tag = self.get_tag()[2]
        if platform_tag.startswith("win"):
            system = "Windows"
            arch = BDIST_TAG_FMOD_MAP[platform_tag]
        else:
            arch = next(
                (v for k, v in BDIST_TAG_FMOD_MAP.items() if platform_tag.endswith(k)),
                None,
            )
            if platform_tag.startswith("macosx"):
                system = "Darwin"
            else:
                system = "Linux"

        try:
            self.distribution.package_data["UnityPy"].append(
                get_fmod_path(system, arch)
            )
        except NotImplementedError:
            pass
        super().run()


setup(
    name="UnityPy",
    packages=find_packages(),
    package_data={"UnityPy": ["resources/uncompressed.tpk"]},
    ext_modules=[
        Extension(
            "UnityPy.UnityPyBoost",
            [
                f"UnityPyBoost/{f}"
                for f in os.listdir(UNITYPYBOOST_DIR)
                if f.endswith(".cpp")
            ],
            depends=[
                f"UnityPyBoost/{f}"
                for f in os.listdir(UNITYPYBOOST_DIR)
                if f.endswith(".hpp")
            ],
            language="c++",
            include_dirs=[UNITYPYBOOST_DIR],
        )
    ],
    cmdclass={"build_ext": BuildExt, "sdist": SDist, "bdist_wheel": BDistWheel},
)

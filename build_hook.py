import os

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        # set infer_tag to True to let hatchling infer the correct platform tag
        build_data["infer_tag"] = True
        # -
        build_data["pure_python"] = False

        # add fmod lib for the target platform
        fmod_lib = get_fmod_library()
        if fmod_lib:
            print(f"Using fmod lib: {fmod_lib}")
            build_data["force_include"][fmod_lib] = fmod_lib
        else:
            print("No fmod lib found for the target platform")

        # compile and add UnityPyBoost
        boost_fp = build_UnityPyBoost(self.root)
        build_data["force_include"][boost_fp] = boost_fp


def build_UnityPyBoost(build_dir: str) -> str:
    from distutils.core import setup, Extension
    print("Building UnityPyBoost")
    UnityPyBoost_dir = os.path.join(build_dir, "UnityPyBoost")
    setup(
        name="UnityPy",
        packages=["UnityPy"],
        script_args=["build_ext", "--inplace"],
        ext_modules=[
            Extension(
                "UnityPy.UnityPyBoost",
                [
                    f"UnityPyBoost/{f}"
                    for f in os.listdir(UnityPyBoost_dir)
                    if f.endswith(".c")
                ],
                language="c",
                include_dirs=[UnityPyBoost_dir],
            )
        ],
    )
    print("Done building UnityPyBoost")
    # return the path to the built UnityPyBoost
    lib_ext = ".pyd" if os.name == "nt" else ".so" 
    for f in os.listdir(os.path.join(build_dir, "UnityPy")):
        if f.endswith(lib_ext):
            return f"UnityPy/{f}"
    else:
        raise Exception("Compiled UnityPyBoost was not found")


def get_fmod_library() -> str:
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

    return f"UnityPy/lib/FMOD/{system}/{arch}/{lib_name}"

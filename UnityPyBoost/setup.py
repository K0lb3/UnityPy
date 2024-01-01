from setuptools import setup, Extension
import os

local = os.path.dirname(os.path.abspath(__file__))

setup(
    name="UnityPyBoost",
    description="TODO",
    author="K0lb3",
    version="0.0.3",
    ext_modules=[
        Extension(
            "UnityPyBoost",
            [os.path.join(local, f) for f in os.listdir(local) if f.endswith(".c")],
            language="c",
            include_dirs=[local],
        )
    ],
)

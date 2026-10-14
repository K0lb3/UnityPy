import os

import UnityPy
from UnityPy.files import SerializedFile
from UnityPy.files.SerializedFile import FileIdentifier

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def write_serialized_files(directory):
    """main.assets, which lists dep.assets as an external, and dep.assets, both copies of a sample file"""
    env = UnityPy.load(os.path.join(SAMPLES, "banner_1"))
    bundle = next(iter(env.files.values()))
    serialized = next(f for f in bundle.files.values() if isinstance(f, SerializedFile))
    with open(os.path.join(directory, "dep.assets"), "wb") as f:
        f.write(serialized.save())

    external = object.__new__(FileIdentifier)
    external.path = "dep.assets"
    external.temp_empty = ""
    external.guid = bytes(16)
    external.type = 0
    serialized.externals.append(external)
    with open(os.path.join(directory, "main.assets"), "wb") as f:
        f.write(serialized.save())
    return len(serialized.objects)


def test_dependencies_are_not_listed_as_objects(tmp_path):
    object_count = write_serialized_files(str(tmp_path))
    env = UnityPy.load(os.path.join(str(tmp_path), "main.assets"))
    assert len(env.objects) == object_count
    main = next(iter(env.files.values()))

    main.load_dependencies()
    dependency = env.get_cab("dep.assets")
    assert isinstance(dependency, SerializedFile)
    assert dependency.is_dependency
    assert len(env.objects) == object_count

"""
This script shows how to create a bundle from dumped assets from the memory.

The dumped assets consist of SerializedFiles and their resources(cabs).
A sample file of the original game is required for this script.
This example uses the globalgamemanager as this asset should exist in all Unity games.
"""

import os
import uuid
import random
from copy import copy
import re

import UnityPy
from UnityPy.enums import ClassIDType
from UnityPy.files import BundleFile
from UnityPy.files.SerializedFile import FileIdentifier, ObjectReader, SerializedType


SERIALIZED_PATH = r"globalgamemanagers"
DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


def main():
    bf = Fake(
        signature="UnityFS",
        version=6,
        format=6,
        version_engine="2017.4.30f1",
        version_player="5.x.x",
        _class=BundleFile,
        files={},
    )
    # load default serialized file and prepare some variables for easier access to key objects
    env = UnityPy.load(SERIALIZED_PATH)
    sf = env.file  # serialized file
    or_bp = list(sf.objects.values())[0].__dict__  # object data

    bf.files["serialized_file"] = sf
    sf.flags = 4

    # remove all unnesessary stuff
    for key in list(sf.objects.keys()):
        del sf.objects[key]
    sf.externals = []

    # add all files from DATA_PATH
    for root, dirs, files in os.walk(DATA_PATH):
        for f in files:
            fp = os.path.join(root, f)
            if f[:3] == "CAB":
                add_cab(bf, sf, root, f)
            else:
                add_object(sf, fp, or_bp)

    # save edited bundle
    open("bundle_edited.unity3d", "wb").write(bf.save())


def add_cab(bf, sf, root, f):
    fp = os.path.join(root, f)
    bf.files[f] = Fake(data=open(fp, "rb").read(), flags=4)
    sf.externals.append(
        Fake(
            temp_empty="",
            guid=generate_16_byte_uid(),
            path=f"archive:/{os.path.basename(root)}/{f}",
            type=0,
            _class=FileIdentifier,
        )
    )


def add_object(sf, fp, or_bp):
    # get correct type id
    path_id, class_name = os.path.splitext(os.path.basename(fp))
    path_id = int(path_id) if re.match(
        r"^\d+$", path_id) else generate_path_id(sf.objects)
    class_id = getattr(
        ClassIDType, class_name[1:], ClassIDType.UnknownType).value
    type_id = -1
    for i, styp in enumerate(sf.types):
        if styp.class_id == class_id:
            type_id = i
    if type_id == -1:  # not found, add type
        type_id = len(sf.types)
        sf.types.append(
            Fake(
                class_id=class_id,
                is_stripped_type=False,
                node=[],
                script_type_index=-1,
                old_type_hash=generate_16_byte_uid(),
                _class=SerializedType,
            )
        )

    # add new object
    odata = copy(or_bp)
    odata.update(
        {
            "data": open(fp, "rb").read(),
            "path_id": generate_path_id(sf.objects),
            "class_id": class_id,
            "type_id": type_id,
        }
    )
    sf.objects[path_id] = Fake(**odata, _class=ObjectReader)


def generate_path_id(objects):
    while True:
        uid = random.randint(-(2 ** 16), 2 ** 16 - 1)
        if uid not in objects:
            return uid


def generate_16_byte_uid():
    return uuid.uuid1().urn[-16:].encode("ascii")


class Fake(object):
    """
    fake class for easy class creation without init call
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        if "_class" in kwargs:
            self.__class__ = kwargs["_class"]

    def save(self):
        return self.data


if __name__ == "__main__":
    main()
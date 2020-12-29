"""
This example shows how to write a custom MonoBehaviour class.


The script is for a game that generates its encryption key based on a specific image.
This image is linked to by a MonoBheaviour called "ScriptableTexture2D".
It is linked to by a pointer after the default MonoBehaviour structure.
This intel was acquired from the assembly of the game.

Unfortunately, the asset doesn't have a type-tree, so the default MonoBehaviour class can't find the pointer.
So a custom MonoBehaviour class is required to get the pointer comfortably.
Doing so is simple, as seen in the following code.
"""

import os
import UnityPy
from UnityPy.classes import MonoBehaviour, PPtr

class ScriptableTexture2D(MonoBehaviour):
    def __init__(self, reader):
        # calls the default MonoBehaviour init
        super().__init__(reader=reader)
        # here goes the implementation of the extra data
        self.texture = PPtr(reader)

# set the path for the target file
root = os.path.dirname(os.path.realpath(__file__))
fp = os.path.join(root,"data.unity3d")

env = UnityPy.load(fp)

# find the correct asset
for obj in env.objects:
    if obj.type == "MonoBehaviour":
        data = obj.read()
        if data.name == "ScriptableTexture2D":
            # correct obj found
            # lets read it with the custom class
            st = ScriptableTexture2D(obj)
            # read the linked image and save it
            tex = st.texture.read()
            print(st.texture.read().name)
            #tex.image.save(os.path.join(root, f"{tex.name}.png"))
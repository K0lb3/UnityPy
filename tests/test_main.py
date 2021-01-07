import os
SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def test_import():
    import UnityPy


def test_read():
    import UnityPy
    for f in os.listdir(SAMPLES):
        am = UnityPy.AssetsManager(os.path.join(SAMPLES, f))
        for asset in am.assets.values():
            for obj in asset.objects.values():
                obj.read()


def test_texture2d():
    import UnityPy
    for f in os.listdir(SAMPLES):
        am = UnityPy.AssetsManager(os.path.join(SAMPLES, f))
        for asset in am.assets.values():
            for obj in asset.objects.values():
                if obj.type == "Texture2D":
                    obj.read().image.save("test.png")


def test_sprite():
    import UnityPy
    for f in os.listdir(SAMPLES):
        am = UnityPy.AssetsManager(os.path.join(SAMPLES, f))
        for asset in am.assets.values():
            for obj in asset.objects.values():
                if obj.type == "Sprite":
                    obj.read().image.save("test.png")


def test_audioclip():
    import UnityPy
    import platform
    env = UnityPy.load(os.path.join(SAMPLES, "char_118_yuki.ab"))
    for obj in env.objects:
        if obj.type == "AudioClip":
            clip = obj.read()
            assert(len(clip.samples) == 1)


if __name__ == "__main__":
    for x in list(locals()):
        if str(x)[:4] == "test":
            locals()[x]()
    input("All Tests Passed")

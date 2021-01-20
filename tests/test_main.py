import os
import UnityPy
from PIL import Image
SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def test_read_single():
    for f in os.listdir(SAMPLES):
        env = UnityPy.load(os.path.join(SAMPLES, f))
        for obj in env.objects:
            obj.read()

def test_read_batch():
    env = UnityPy.load(SAMPLES)
    for obj in env.objects:
        obj.read()

def test_texture2d():
    import UnityPy
    for f in os.listdir(SAMPLES):
        env = UnityPy.load(os.path.join(SAMPLES, f))
        for obj in env.objects:
            if obj.type == "Texture2D":
                data = obj.read()
                data.image.save("test.png")
                data.image = data.image.transpose(Image.ROTATE_90)
                data.save()


def test_sprite():
    import UnityPy
    for f in os.listdir(SAMPLES):
        env = UnityPy.load(os.path.join(SAMPLES, f))
        for obj in env.objects:
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

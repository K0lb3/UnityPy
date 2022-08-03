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
    for f in os.listdir(SAMPLES):
        env = UnityPy.load(os.path.join(SAMPLES, f))
        for obj in env.objects:
            if obj.type == "Texture2D":
                data = obj.read()
                data.image.save("test.png")
                data.image = data.image.transpose(Image.ROTATE_90)
                data.save()


def test_sprite():
    for f in os.listdir(SAMPLES):
        env = UnityPy.load(os.path.join(SAMPLES, f))
        for obj in env.objects:
            if obj.type == "Sprite":
                obj.read().image.save("test.png")


def test_audioclip():
    env = UnityPy.load(os.path.join(SAMPLES, "char_118_yuki.ab"))
    for obj in env.objects:
        if obj.type == "AudioClip":
            clip = obj.read()
            assert len(clip.samples) == 1


def test_mesh():
    env = UnityPy.load(os.path.join(SAMPLES, "xinzexi_2_n_tex"))
    with open(os.path.join(SAMPLES, 'xinzexi_2_n_tex_mesh'), 'rb') as f:
        wanted = f.read().replace(b'\r', b'')
    for obj in env.objects:
        if obj.type == "Mesh":
            mesh = obj.read()
            data = mesh.export()
            if isinstance(data, str):
                data = data.encode('utf8').replace(b'\r', b'')
            assert data == wanted

def test_read_typetree():
    env = UnityPy.load(SAMPLES)
    for obj in env.objects:
        obj.read_typetree()

if __name__ == "__main__":
    for x in list(locals()):
        if str(x)[:4] == "test":
            locals()[x]()
    input("All Tests Passed")

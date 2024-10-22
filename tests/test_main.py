import io
import os
import platform

from PIL import Image

import UnityPy

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


def test_save_dict():
    env = UnityPy.load(SAMPLES)
    for obj in env.objects:
        data = obj.get_raw_data()
        item = obj.read_typetree(wrap=False)
        assert isinstance(item, dict)
        re_data = obj.save_typetree(item)
        assert data == re_data


def test_save_wrap():
    env = UnityPy.load(SAMPLES)
    for obj in env.objects:
        data = obj.get_raw_data()
        item = obj.read_typetree(wrap=True)
        assert not isinstance(item, dict)
        re_data = obj.save_typetree(item)
        assert data == re_data


def test_texture2d():
    for f in os.listdir(SAMPLES):
        env = UnityPy.load(os.path.join(SAMPLES, f))
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                data = obj.read()
                data.image.save(io.BytesIO(), format="PNG")
                data.image = data.image.transpose(Image.ROTATE_90)
                data.save()


def test_sprite():
    for f in os.listdir(SAMPLES):
        env = UnityPy.load(os.path.join(SAMPLES, f))
        for obj in env.objects:
            if obj.type.name == "Sprite":
                obj.read().image.save(io.BytesIO(), format="PNG")


if platform.system() == "Darwin":
    # crunch issue on macos leading to segfault
    del test_texture2d
    del test_sprite

def test_audioclip():
    # as not platforms are supported by FMOD
    # we have to check if the platform is supported first
    try:
        from UnityPy.export import AudioClipConverter

        AudioClipConverter.import_pyfmodex()
    except NotImplementedError:
        return
    except OSError:
        # cibuildwheel doesn't copy the .so files
        # so we have to skip the test on it
        print("Failed to load the fmod lib for your system.")
        print("Skipping the audioclip test.")
        return
    if AudioClipConverter.pyfmodex is False:
        return
    env = UnityPy.load(os.path.join(SAMPLES, "char_118_yuki.ab"))
    for obj in env.objects:
        if obj.type.name == "AudioClip":
            clip = obj.read()
            assert len(clip.samples) == 1


def test_mesh():
    env = UnityPy.load(os.path.join(SAMPLES, "xinzexi_2_n_tex"))
    with open(os.path.join(SAMPLES, "xinzexi_2_n_tex_mesh"), "rb") as f:
        wanted = f.read().replace(b"\r", b"")
    for obj in env.objects:
        if obj.type.name == "Mesh":
            mesh = obj.read()
            data = mesh.export()
            if isinstance(data, str):
                data = data.encode("utf8").replace(b"\r", b"")
            assert data == wanted


def test_read_typetree():
    env = UnityPy.load(SAMPLES)
    for obj in env.objects:
        obj.read_typetree()


def test_save():
    env = UnityPy.load(SAMPLES)
    # TODO - check against original
    # this only makes sure
    # that the save function still produces a readable file
    for name, file in env.files.items():
        if isinstance(file, UnityPy.streams.EndianBinaryReader):
            continue
        save1 = file.save()
        save2 = UnityPy.load(save1).file.save()
        assert save1 == save2


if __name__ == "__main__":
    for x in list(locals()):
        if str(x)[:4] == "test":
            locals()[x]()
    input("All Tests Passed")

import pytest

import UnityPy


def test_load_missing_file_raises():
    # silently returning an empty Environment hides typos and wrong paths
    with pytest.raises(FileNotFoundError):
        UnityPy.load("definitely_missing_file.unity3d")


def test_load_missing_dependency_stays_silent():
    # missing dependencies (e.g. unshipped externals) are normal and must be skipped
    env = UnityPy.Environment()
    assert env.load_file("no_such_dependency.assets", is_dependency=True) is None


def test_load_folder_still_works(tmp_path):
    (tmp_path / "dummy.asset").write_bytes(b"not a real unity file, just needs to exist")
    env = UnityPy.load(str(tmp_path))
    assert len(env.files) == 1


def test_load_bytes_still_works():
    env = UnityPy.load(b"UnityFS\x00")
    assert len(env.files) == 1

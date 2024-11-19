import gzip
import os

from UnityPy.files.BundleFile import BundleFile, BundleFileFS
from UnityPy.files.File import parse_file
from UnityPy.files.WebFile import WebFile
from UnityPy.streams.EndianBinaryReader import EndianBinaryReader

LOCAL = os.path.join(os.path.dirname(__file__), "samples")

WEBFILE_FP = os.path.join(LOCAL, "Build6_Web.data.gz")


def test_webfile():
    with open(WEBFILE_FP, "rb") as f:
        cdata = f.read()

    # test raw
    data = gzip.decompress(cdata)
    reader = EndianBinaryReader(data)
    webfile = parse_file(reader, "Build6_Web.data.gz")
    assert isinstance(webfile, WebFile)
    redata = webfile.dump().get_bytes()
    assert redata == data

    # test gzip compressed
    reader = EndianBinaryReader(cdata)
    webfile = parse_file(reader, "Build6_Web.data.gz")
    assert isinstance(webfile, WebFile)
    redata = webfile.dump().get_bytes()
    rereader = EndianBinaryReader(redata)
    re_webfile = parse_file(rereader, "Build6_Web.data.gz")
    assert isinstance(re_webfile, WebFile)
    assert all(
        [a == b for a, b in zip(webfile.directory_infos, re_webfile.directory_infos)]
    )


def _get_bundlefile_raw() -> bytes:
    with open(WEBFILE_FP, "rb") as f:
        cdata = f.read()

    reader = EndianBinaryReader(cdata)
    webfile = parse_file(reader, "Build6_Web.data.gz")
    for directory_info in webfile.directory_infos:
        if directory_info.path == "data.unity3d":
            webfile.directory_reader.seek(directory_info.offset)
            return webfile.directory_reader.read(directory_info.size)
    raise FileNotFoundError("data.unity3d not found in Build6_Web.data.gz")


def test_bundlefile_fs():
    cdata = _get_bundlefile_raw()

    reader = EndianBinaryReader(cdata)
    bundlefile = parse_file(reader, "data.unity3d", f"{WEBFILE_FP}/data.unity3d")
    assert isinstance(bundlefile, BundleFile)
    assert isinstance(bundlefile, BundleFileFS)
    redata = bundlefile.dump().get_bytes()
    rereader = EndianBinaryReader(redata)
    re_bundlefile = parse_file(rereader, "data.unity3d", f"{WEBFILE_FP}/data.unity3d")
    assert isinstance(re_bundlefile, BundleFile)
    assert isinstance(re_bundlefile, BundleFileFS)
    assert all(
        [
            a == b
            for a, b in zip(bundlefile.directory_infos, re_bundlefile.directory_infos)
        ]
    )
    print()


if __name__ == "__main__":
    test_webfile()
    test_bundlefile_fs()

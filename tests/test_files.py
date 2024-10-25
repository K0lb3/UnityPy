import gzip
import os

from UnityPy.files.File import parse_file
from UnityPy.files.WebFile import WebFile
from UnityPy.streams.EndianBinaryReader import EndianBinaryReader

LOCAL = os.path.join(os.path.dirname(__file__), "samples")


def test_webfile():
    fp = os.path.join(LOCAL, "Build6_Web.data.gz")
    with open(fp, "rb") as f:
        cdata = f.read()

    # test raw
    data = gzip.decompress(cdata)
    reader = EndianBinaryReader(data)
    webfile = parse_file(reader, "Build6_Web.data.gz", fp)
    assert isinstance(webfile, WebFile)
    redata = webfile.dump().get_bytes()
    assert redata == data

    # test gzip compressed
    reader = EndianBinaryReader(cdata)
    webfile = parse_file(reader, "Build6_Web.data.gz", fp)
    assert isinstance(webfile, WebFile)
    redata = webfile.dump().get_bytes()
    rereader = EndianBinaryReader(redata)
    re_webfile = parse_file(rereader, "Build6_Web.data.gz", fp)
    assert isinstance(re_webfile, WebFile)
    assert all(
        [a == b for a, b in zip(webfile.directory_infos, re_webfile.directory_infos)]
    )


if __name__ == "__main__":
    test_webfile()

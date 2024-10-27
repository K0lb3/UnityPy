# based on: https://github.com/Razmoth/PGRStudio/blob/master/AssetStudio/PGR/PGR.cs
import re
from typing import Tuple, Union

from ..streams import EndianBinaryReader

try:
    from UnityPy import UnityPyBoost
except ImportError:
    UnityPyBoost = None

UNITY3D_SIGNATURE = b"#$unity3dchina!@"
DECRYPT_KEY: bytes = None


def set_assetbundle_decrypt_key(key: Union[bytes, str]):
    if isinstance(key, str):
        key = key.encode("utf-8", "surrogateescape")
    if len(key) != 16:
        raise ValueError(
            f"AssetBundle Key length is wrong. It should be 16 bytes and now is {len(key)} bytes."
        )
    global DECRYPT_KEY
    DECRYPT_KEY = key


def read_vector(reader: EndianBinaryReader) -> Tuple[bytes, bytes]:
    data = reader.read_bytes(0x10)
    key = reader.read_bytes(0x10)
    reader.Position += 1

    return data, key


def decrypt_key(key: bytes, data: bytes, keybytes: bytes):
    from Crypto.Cipher import AES

    key = AES.new(keybytes, AES.MODE_ECB).encrypt(key)
    return bytes(x ^ y for x, y in zip(data, key))


def brute_force_key(
    fp: str,
    key_sig: bytes,
    data_sig: bytes,
    pattern: re.Pattern = re.compile(rb"(?=(\w{16}))"),
    verbose: bool = False,
):
    with open(fp, "rb") as f:
        data = f.read()

    matches = pattern.findall(data)
    for i, key in enumerate(matches):
        if verbose:
            print(f"Trying {i + 1}/{len(matches)} - {key}")
        signature = decrypt_key(key_sig, data_sig, key)
        if signature == UNITY3D_SIGNATURE:
            if verbose:
                print(f"Found key: {key}")
            return key
    return None


def to_uint4_array(source: bytes, offset: int = 0):
    buffer = bytearray(len(source) * 2)
    for j in range(len(source)):
        buffer[j * 2] = source[offset + j] >> 4
        buffer[j * 2 + 1] = source[offset + j] & 15
    return buffer


class ArchiveStorageDecryptor:
    unknown_1: int
    index: bytes
    substitute: bytes = bytes(0x10)

    def __init__(self, reader: EndianBinaryReader) -> None:
        self.unknown_1 = reader.read_u_int()

        # read vector data/key vectors
        self.data, self.key = read_vector(reader)
        self.data_sig, self.key_sig = read_vector(reader)

        if DECRYPT_KEY is None:
            raise LookupError(
                "\n".join(
                    [
                        "The BundleFile is encrypted, but no key was provided!",
                        "You can set the key via UnityPy.set_assetbundle_decrypt_key(key).",
                        "To try brute-forcing the key, use UnityPy.helpers.ArchiveStorageManager.brute_force_key(fp, key_sig, data_sig)",
                        f"with  key_sig = {self.key_sig}, data_sig = {self.data_sig},"
                        "and fp being the path to global-metadata.dat or a memory dump.",
                    ]
                )
            )

        signature = decrypt_key(self.key_sig, self.data_sig, DECRYPT_KEY)
        if signature != UNITY3D_SIGNATURE:
            raise Exception(f"Invalid signature {signature} != {UNITY3D_SIGNATURE}")

        data = decrypt_key(self.key, self.data, DECRYPT_KEY)
        data = to_uint4_array(data)
        self.index = data[:0x10]
        self.substitute = bytes(
            data[0x10 + i * 4 + j] for j in range(4) for i in range(4)
        )

    def decrypt_block(self, data: bytes, index: int):

        if UnityPyBoost:
            return UnityPyBoost.decrypt_block(self.index, self.substitute, data, index)

        offset = 0
        size = len(data)
        data = bytearray(data)
        view = memoryview(data)
        while offset < len(data):
            offset += self.decrypt(view[offset:], index, size - offset)
            index += 1
        return data

    def decrypt_byte(self, view: bytearray, offset: int, index: int):
        b = (
            self.substitute[((index >> 2) & 3) + 4]
            + self.substitute[index & 3]
            + self.substitute[((index >> 4) & 3) + 8]
            + self.substitute[(index % 256 >> 6) + 12]
        )
        view[offset] = (
            (self.index[view[offset] & 0xF] - b) & 0xF
            | 0x10 * (self.index[view[offset] >> 4] - b)
        ) % 256
        b = view[offset]
        return b, offset + 1, index + 1

    def decrypt(self, data: bytearray, index: int, remaining: int):
        offset = 0

        curByte, offset, index = self.decrypt_byte(data, offset, index)
        byteHigh = curByte >> 4
        byteLow = curByte & 0xF

        if byteHigh == 0xF:
            b = 0xFF
            while b == 0xFF:
                b, offset, index = self.decrypt_byte(data, offset, index)
                byteHigh += b

        offset += byteHigh

        if offset < remaining:
            _, offset, index = self.decrypt_byte(data, offset, index)
            _, offset, index = self.decrypt_byte(data, offset, index)
            if byteLow == 0xF:
                b = 0xFF
                while b == 0xFF:
                    b, offset, index = self.decrypt_byte(data, offset, index)

        return offset

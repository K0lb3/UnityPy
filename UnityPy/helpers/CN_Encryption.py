# original: https://github.com/Razmoth/PGRStudio/blob/master/AssetStudio/PGR/PGR.cs
from typing import List, Tuple

from Crypto.Cipher import AES

from ..streams import EndianBinaryReader


def read_vector(reader: EndianBinaryReader) -> Tuple[bytes, bytes]:
    data = reader.read_bytes(0x10)
    key = reader.read_bytes(0x10)
    reader.read_byte()

    return data, key


def decrypt_key(key: bytes, data: bytes, keybytes: bytes):
    key = AES.new(keybytes, AES.MODE_ECB).encrypt(key)
    return bytes(x ^ y for x, y in zip(data, key))


def to_uint4_array(source: bytes, offset: int = 0):
    buffer = bytearray(len(source) * 2)
    for j in range(len(source)):
        buffer[j * 2] = source[offset + j] >> 4
        buffer[j * 2 + 1] = source[offset + j] & 15
    return buffer


class CN_Encryption:
    Version: int = 0
    Header: str = "#$unity3dchina!@"
    Keys: List[str] = ["kurokurokurokuro", "y5XPvqLOrCokWRIa"]

    Index: bytes = bytes(0x10)
    Sub: bytes = bytes(0x10)

    def __init__(self, reader: EndianBinaryReader) -> None:
        value = reader.read_u_int()

        # read vector data/key vectors
        self.data1, self.key1 = read_vector(reader)
        self.data2, self.key2 = read_vector(reader)

        keybytes = self.Keys[self.Version].encode("utf8")

        str = decrypt_key(self.key2, self.data2, keybytes).decode("utf8")
        if str != self.Header:
            raise Exception("Invalid Signature !!")

        data = decrypt_key(self.key1, self.data1, keybytes)
        data = to_uint4_array(data)
        self.Index = data[:0x10]
        self.Sub = bytes(data[0x10 + i * 4 + j] for j in range(4) for i in range(4))

    def decrypt_block(self, data: bytes, index: int):
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
            self.Sub[((index >> 2) & 3) + 4]
            + self.Sub[index & 3]
            + self.Sub[((index >> 4) & 3) + 8]
            + self.Sub[(index % 256 >> 6) + 12]
        )
        view[offset] = (
            (self.Index[view[offset] & 0xF] - b) & 0xF
            | 0x10 * (self.Index[view[offset] >> 4] - b)
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

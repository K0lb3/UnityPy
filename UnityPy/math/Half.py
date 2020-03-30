import struct

from UnityPy import math

# import binascii

# import numpy

MaxValue = 65504.0
MinValue = -65504.0


def ToHalf(*args) -> float:
    """
	Converts the input into a half-float.
	Inputs:
		unsigned integer
		or
		buffer (bytes, buffer)
		offset
	"""
    # int input -> pack as UInt16
    if len(args) == 1:
        data = struct.pack("H", args[0])
        val = struct.unpack("e", data)[0]
    # buffer input
    elif len(args) == 2:
        val = struct.unpack_from("e", args[0], args[1])[0]

    if math.isnan(val):
        # print('Nan')
        return 0
    elif math.isinf(val):
        return MaxValue

    return val


# #CONSTANTS
# Epsilon = ToHalf(0x0001)
# MaxValue = ToHalf(0x7bff)
# MinValue = ToHalf(0xfbff)
# NaN = ToHalf(0xfe00)
# NegativeInfinity = ToHalf(0xfc00)
# PositiveInfinity = ToHalf(0x7c00)

# class Float16Compressor:
# 	def __init__(self):
# 		self.temp = 0

# 	def compress(self, float32):
# 		F16_EXPONENT_BITS = 0x1F
# 		F16_EXPONENT_SHIFT = 10
# 		F16_EXPONENT_BIAS = 15
# 		F16_MANTISSA_BITS = 0x3ff
# 		F16_MANTISSA_SHIFT = (23 - F16_EXPONENT_SHIFT)
# 		F16_MAX_EXPONENT = (F16_EXPONENT_BITS << F16_EXPONENT_SHIFT)

# 		a = struct.pack('>f', float32)
# 		b = binascii.hexlify(a)

# 		f32 = int(b, 16)
# 		f16 = 0
# 		sign = (f32 >> 16) & 0x8000
# 		exponent = ((f32 >> 23) & 0xff) - 127
# 		mantissa = f32 & 0x007fffff

# 		if exponent == 128:
# 			f16 = sign | F16_MAX_EXPONENT
# 			if mantissa:
# 				f16 |= (mantissa & F16_MANTISSA_BITS)
# 		elif exponent > 15:
# 			f16 = sign | F16_MAX_EXPONENT
# 		elif exponent > -15:
# 			exponent += F16_EXPONENT_BIAS
# 			mantissa >>= F16_MANTISSA_SHIFT
# 			f16 = sign | exponent << F16_EXPONENT_SHIFT | mantissa
# 		else:
# 			f16 = sign
# 		return f16

# 	def decompress(self, float16):
# 		s = int((float16 >> 15) & 0x00000001)  # sign
# 		e = int((float16 >> 10) & 0x0000001f)  # exponent
# 		f = int(float16 & 0x000003ff)  # fraction

# 		if e == 0:
# 			if f == 0:
# 				return int(s << 31)
# 			else:
# 				while not (f & 0x00000400):
# 					f = f << 1
# 					e -= 1
# 				e += 1
# 				f &= ~0x00000400
# 		# print(s,e,f)
# 		elif e == 31:
# 			if f == 0:
# 				return int((s << 31) | 0x7f800000)
# 			else:
# 				return int((s << 31) | 0x7f800000 | (f << 13))

# 		e = e + (127 - 15)
# 		f = f << 13
# 		return int((s << 31) | (e << 23) | f)

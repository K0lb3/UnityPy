#  *
#  * Unpack a texture compressed with ETC1
#  *
#  * @author Mark Callow, HI Corporation.
#  *

# Copyright (c) 2010 The Khronos Group Inc.

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and/or associated documentation files (the
# "Materials"), to deal in the Materials without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Materials, and to
# permit persons to whom the Materials are furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be included
# unaltered in all copies or substantial portions of the Materials.
# Any additions, deletions, or changes to the original source files
# must be clearly indicated in accompanying documentation.

# If only executable code is distributed, then the accompanying
# documentation must state that "this software is based in part on the
# work of the Khronos Group."

# THE MATERIALS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# MATERIALS OR THE USE OR OTHER DEALINGS IN THE MATERIALS.

import struct
from io import BytesIO
from PIL import Image, ImageFile


# Macros to help with bit extraction/insertion


def SHIFT(size, startpos):
	return startpos - size + 1


def MASK(size, startpos):
	return ((2 << (size - 1)) - 1) << SHIFT(size, startpos)


def PUTBITS(dest, data, size, startpos):
	mask = MASK(size, startpos)
	dest = (dest & ~mask) | ((data << SHIFT(size, startpos)) & mask)
	return dest


def SHIFTHIGH(size, startpos):
	return (((startpos) - 32) - (size) + 1)


def MASKHIGH(size, startpos):
	return (((1 << (size)) - 1) << SHIFTHIGH(size, startpos))


def PUTBITSHIGH(dest, data, size, startpos):
	mask = MASKHIGH(size, startpos)
	shift = SHIFTHIGH(size, startpos)
	dest = (dest & ~mask) | ((data << shift) & mask)
	return dest


def GETBITS(source, size, startpos):
	mask = (1 << size) - 1
	shift = startpos - size + 1
	return (source >> shift) & mask


def GETBITSHIGH(source, size, startpos):
	shift = (startpos - 32) - size + 1
	mask = (1 << size) - 1
	result = (source >> shift) & mask
	return result


# Thumb macros and definitions
R_BITS59T = 4
G_BITS59T = 4
B_BITS59T = 4
R_BITS58H = 4
G_BITS58H = 4
B_BITS58H = 4
R = 0
G = 1
B = 2
BLOCKHEIGHT = 4
BLOCKWIDTH = 4
TABLE_BITS_59T = 3
TABLE_BITS_58H = 3


# Helper Macros


def CLAMP(ll, x, ul):
	if x < ll:
		return ll
	elif x > ul:
		return ul
	else:
		return x


# Global tables

table59T = [3, 6, 11, 16, 23, 32, 41, 64]  # 3-bit table for the 59 bit T-mode
table58H = [3, 6, 11, 16, 23, 32, 41, 64]  # 3-bit table for the 58 bit H-mode
compressParams = [
		[-8, -2, 2, 8],
		[-8, -2, 2, 8],
		[-17, -5, 5, 17],
		[-17, -5, 5, 17],
		[-29, -9, 9, 29],
		[-29, -9, 9, 29],
		[-42, -13, 13, 42],
		[-42, -13, 13, 42],
		[-60, -18, 18, 60],
		[-60, -18, 18, 60],
		[-80, -24, 24, 80],
		[-80, -24, 24, 80],
		[-106, -33, 33, 106],
		[-106, -33, 33, 106],
		[-183, -47, 47, 183],
		[-183, -47, 47, 183]
]
unscramble = [2, 3, 1, 0]
alphaTableInitialized = False
alphaTable = [x[:] for x in [[0] * 8] * 256]
alphaBase = [
		[-15, -9, -6, -3],
		[-13, -10, -7, -3],
		[-13, -8, -5, -2],
		[-13, -6, -4, -2],
		[-12, -8, -6, -3],
		[-11, -9, -7, -3],
		[-11, -8, -7, -4],
		[-11, -8, -5, -3],
		[-10, -8, -6, -2],
		[-10, -8, -5, -2],
		[-10, -8, -4, -2],
		[-10, -7, -5, -2],
		[-10, -7, -4, -3],
		[-10, -3, -2, -1],
		[-9, -8, -6, -4],
		[-9, -7, -5, -3]
]

# Enums

PATTERN_H = 0
PATTERN_T = 1


# Code used to create the valtab
def setupAlphaTable():
	global alphaTableInitialized
	if alphaTableInitialized:
		return
	
	# read table used for alpha compression
	global alphaTable
	for i in range(16, 32):
		for j in range(8):
			buf = alphaBase[i - 16][3 - j % 4]
			if j < 4:
				alphaTable[i][j] = buf
			else:
				alphaTable[i][j] = (-buf - 1)
	
	# beyond the first 16 values, the rest of the table is implicit.. so calculate that!
	for i in range(256):
		# fill remaining slots in table with multiples of the first ones.
		mul = int(i / 16)
		old = 16 + i % 16
		for j in range(0, 8):
			alphaTable[i][j] = alphaTable[old][j] * mul
		# note: we don't do clamping here, though we could, because we'll be clamped afterwards anyway.
	
	alphaTableInitialized = True


# The _format stores the bits for the three extra modes in a roundabout way to be able to
# fit them without increasing the bit rate. This function converts them into something
# that is easier to work with.
def unstuff57bits(planar_word1, planar_word2):
	# Get bits from twotimer configuration for 57 bits
	#
	# Go to this bit layout:
	#
	#      63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32
	#      -----------------------------------------------------------------------------------------------
	#     |R0               |G01G02              |B01B02  ;B03     |RH1           |RH2|GH                 |
	#      -----------------------------------------------------------------------------------------------
	#
	#      31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
	#      -----------------------------------------------------------------------------------------------
	#     |BH               |RV               |GV                  |BV                | not used          |
	#      -----------------------------------------------------------------------------------------------
	#
	#  From this:
	#
	#      63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32
	#      ------------------------------------------------------------------------------------------------
	#     |//|R0               |G01|/|G02              |B01|/ // //|B02  |//|B03     |RH1           |df|RH2|
	#      ------------------------------------------------------------------------------------------------
	#
	#      31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
	#      -----------------------------------------------------------------------------------------------
	#     |GH                  |BH               |RV               |GV                   |BV              |
	#      -----------------------------------------------------------------------------------------------
	#
	#      63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34  33  32
	#      ---------------------------------------------------------------------------------------------------
	#     | base col1    | dcol 2 | base col1    | dcol 2 | base col 1   | dcol 2 | table  | table  |diff|flip|
	#     | R1' (5 bits) | dR2    | G1' (5 bits) | dG2    | B1' (5 bits) | dB2    | cw 1   | cw 2   |bit |bit |
	#      ---------------------------------------------------------------------------------------------------
	
	RO = GETBITSHIGH(planar_word1, 6, 62)
	GO1 = GETBITSHIGH(planar_word1, 1, 56)
	GO2 = GETBITSHIGH(planar_word1, 6, 54)
	BO1 = GETBITSHIGH(planar_word1, 1, 48)
	BO2 = GETBITSHIGH(planar_word1, 2, 44)
	BO3 = GETBITSHIGH(planar_word1, 3, 41)
	RH1 = GETBITSHIGH(planar_word1, 5, 38)
	RH2 = GETBITSHIGH(planar_word1, 1, 32)
	GH = GETBITS(planar_word2, 7, 31)
	BH = GETBITS(planar_word2, 6, 24)
	RV = GETBITS(planar_word2, 6, 18)
	GV = GETBITS(planar_word2, 7, 12)
	BV = GETBITS(planar_word2, 6, 5)
	
	planar57_word1 = PUTBITSHIGH(0, RO, 6, 63)
	planar57_word1 = PUTBITSHIGH(planar57_word1, GO1, 1, 57)
	planar57_word1 = PUTBITSHIGH(planar57_word1, GO2, 6, 56)
	planar57_word1 = PUTBITSHIGH(planar57_word1, BO1, 1, 50)
	planar57_word1 = PUTBITSHIGH(planar57_word1, BO2, 2, 49)
	planar57_word1 = PUTBITSHIGH(planar57_word1, BO3, 3, 47)
	planar57_word1 = PUTBITSHIGH(planar57_word1, RH1, 5, 44)
	planar57_word1 = PUTBITSHIGH(planar57_word1, RH2, 1, 39)
	planar57_word1 = PUTBITSHIGH(planar57_word1, GH, 7, 38)
	
	planar57_word2 = PUTBITS(0, BH, 6, 31)
	planar57_word2 = PUTBITS(planar57_word2, RV, 6, 25)
	planar57_word2 = PUTBITS(planar57_word2, GV, 7, 19)
	planar57_word2 = PUTBITS(planar57_word2, BV, 6, 12)
	
	return (planar57_word1, planar57_word2)


# The _format stores the bits for the three extra modes in a roundabout way to be able to
# fit them without increasing the bit rate. This function converts them into something
# that is easier to work with.
def unstuff58bits(thumbH_word1, thumbH_word2):
	# Go to this layout:
	#
	#     |63 62 61 60 59 58|57 56 55 54 53 52 51|50 49|48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33|32   |
	#     |-------empty-----|part0---------------|part1|part2------------------------------------------|part3|
	#
	#  from this:
	#
	#      63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32
	#      --------------------------------------------------------------------------------------------------|
	#     |//|part0               |// // //|part1|//|part2                                          |df|part3|
	#      --------------------------------------------------------------------------------------------------|
	
	# move parts
	part0 = GETBITSHIGH(thumbH_word1, 7, 62)
	part1 = GETBITSHIGH(thumbH_word1, 2, 52)
	part2 = GETBITSHIGH(thumbH_word1, 16, 49)
	part3 = GETBITSHIGH(thumbH_word1, 1, 32)
	
	thumbH58_word1 = PUTBITSHIGH(0, part0, 7, 57)
	thumbH58_word1 = PUTBITSHIGH(thumbH58_word1, part1, 2, 50)
	thumbH58_word1 = PUTBITSHIGH(thumbH58_word1, part2, 16, 48)
	thumbH58_word1 = PUTBITSHIGH(thumbH58_word1, part3, 1, 32)
	
	thumbH58_word2 = thumbH_word2
	return (thumbH58_word1, thumbH58_word2)


# The _format stores the bits for the three extra modes in a roundabout way to be able to
# fit them without increasing the bit rate. This function converts them into something
# that is easier to work with.
def unstuff59bits(thumbT_word1, thumbT_word2):
	# Get bits from twotimer configuration 59 bits.
	#
	# Go to this bit layout:
	#
	#     |63 62 61 60 59|58 57 56 55|54 53 52 51|50 49 48 47|46 45 44 43|42 41 40 39|38 37 36 35|34 33 32|
	#     |----empty-----|---red 0---|--green 0--|--blue 0---|---red 1---|--green 1--|--blue 1---|--dist--|
	#
	#     |31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01 00|
	#     |----------------------------------------index bits---------------------------------------------|
	#
	#
	#  From this:
	#
	#      63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32
	#      -----------------------------------------------------------------------------------------------
	#     |// // //|R0a  |//|R0b  |G0         |B0         |R1         |G1         |B1          |da  |df|db|
	#      -----------------------------------------------------------------------------------------------
	#
	#     |31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01 00|
	#     |----------------------------------------index bits---------------------------------------------|
	#
	#      63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32
	#      -----------------------------------------------------------------------------------------------
	#     | base col1    | dcol 2 | base col1    | dcol 2 | base col 1   | dcol 2 | table  | table  |df|fp|
	#     | R1' (5 bits) | dR2    | G1' (5 bits) | dG2    | B1' (5 bits) | dB2    | cw 1   | cw 2   |bt|bt|
	#      ------------------------------------------------------------------------------------------------
	
	R0a = 0
	
	# Fix middle part
	thumbT59_word1 = thumbT_word1 >> 1
	# Fix db (lowest bit of d)
	thumbT59_word1 = PUTBITSHIGH(thumbT59_word1, thumbT_word1, 1, 32)
	# Fix R0a (top two bits of R0)
	R0a = GETBITSHIGH(thumbT_word1, 2, 60)
	thumbT59_word1 = PUTBITSHIGH(thumbT59_word1, R0a, 2, 58)
	
	# Zero top part (not needed)
	thumbT59_word1 = PUTBITSHIGH(thumbT59_word1, 0, 5, 63)
	
	thumbT59_word2 = thumbT_word2
	return thumbT59_word1, thumbT59_word2


# The color bits are expanded to the full color
def decompressColor(R_B, G_B, B_B, colors_RGB444):
	# The color should be retrieved as:
	#
	# c = round(255/(r_bits^2-1))*comp_color
	#
	# This is similar to bit replication
	#
	# Note -- this code only work for bit replication from 4 bits and up --- 3 bits needs
	# two copy operations.
	
	colors = [[0, 0, 0], [0, 0, 0]]
	
	colors[0][R] = (colors_RGB444[0][R] << (8 - R_B)) | (colors_RGB444[0][R] >> (R_B - (8 - R_B)))
	colors[0][G] = (colors_RGB444[0][G] << (8 - G_B)) | (colors_RGB444[0][G] >> (G_B - (8 - G_B)))
	colors[0][B] = (colors_RGB444[0][B] << (8 - B_B)) | (colors_RGB444[0][B] >> (B_B - (8 - B_B)))
	colors[1][R] = (colors_RGB444[1][R] << (8 - R_B)) | (colors_RGB444[1][R] >> (R_B - (8 - R_B)))
	colors[1][G] = (colors_RGB444[1][G] << (8 - G_B)) | (colors_RGB444[1][G] >> (G_B - (8 - G_B)))
	colors[1][B] = (colors_RGB444[1][B] << (8 - B_B)) | (colors_RGB444[1][B] >> (B_B - (8 - B_B)))
	return colors


def calculatePaintColors59T(d, p, colors):
	# //////////////////////////////////////////////
	#
	#      C3      C1      C4----C1---C2
	#      |       |             |
	#      |       |             |
	#      |-------|             |
	#      |       |             |
	#      |       |             |
	#      C4      C2            C3
	#
	# //////////////////////////////////////////////
	
	possible_colors = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
	
	# C4
	possible_colors[3][R] = CLAMP(0, colors[1][R] - table59T[d], 255)
	possible_colors[3][G] = CLAMP(0, colors[1][G] - table59T[d], 255)
	possible_colors[3][B] = CLAMP(0, colors[1][B] - table59T[d], 255)
	
	if (p == PATTERN_T):
		# C3
		possible_colors[0][R] = colors[0][R]
		possible_colors[0][G] = colors[0][G]
		possible_colors[0][B] = colors[0][B]
		# C2
		possible_colors[1][R] = CLAMP(0, colors[1][R] + table59T[d], 255)
		possible_colors[1][G] = CLAMP(0, colors[1][G] + table59T[d], 255)
		possible_colors[1][B] = CLAMP(0, colors[1][B] + table59T[d], 255)
		# C1
		possible_colors[2][R] = colors[1][R]
		possible_colors[2][G] = colors[1][G]
		possible_colors[2][B] = colors[1][B]
	
	else:
		print("Invalid pattern. Terminating")
		exit(1)
	
	return possible_colors


# Calculate the paint colors from the block colors
# using a distance d and one of the H- or T-patterns.
def calculatePaintColors58H(d, p, colors):
	possible_colors = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
	
	# //////////////////////////////////////////////
	# //
	#      C3      C1      C4----C1---C2
	#      |       |             |
	#      |       |             |
	#      |-------|             |
	#      |       |             |
	#      |       |             |
	#      C4      C2            C3
	# //
	# //////////////////////////////////////////////
	
	# C4
	possible_colors[3][R] = CLAMP(0, colors[1][R] - table58H[d], 255)
	possible_colors[3][G] = CLAMP(0, colors[1][G] - table58H[d], 255)
	possible_colors[3][B] = CLAMP(0, colors[1][B] - table58H[d], 255)
	
	if p == PATTERN_H:
		# C1
		possible_colors[0][R] = CLAMP(0, colors[0][R] + table58H[d], 255)
		possible_colors[0][G] = CLAMP(0, colors[0][G] + table58H[d], 255)
		possible_colors[0][B] = CLAMP(0, colors[0][B] + table58H[d], 255)
		# C2
		possible_colors[1][R] = CLAMP(0, colors[0][R] - table58H[d], 255)
		possible_colors[1][G] = CLAMP(0, colors[0][G] - table58H[d], 255)
		possible_colors[1][B] = CLAMP(0, colors[0][B] - table58H[d], 255)
		# C3
		possible_colors[2][R] = CLAMP(0, colors[1][R] + table58H[d], 255)
		possible_colors[2][G] = CLAMP(0, colors[1][G] + table58H[d], 255)
		possible_colors[2][B] = CLAMP(0, colors[1][B] + table58H[d], 255)
	
	else:
		print("Invalid pattern. Terminating")
		exit(1)
	
	return possible_colors


# bit number frompos is extracted from input, and moved to bit number topos in the return value.
def getbit(input, frompos, topos):
	if frompos > topos:
		return ((1 << frompos) & input) >> (frompos - topos)
	return ((1 << frompos) & input) << (topos - frompos)


# takes as input a value, returns the value clamped to the interval [0,255].
def clamp(val):
	if val < 0:
		val = 0
	if val > 255:
		val = 255
	return val


# https://github.com/KhronosGroup/KTX
class ETC2Decoder(ImageFile.PyDecoder):
	
	# Helper Macros
	
	def RED_CHANNEL(self, x, y, value):
		self.dstImage[self.dstChannels * (y * self.width + x) + 0] = value
		return value
	
	def GREEN_CHANNEL(self, x, y, value):
		self.dstImage[self.dstChannels * (y * self.width + x) + 1] = value
		return value
	
	def BLUE_CHANNEL(self, x, y, value):
		self.dstImage[self.dstChannels * (y * self.width + x) + 2] = value
		return value
	
	def ALPHA_CHANNEL(self, x, y, value):
		self.dstImage[self.dstChannels * (y * self.width + x) + 3] = value
		return value
	
	# Decompress a T-mode block (simple packing)
	# Simple 59T packing:
	# |63 62 61 60 59|58 57 56 55|54 53 52 51|50 49 48 47|46 45 44 43|42 41 40 39|38 37 36 35|34 33 32|
	# |----empty-----|---red 0---|--green 0--|--blue 0---|---red 1---|--green 1--|--blue 1---|--dist--|
	#
	# |31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01 00|
	# |----------------------------------------index bits---------------------------------------------|
	def decompressBlockTHUMB59Tc(self, block_part1, block_part2, startx, starty):
		colorsRGB444 = [[0, 0, 0], [0, 0, 0]]
		block_mask = [x[:] for x in [[0] * 4] * 4]
		
		# First decode left part of block.
		colorsRGB444[0][R] = GETBITSHIGH(block_part1, 4, 58)
		colorsRGB444[0][G] = GETBITSHIGH(block_part1, 4, 54)
		colorsRGB444[0][B] = GETBITSHIGH(block_part1, 4, 50)
		
		colorsRGB444[1][R] = GETBITSHIGH(block_part1, 4, 46)
		colorsRGB444[1][G] = GETBITSHIGH(block_part1, 4, 42)
		colorsRGB444[1][B] = GETBITSHIGH(block_part1, 4, 38)
		
		distance = GETBITSHIGH(block_part1, TABLE_BITS_59T, 34)
		
		# Extend the two colors to RGB888
		colors = decompressColor(R_BITS59T, G_BITS59T, B_BITS59T, colorsRGB444)
		paint_colors = calculatePaintColors59T(distance, PATTERN_T, colors)
		
		# Choose one of the four paint colors for each texel
		for x in range(BLOCKWIDTH):
			for y in range(BLOCKHEIGHT):
				block_mask[x][y] = GETBITS(block_part2, 1, (y + x * 4) + 16) << 1
				block_mask[x][y] |= GETBITS(block_part2, 1, (y + x * 4))
				self.RED_CHANNEL(startx + x, starty + y, CLAMP(0, paint_colors[block_mask[x][y]][R], 255))
				self.GREEN_CHANNEL(startx + x, starty + y, CLAMP(0, paint_colors[block_mask[x][y]][G], 255))
				self.BLUE_CHANNEL(startx + x, starty + y, CLAMP(0, paint_colors[block_mask[x][y]][B], 255))
	
	# Decompress an H-mode block
	def decompressBlockTHUMB58Hc(self, block_part1, block_part2, startx, starty):
		colorsRGB444 = [x[:] for x in [[0] * 3] * 2]
		block_mask = [x[:] for x in [[0] * 4] * 4]
		
		# First decode left part of block.
		colorsRGB444[0][R] = GETBITSHIGH(block_part1, 4, 57)
		colorsRGB444[0][G] = GETBITSHIGH(block_part1, 4, 53)
		colorsRGB444[0][B] = GETBITSHIGH(block_part1, 4, 49)
		
		colorsRGB444[1][R] = GETBITSHIGH(block_part1, 4, 45)
		colorsRGB444[1][G] = GETBITSHIGH(block_part1, 4, 41)
		colorsRGB444[1][B] = GETBITSHIGH(block_part1, 4, 37)
		
		distance = (GETBITSHIGH(block_part1, 2, 33)) << 1
		
		col0 = GETBITSHIGH(block_part1, 12, 57)
		col1 = GETBITSHIGH(block_part1, 12, 45)
		
		if col0 >= col1:
			distance = distance | 1
		
		# Extend the two colors to RGB888
		colors = decompressColor(R_BITS58H, G_BITS58H, B_BITS58H, colorsRGB444)
		
		paint_colors = calculatePaintColors58H(distance, PATTERN_H, colors)
		
		# Choose one of the four paint colors for each texel
		for x in range(BLOCKWIDTH):
			for y in range(BLOCKHEIGHT):
				block_mask[x][y] = GETBITS(block_part2, 1, (y + x * 4) + 16) << 1
				block_mask[x][y] = block_mask[x][y] | GETBITS(block_part2, 1, (y + x * 4))
				self.RED_CHANNEL(startx + x, starty + y, CLAMP(0, paint_colors[block_mask[x][y]][R], 255))
				self.GREEN_CHANNEL(startx + x, starty + y, CLAMP(0, paint_colors[block_mask[x][y]][G], 255))
				self.BLUE_CHANNEL(startx + x, starty + y, CLAMP(0, paint_colors[block_mask[x][y]][B], 255))
	
	# Decompress the planar mode.
	def decompressBlockPlanar57c(self, compressed57_1, compressed57_2, startx, starty):
		colorO = [0, 0, 0]
		colorH = [0, 0, 0]
		colorV = [0, 0, 0]
		
		colorO[0] = GETBITSHIGH(compressed57_1, 6, 63)
		colorO[1] = GETBITSHIGH(compressed57_1, 7, 57)
		colorO[2] = GETBITSHIGH(compressed57_1, 6, 50)
		colorH[0] = GETBITSHIGH(compressed57_1, 6, 44)
		colorH[1] = GETBITSHIGH(compressed57_1, 7, 38)
		colorH[2] = GETBITS(compressed57_2, 6, 31)
		colorV[0] = GETBITS(compressed57_2, 6, 25)
		colorV[1] = GETBITS(compressed57_2, 7, 19)
		colorV[2] = GETBITS(compressed57_2, 6, 12)
		
		colorO[0] = (colorO[0] << 2) | (colorO[0] >> 4)
		colorO[1] = (colorO[1] << 1) | (colorO[1] >> 6)
		colorO[2] = (colorO[2] << 2) | (colorO[2] >> 4)
		
		colorH[0] = (colorH[0] << 2) | (colorH[0] >> 4)
		colorH[1] = (colorH[1] << 1) | (colorH[1] >> 6)
		colorH[2] = (colorH[2] << 2) | (colorH[2] >> 4)
		
		colorV[0] = (colorV[0] << 2) | (colorV[0] >> 4)
		colorV[1] = (colorV[1] << 1) | (colorV[1] >> 6)
		colorV[2] = (colorV[2] << 2) | (colorV[2] >> 4)
		
		for xx in range(4):
			for yy in range(4):
				self.RED_CHANNEL(startx + xx, starty + yy, CLAMP(0, ((xx * (colorH[0] - colorO[0]) + yy * (colorV[0] - colorO[0]) + 4 * colorO[0] + 2) >> 2), 255))
				self.GREEN_CHANNEL(startx + xx, starty + yy, CLAMP(0, ((xx * (colorH[1] - colorO[1]) + yy * (colorV[1] - colorO[1]) + 4 * colorO[1] + 2) >> 2), 255))
				self.BLUE_CHANNEL(startx + xx, starty + yy, CLAMP(0, ((xx * (colorH[2] - colorO[2]) + yy * (colorV[2] - colorO[2]) + 4 * colorO[2] + 2) >> 2), 255))
	
	# Decompress an ETC1 block (or ETC2 using individual or differential mode).
	def decompressBlockDiffFlipC(self, block_part1, block_part2, startx, starty):
		avg_color = [0, 0, 0]
		enc_color1 = [0, 0, 0]
		enc_color2 = [0, 0, 0]
		diff = [0, 0, 0]
		
		diffbit = GETBITSHIGH(block_part1, 1, 33)
		flipbit = GETBITSHIGH(block_part1, 1, 32)
		
		if not diffbit:
			# We have diffbit = 0.
			
			# First decode left part of block.
			avg_color[0] = GETBITSHIGH(block_part1, 4, 63)
			avg_color[1] = GETBITSHIGH(block_part1, 4, 55)
			avg_color[2] = GETBITSHIGH(block_part1, 4, 47)
			
			# Here, we should really multiply by 17 instead of 16. This can
			# be done by just copying the four lower bits to the upper ones
			# while keeping the lower bits.
			avg_color[0] |= (avg_color[0] << 4)
			avg_color[1] |= (avg_color[1] << 4)
			avg_color[2] |= (avg_color[2] << 4)
			
			table = GETBITSHIGH(block_part1, 3, 39) << 1
			
			pixel_indices_MSB = GETBITS(block_part2, 16, 31)
			pixel_indices_LSB = GETBITS(block_part2, 16, 15)
			
			if flipbit == 0:
				# We should not flip
				shift = 0
				for x in range(startx, startx + 2):
					for y in range(starty, starty + 4):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
			
			else:
				# We should flip
				shift = 0
				for x in range(startx, startx + 4):
					for y in range(starty, starty + 2):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
					
					shift += 2
			
			# Now decode other part of block.
			avg_color[0] = GETBITSHIGH(block_part1, 4, 59)
			avg_color[1] = GETBITSHIGH(block_part1, 4, 51)
			avg_color[2] = GETBITSHIGH(block_part1, 4, 43)
			
			# Here, we should really multiply by 17 instead of 16. This can
			# be done by just copying the four lower bits to the upper ones
			# while keeping the lower bits.
			avg_color[0] |= (avg_color[0] << 4)
			avg_color[1] |= (avg_color[1] << 4)
			avg_color[2] |= (avg_color[2] << 4)
			
			table = GETBITSHIGH(block_part1, 3, 36) << 1
			pixel_indices_MSB = GETBITS(block_part2, 16, 31)
			pixel_indices_LSB = GETBITS(block_part2, 16, 15)
			
			if flipbit == 0:
				# We should not flip
				shift = 8
				for x in range(startx + 2, startx + 4):
					for y in range(starty, starty + 4):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
			
			else:
				# We should flip
				shift = 2
				for x in range(startx, startx + 4):
					for y in range(starty + 2, starty + 4):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
					
					shift += 2
		else:
			# We have diffbit = 1.
			
			#      63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34  33  32
			#      ---------------------------------------------------------------------------------------------------
			#     | base col1    | dcol 2 | base col1    | dcol 2 | base col 1   | dcol 2 | table  | table  |diff|flip|
			#     | R1' (5 bits) | dR2    | G1' (5 bits) | dG2    | B1' (5 bits) | dB2    | cw 1   | cw 2   |bit |bit |
			#      ---------------------------------------------------------------------------------------------------
			#
			#
			#     c) bit layout in bits 31 through 0 (in both cases)
			#
			#      31 30 29 28 27 26 25 24 23 22 21 20 19 18 17 16 15 14 13 12 11 10  9  8  7  6  5  4  3   2   1  0
			#      --------------------------------------------------------------------------------------------------
			#     |       most significant pixel index bits       |         least significant pixel index bits       |
			#     | p| o| n| m| l| k| j| i| h| g| f| e| d| c| b| a| p| o| n| m| l| k| j| i| h| g| f| e| d| c | b | a |
			#      --------------------------------------------------------------------------------------------------
			
			# First decode left part of block.
			enc_color1[0] = GETBITSHIGH(block_part1, 5, 63)
			enc_color1[1] = GETBITSHIGH(block_part1, 5, 55)
			enc_color1[2] = GETBITSHIGH(block_part1, 5, 47)
			
			# Expand from 5 to 8 bits
			avg_color[0] = (enc_color1[0] << 3) | (enc_color1[0] >> 2)
			avg_color[1] = (enc_color1[1] << 3) | (enc_color1[1] >> 2)
			avg_color[2] = (enc_color1[2] << 3) | (enc_color1[2] >> 2)
			
			table = GETBITSHIGH(block_part1, 3, 39) << 1
			
			pixel_indices_MSB = GETBITS(block_part2, 16, 31)
			pixel_indices_LSB = GETBITS(block_part2, 16, 15)
			
			if flipbit == 0:
				# We should not flip
				shift = 0
				for x in range(startx, startx + 2):
					for y in range(starty, starty + 4):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
			
			else:
				# We should flip
				shift = 0
				for x in range(startx, startx + 4):
					for y in range(starty, starty + 2):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
					
					shift += 2
			
			# Now decode right part of block.
			diff[0] = GETBITSHIGH(block_part1, 3, 58)
			diff[1] = GETBITSHIGH(block_part1, 3, 50)
			diff[2] = GETBITSHIGH(block_part1, 3, 42)
			
			# Extend sign bit to entire byte.
			if diff[0] & 0x04:
				diff[0] |= 0xf8
				diff[0] -= 256
			
			if diff[1] & 0x04:
				diff[1] |= 0xf8
				diff[1] -= 256
			
			if diff[2] & 0x04:
				diff[2] |= 0xf8
				diff[2] -= 256
			
			#  Calculale second color
			enc_color2[0] = enc_color1[0] + diff[0]
			enc_color2[1] = enc_color1[1] + diff[1]
			enc_color2[2] = enc_color1[2] + diff[2]
			
			# Expand from 5 to 8 bits
			avg_color[0] = (enc_color2[0] << 3) | (enc_color2[0] >> 2)
			avg_color[1] = (enc_color2[1] << 3) | (enc_color2[1] >> 2)
			avg_color[2] = (enc_color2[2] << 3) | (enc_color2[2] >> 2)
			
			table = GETBITSHIGH(block_part1, 3, 36) << 1
			
			pixel_indices_MSB = GETBITS(block_part2, 16, 31)
			pixel_indices_LSB = GETBITS(block_part2, 16, 15)
			
			if flipbit == 0:
				# We should not flip
				shift = 8
				for x in range(startx + 2, startx + 4):
					for y in range(starty, starty + 4):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
			
			else:
				# We should flip
				shift = 2
				for x in range(startx, startx + 4):
					for y in range(starty + 2, starty + 4):
						index = ((pixel_indices_MSB >> shift) & 1) << 1
						index |= ((pixel_indices_LSB >> shift) & 1)
						shift += 1
						index = unscramble[index]
						
						self.RED_CHANNEL(x, y, CLAMP(0, avg_color[0] + compressParams[table][index], 255))
						self.GREEN_CHANNEL(x, y, CLAMP(0, avg_color[1] + compressParams[table][index], 255))
						self.BLUE_CHANNEL(x, y, CLAMP(0, avg_color[2] + compressParams[table][index], 255))
					
					shift += 2
	
	def decompressBlockETC2c(self, block_part1, block_part2, startx, starty):
		diffbit = (GETBITSHIGH(block_part1, 1, 33))
		if diffbit:
			# We have diffbit = 1;
			
			# Base color
			color1 = [0, 0, 0]
			color1[0] = GETBITSHIGH(block_part1, 5, 63)
			color1[1] = GETBITSHIGH(block_part1, 5, 55)
			color1[2] = GETBITSHIGH(block_part1, 5, 47)
			
			# Diff color
			diff = [0, 0, 0]
			diff[0] = GETBITSHIGH(block_part1, 3, 58)
			diff[1] = GETBITSHIGH(block_part1, 3, 50)
			diff[2] = GETBITSHIGH(block_part1, 3, 42)
			
			# Extend sign bit to entire byte.
			if diff[0] & 0x04:
				diff[0] |= 0xf8
				diff[0] -= 256
			
			if diff[1] & 0x04:
				diff[1] |= 0xf8
				diff[1] -= 256
			
			if diff[2] & 0x04:
				diff[2] |= 0xf8
				diff[2] -= 256
			
			red = color1[0] + diff[0]
			green = color1[1] + diff[1]
			blue = color1[2] + diff[2]
			
			if red < 0 or red > 31:
				block59_part1, block59_part2 = unstuff59bits(block_part1, block_part2)
				self.decompressBlockTHUMB59Tc(block59_part1, block59_part2, startx, starty)
			
			elif green < 0 or green > 31:
				block58_part1, block58_part2 = unstuff58bits(block_part1, block_part2)
				self.decompressBlockTHUMB58Hc(block58_part1, block58_part2, startx, starty)
			
			elif blue < 0 or blue > 31:
				block57_part1, block57_part2 = unstuff57bits(block_part1, block_part2)
				self.decompressBlockPlanar57c(block57_part1, block57_part2, startx, starty)
			
			else:
				self.decompressBlockDiffFlipC(block_part1, block_part2, startx, starty)
		else:
			# We have diffbit = 0;
			self.decompressBlockDiffFlipC(block_part1, block_part2, startx, starty)
	
	# Decodes tha alpha component in a block coded with GL_COMPRESSED_RGBA8_ETC2_EAC.
	# Note that this decoding is slightly different from that of GL_COMPRESSED_R11_EAC.
	# However, a hardware decoder can share gates between the two formats as explained
	# in the specification under GL_COMPRESSED_R11_EAC.
	def decompressBlockAlphaC(self, data, ix, iy):
		b = struct.unpack("BBBBBBBB", self.srcETC.read(8))
		alpha = b[0]
		table = b[1]
		
		bit = 0
		byte = 2
		# extract an alpha value for each pixel.
		for x in range(0, 4):
			for y in range(0, 4):
				# Extract table index
				index = 0
				for bitpos in range(0, 3):
					index |= getbit(b[byte], 7 - bit, 2 - bitpos)
					bit += 1
					if bit > 7:
						bit = 0
						byte += 1
				self.ALPHA_CHANNEL(ix + x, iy + y, clamp(alpha + alphaTable[table][index]))
	
	def readBigEndian4byteWord(self, src):
		s = struct.unpack("BBBB", self.srcETC.read(4))
		pBlock = (s[0] << 24) | (s[1] << 16) | (s[2] << 8) | s[3]
		return pBlock
	
	ETC_RGB4 = 34
	ETC2_RGB = 45
	ETC2_RGBA1 = 46
	ETC2_RGBA8 = 47
	ETC_RGB4_3DS = 60
	ETC_RGBA8_3DS = 61
	ETC_RGB4Crunched = 64
	ETC2_RGBA8Crunched = 65
	
	srcETC = None
	dstImage = None
	dstChannelBytes = 1
	dstChannels = 3
	
	width = 0
	height = 0
	
	# Unpack an ETC1_RGB8_OES _format compressed textur
	def _ktxUnpackETC(self, srcETC, srcFormat, activeWidth, activeHeight):
		self.srcETC = BytesIO(srcETC)
		self.width = activeWidth
		self.height = activeHeight
		
		src = 0
		
		if srcFormat in [ETC2Decoder.ETC_RGB4, ETC2Decoder.ETC2_RGB, ETC2Decoder.ETC_RGB4_3DS, ETC2Decoder.ETC_RGB4Crunched]:
			self.dstChannelBytes = 1
			self.dstChannels = 3
			alphaFormat = 0
		
		elif srcFormat in [ETC2Decoder.ETC_RGBA8_3DS, ETC2Decoder.ETC2_RGBA8, ETC2Decoder.ETC2_RGBA8Crunched]:
			self.dstChannelBytes = 1
			self.dstChannels = 4
			alphaFormat = 8
		
		elif srcFormat == ETC2Decoder.ETC2_RGBA1:
			self.dstChannelBytes = 1
			self.dstChannels = 4
			alphaFormat = 1
		
		else:
			print(srcFormat)
			exit(0)  # Upper levels should be passing only one of the above srcFormats.
		
		# active_{width,height} show how many pixels contain active data,
		# (the rest are just for making sure we have a 2*a x 4*b size).
		
		# Compute the full width & height.
		width = int((activeWidth + 3) / 4) * 4
		height = int((activeHeight + 3) / 4) * 4
		
		# print("Width = %d, Height = %d\n" % (width, height))
		# print("active pixel area: top left %d x %d area.\n" % (activeWidth, activeHeight))
		
		self.dstImage = bytearray(self.dstChannels * self.dstChannelBytes * width * height)
		if not self.dstImage:
			return 0, 0
		
		if not alphaFormat == 0:
			setupAlphaTable()
		
		for y in range(int(height / 4)):
			for x in range(int(width / 4)):
				# Decode alpha channel for RGBA
				if alphaFormat == 8:
					self.decompressBlockAlphaC(src, 4 * x, 4 * y)
					src += 8
				
				# Decode color dstChannels
				block_part1 = self.readBigEndian4byteWord(src)
				src += 4
				block_part2 = self.readBigEndian4byteWord(src)
				src += 4
				
				if alphaFormat == 1:
					self.decompressBlockETC21BitAlphaC(block_part1, block_part2, 4 * x, 4 * y)
				else:
					self.decompressBlockETC2c(block_part1, block_part2, 4 * x, 4 * y)
		
		# Ok, now write out the active pixels to the destination image.
		# (But only if the active pixels differ from the total pixels)
		
		if not (height == activeHeight and width == activeWidth):
			dstPixelBytes = self.dstChannels * self.dstChannelBytes
			dstRowBytes = dstPixelBytes * width
			activeRowBytes = activeWidth * dstPixelBytes
			newimg = bytearray(dstPixelBytes * activeWidth * activeHeight)
			if not newimg:
				return 0, 0
			
			# Convert from total area to active area:
			
			for yy in range(activeHeight):
				for xx in range(activeWidth):
					for zz in range(dstPixelBytes):
						newimg[yy * activeRowBytes + xx * dstPixelBytes + zz] = self.dstImage[yy * dstRowBytes + xx * dstPixelBytes + zz]
			
			self.dstImage = newimg
		
		return bytes(self.dstImage)
	
	def decode(self, buffer):
		self.set_as_raw(self._ktxUnpackETC(buffer, self.args[0], self.state.xsize, self.state.ysize))
		return -1, 0


Image.register_decoder('etc2', ETC2Decoder)

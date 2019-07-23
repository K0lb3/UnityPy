from enum import IntEnum

from .component import Component
from .object import Object, field


class FontStyle(IntEnum):
	Normal = 0
	Bold = 1
	Italic = 2
	BoldAndItalic = 3


class TextAlignment(IntEnum):
	Left = 0
	Center = 1
	Right = 2


class TextAnchor(IntEnum):
	UpperLeft = 0
	UpperCenter = 1
	UpperRight = 2
	MiddleLeft = 3
	MiddleCenter = 4
	MiddleRight = 5
	LowerLeft = 6
	LowerCenter = 7
	LoweRight = 8


class TextMesh(Component):
	alignment = field("m_Alignment", TextAlignment)
	anchor = field("m_Anchor", TextAnchor)
	character_size = field("m_CharacterSize")
	color = field("m_Color")
	font_size = field("m_FontSize")
	font = field("m_Font")
	font_style = field("m_FontStyle", FontStyle)
	line_spacing = field("m_LineSpacing")
	offset_z = field("m_OffsetZ")
	rich_text = field("m_RichText", bool)
	tab_size = field("m_TabSize")
	text = field("m_Text")
	
	def __str__(self):
		return self.text


class TextAsset(Object):
	path = field("m_PathName")
	script = field("m_Script")
	
	@property
	def bytes(self):
		return self.script
	
	@property
	def text(self):
		return self.bytes.decode("utf-8")


class Shader(Object):
	dependencies = field("m_Dependencies")
	script = field("m_Script")

from .object import Object, field


class Font(Object):
	data = field("m_FontData")
	ascent = field("m_Ascent", float)
	character_padding = field("m_CharacterPadding")
	character_spacing = field("m_CharacterSpacing")
	font_size = field("m_FontSize", float)
	kerning = field("m_Kerning", float)
	line_spacing = field("m_LineSpacing", float)
	pixel_scale = field("m_PixelScale", float)

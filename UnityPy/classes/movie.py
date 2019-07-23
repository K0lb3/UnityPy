from .object import field
from .texture import Texture


class MovieTexture(Texture):
	audio_clip = field("m_AudioClip")
	color_space = field("m_ColorSpace")
	loop = field("m_Loop", bool)
	movie_data = field("m_MovieData")

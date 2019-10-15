import PIL
from enum import IntEnum

from .Texture2DConverter import get_image_from_texture2d
from ..math import Rectangle


# should be imported from Sprite, but not possible
class SpritePackingRotation(IntEnum):
	kSPRNone = 0,
	kSPRFlipHorizontal = 1,
	kSPRFlipVertical = 2,
	kSPRRotate180 = 3,
	kSPRRotate90 = 4


def get_image_from_sprite(m_Sprite) -> PIL.Image:
	try:
		atlas = m_Sprite.m_SpriteAtlas
		sprite_atlas_data = atlas.m_RenderDataKey

		m_Texture2D = sprite_atlas_data.m_Texture2D
		# textureRect
		texture_rect = sprite_atlas_data.textureRect
		texture_rect_offset = sprite_atlas_data.textureRectOffset
		settings_raw = sprite_atlas_data.settingsRaw
	except:
		m_Texture2D = m_Sprite.m_RD.texture
		texture_rect = m_Sprite.m_RD.textureRect
		texture_rect_offset = m_Sprite.m_RD.textureRectOffset
		settings_raw = m_Sprite.m_RD.settingsRaw
	finally:
		original_image = get_image_from_texture2d(m_Texture2D.read(), False)
		# textureRectI = Rectangle.round(textureRect)
		sprite_image = original_image.crop((texture_rect.left, texture_rect.top, texture_rect.right,
										  texture_rect.bottom))
		
		if settings_raw.packed == 1:
			rotation = settings_raw.packingRotation
			if rotation == SpritePackingRotation.kSPRFlipHorizontal:
				sprite_image = sprite_image.transpose(PIL.Image.FLIP_TOP_BOTTOM)
			# spriteImage = RotateFlip(RotateFlipType.RotateNoneFlipX)
			elif rotation == SpritePackingRotation.kSPRFlipVertical:
				sprite_image = sprite_image.transpose(PIL.Image.FLIP_LEFT_RIGHT)
			# spriteImage.RotateFlip(RotateFlipType.RotateNoneFlipY)
			elif rotation == SpritePackingRotation.kSPRRotate180:
				sprite_image = sprite_image.transpose(PIL.Image.ROTATE_180)
			# spriteImage.RotateFlip(RotateFlipType.Rotate180FlipNone)
			elif rotation == SpritePackingRotation.kSPRRotate90:
				sprite_image = sprite_image.transpose(PIL.Image.ROTATE_270)
			# spriteImage.RotateFlip(RotateFlipType.Rotate270FlipNone)

			# Tight
			"""
			FillPath has to be figured out

			if settingsRaw.packingMode == SpritePackingMode.kSPMTight:
				try:
					triangles = GetTriangles(m_Sprite.m_RD)
					points = triangles.Select(x => x.Select(y => new PointF(y.X, y.Y)).ToArray())
					#using (var path = new GraphicsPath())
					for p in points:
						path.AddPolygon(p)

					matr = Matrix()

					version = m_Sprite.version
					if version[0] < 5 or (version[0] == 5 and version[1] < 4) or (version[0] == 5 and version[1] == 4 and version[2] <= 1): #5.4.1p3 down
						matr.Translate(m_Sprite.m_Rect.Width * 0.5 - textureRectOffset.X, m_Sprite.m_Rect.Height * 0.5 - textureRectOffset.Y)
					else:
						matr.Translate(m_Sprite.m_Rect.Width * m_Sprite.m_Pivot.X - textureRectOffset.X, m_Sprite.m_Rect.Height * m_Sprite.m_Pivot.Y - textureRectOffset.Y)
					matr.Scale(m_Sprite.m_PixelsToUnits, m_Sprite.m_PixelsToUnits)
					path.Transform(matr)

					bitmap = PIL.Image.new(originalImage.mode ,(textureRectI.Width, textureRectI.Height))
					bitmap.FillPath(spriteImage, path)
					return ImageOps.flip(bitmap)

				except:
					pass
			"""
		# Rectangle
		return sprite_image.transpose(PIL.Image.FLIP_TOP_BOTTOM)
	return None


"""
private static Vector2[][] GetTriangles(SpriteRenderData m_RD)
{
    if (m_RD.vertices != null) #5.6 down
    {
        var vertices = m_RD.vertices.Select(x => (Vector2)x.pos).ToArray();
        var triangleCount = m_RD.indices.Length / 3;
        var triangles = new Vector2[triangleCount][];
        for (int i = 0; i < triangleCount; i++)
        {
            var first = m_RD.indices[i * 3];
            var second = m_RD.indices[i * 3 + 1];
            var third = m_RD.indices[i * 3 + 2];
            var triangle = new[] { vertices[first], vertices[second], vertices[third] };
            triangles[i] = triangle;
        }
        return triangles;
    }

    return GetTriangles(m_RD.m_VertexData, m_RD.m_SubMeshes, m_RD.m_IndexBuffer); #5.6 and up
}

private static Vector2[][] GetTriangles(VertexData m_VertexData, SubMesh[] m_SubMeshes, byte[] m_IndexBuffer)
{
    var triangles = new List<Vector2[]>();
    var m_Channel = m_VertexData.m_Channels[0]; #kShaderChannelVertex
    var m_Stream = m_VertexData.m_Streams[m_Channel.stream];
    using (BinaryReader vertexReader = new BinaryReader(new MemoryStream(m_VertexData.m_DataSize)),
                        indexReader = new BinaryReader(new MemoryStream(m_IndexBuffer)))
    {
        foreach (var subMesh in m_SubMeshes)
        {
            vertexReader.BaseStream.Position = m_Stream.offset + subMesh.firstVertex * m_Stream.stride + m_Channel.offset;

            var vertices = new Vector2[subMesh.vertexCount];
            for (int v = 0; v < subMesh.vertexCount; v++)
            {
                vertices[v] = vertexReader.ReadVector3();
                vertexReader.BaseStream.Position += m_Stream.stride - 12;
            }

            indexReader.BaseStream.Position = subMesh.firstByte;

            var triangleCount = subMesh.indexCount / 3u;
            for (int i = 0; i < triangleCount; i++)
            {
                var first = indexReader.ReadUInt16() - subMesh.firstVertex;
                var second = indexReader.ReadUInt16() - subMesh.firstVertex;
                var third = indexReader.ReadUInt16() - subMesh.firstVertex;
                var triangle = new[] { vertices[first], vertices[second], vertices[third] };
                triangles.Add(triangle);
            }
        }
    }
    return triangles.ToArray();
}
}
}
"""

from enum import IntEnum

from PIL import Image, ImageDraw

from .Texture2DConverter import get_image_from_texture2d
from ..EndianBinaryReader import EndianBinaryReader


# should be imported from Sprite, but too lazy to fix the import issues caused by that
class SpritePackingRotation(IntEnum):
    kSPRNone = 0,
    kSPRFlipHorizontal = 1,
    kSPRFlipVertical = 2,
    kSPRRotate180 = 3,
    kSPRRotate90 = 4


class SpritePackingMode(IntEnum):
    kSPMTight = 0,
    kSPMRectangle = 1


def get_image(sprite, texture, alpha_texture) -> Image:
    if alpha_texture and getattr(alpha_texture, 'type', '') == "Texture2D":
        cache_id = (texture.path_id, alpha_texture.path_id)
        if cache_id not in sprite.assets_file._cache:
            original_image = get_image_from_texture2d(texture.read(), False)
            alpha_image = get_image_from_texture2d(alpha_texture.read(), False)
            original_image = Image.merge('RGBA', (*original_image.split()[:3], alpha_image.split()[0]))
            sprite.assets_file._cache[cache_id] = original_image
    else:
        cache_id = texture.path_id
        if cache_id not in sprite.assets_file._cache:
            original_image = get_image_from_texture2d(texture.read(), False)
            sprite.assets_file._cache[cache_id] = original_image
    return sprite.assets_file._cache[cache_id]


def get_image_from_sprite(m_Sprite) -> Image:
    atlas = None
    if m_Sprite.m_SpriteAtlas:
        atlas = m_Sprite.m_SpriteAtlas
    elif m_Sprite.m_AtlasTags:
        # looks like the direct pointer is empty, let's try to find the Atlas via its name
        for obj in m_Sprite.assets_file.objects.values():
            if obj.type == "SpriteAtlas":
                atlas = obj.read()
                if atlas.name == m_Sprite.m_AtlasTags[0]:
                    break 
                atlas = None
    
    if atlas:
        sprite_atlas_data = atlas.render_data_map[m_Sprite.m_RenderDataKey]
    else:
        sprite_atlas_data = m_Sprite.m_RD

    m_Texture2D = sprite_atlas_data.texture
    alpha_texture = sprite_atlas_data.alphaTexture
    texture_rect = sprite_atlas_data.textureRect
    texture_rect_offset = sprite_atlas_data.textureRectOffset
    settings_raw = sprite_atlas_data.settingsRaw

    original_image = get_image(m_Sprite, m_Texture2D, alpha_texture)

    sprite_image = original_image.crop((texture_rect.left, texture_rect.top, texture_rect.right,
                                        texture_rect.bottom))

    if settings_raw.packed == 1:
        rotation = settings_raw.packingRotation
        if rotation == SpritePackingRotation.kSPRFlipHorizontal:
            sprite_image = sprite_image.transpose(Image.FLIP_TOP_BOTTOM)
        # spriteImage = RotateFlip(RotateFlipType.RotateNoneFlipX)
        elif rotation == SpritePackingRotation.kSPRFlipVertical:
            sprite_image = sprite_image.transpose(Image.FLIP_LEFT_RIGHT)
        # spriteImage.RotateFlip(RotateFlipType.RotateNoneFlipY)
        elif rotation == SpritePackingRotation.kSPRRotate180:
            sprite_image = sprite_image.transpose(Image.ROTATE_180)
        # spriteImage.RotateFlip(RotateFlipType.Rotate180FlipNone)
        elif rotation == SpritePackingRotation.kSPRRotate90:
            sprite_image = sprite_image.transpose(Image.ROTATE_270)
    # spriteImage.RotateFlip(RotateFlipType.Rotate270FlipNone)

    if settings_raw.packingMode == SpritePackingMode.kSPMTight:
        # Tight

        # create mask to keep only the polygon
        points = get_points(m_Sprite.m_RD)
        points = normalize_points(points, m_Sprite.m_PixelsToUnits)
        mask = Image.new("1", sprite_image.size, color=0)
        draw = ImageDraw.ImageDraw(mask)
        draw.polygon(points, fill=1)

        # apply the mask
        empty_img = Image.new(sprite_image.mode, sprite_image.size, color=0)
        sprite_image = Image.composite(sprite_image, empty_img, mask)

    return sprite_image.transpose(Image.FLIP_TOP_BOTTOM)


def normalize_points(points, mod):
    min_x = min(p.X for p in points)
    min_y = min(p.Y for p in points)
    return [
        ((p.X - min_x) * mod, (p.Y - min_y) * mod)
        for p in points
    ]


def get_points(m_RD):
    """
    returns the vertices of the sprite
    """
    if hasattr(m_RD, "vertices"):  # 5.6 down
        vertices = [v.pos for v in m_RD.vertices]
    # points = [
    #    vertices[index]
    #    for index in range(m_RD.indices)
    # ]
    else:  # 5.6 and up
        m_Channel = m_RD.m_VertexData.m_Channels[0]  # kShaderChannelVertex
        m_Stream = m_RD.m_VertexData.m_Streams[m_Channel.stream]

        vertexReader = EndianBinaryReader(m_RD.m_VertexData.m_DataSize, endian='<')
        # indexReader = EndianBinaryReader(m_RD.m_IndexBuffer, endian='<')

        for subMesh in m_RD.m_SubMeshes:
            vertexReader.Position = m_Stream.offset + subMesh.firstVertex * m_Stream.stride + m_Channel.offset

            vertices = []
            for _ in range(subMesh.vertexCount):
                vertices.append(vertexReader.read_vector3())
                vertexReader.Position = vertexReader.Position + m_Stream.stride - 12

            # indexReader.Position = subMesh.firstByte

            # for _ in range(subMesh.indexCount):
            #    points.append(vertices[indexReader.read_u_short() - subMesh.firstVertex])

    return vertices

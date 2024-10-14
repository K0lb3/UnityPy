from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from ..enums import (
    ClassIDType,
    SpriteMeshType,
    SpritePackingMode,
    SpritePackingRotation,
)
from ..helpers.MeshHelper import MeshHandler
from .Texture2DConverter import get_image_from_texture2d

if TYPE_CHECKING:
    from typing import List, Optional, Tuple

    from ..classes import PPtr, Sprite, Texture2D

try:
    import numpy as np
except ImportError:
    np = None


class SpriteSettings:
    packed: bool
    packingMode: SpritePackingMode
    packingRotation: SpritePackingRotation
    meshType: SpriteMeshType

    def __init__(self, settings_raw):
        self.settingsRaw = settings_raw
        self.packed = bool(self.settingsRaw & 1)  # 1
        self.packingMode = SpritePackingMode((self.settingsRaw >> 1) & 1)  # 1
        self.packingRotation = SpritePackingRotation((self.settingsRaw >> 2) & 0xF)  # 4
        self.meshType = SpriteMeshType((self.settingsRaw >> 6) & 1)  # 1
        # rest of the bits are reserved


def get_image(
    sprite: Sprite, texture: PPtr[Texture2D], alpha_texture: Optional[PPtr[Texture2D]]
) -> Image.Image:
    if alpha_texture:
        cache_id = (texture.path_id, alpha_texture.path_id)
        if cache_id not in sprite.assets_file._cache:
            original_image = get_image_from_texture2d(texture.read(), False)
            alpha_image = get_image_from_texture2d(alpha_texture.read(), False)
            original_image = Image.merge(
                "RGBA", (*original_image.split()[:3], alpha_image.split()[0])
            )
            sprite.assets_file._cache[cache_id] = original_image
    else:
        cache_id = texture.path_id
        if cache_id not in sprite.assets_file._cache:
            original_image = get_image_from_texture2d(texture.read(), False)
            sprite.assets_file._cache[cache_id] = original_image
    return sprite.assets_file._cache[cache_id]


def get_image_from_sprite(m_Sprite: Sprite) -> Image.Image:
    atlas = None
    if m_Sprite.m_SpriteAtlas:
        atlas = m_Sprite.m_SpriteAtlas.read()
    elif m_Sprite.m_AtlasTags:
        # looks like the direct pointer is empty, let's try to find the Atlas via its name
        for obj in m_Sprite.assets_file.objects.values():
            if obj.type == ClassIDType.SpriteAtlas:
                atlas = obj.read()
                if atlas.m_Name == m_Sprite.m_AtlasTags[0]:
                    break
                atlas = None

    if atlas:
        sprite_atlas_data = next(
            value
            for key, value in atlas.m_RenderDataMap
            if key == m_Sprite.m_RenderDataKey
        )
    else:
        sprite_atlas_data = m_Sprite.m_RD

    m_Texture2D = sprite_atlas_data.texture
    alpha_texture = sprite_atlas_data.alphaTexture
    texture_rect = sprite_atlas_data.textureRect
    settings_raw = sprite_atlas_data.settingsRaw

    original_image = get_image(m_Sprite, m_Texture2D, alpha_texture)

    sprite_image = original_image.crop(
        (
            texture_rect.x,
            texture_rect.y,
            texture_rect.x + texture_rect.width,
            texture_rect.y + texture_rect.height,
        )
    )

    settings_raw = SpriteSettings(settings_raw)
    if settings_raw.packed == 1:
        rotation = settings_raw.packingRotation
        if rotation == SpritePackingRotation.kSPRFlipHorizontal:
            sprite_image = sprite_image.transpose(Image.FLIP_LEFT_RIGHT)
        # spriteImage = RotateFlip(RotateFlipType.RotateNoneFlipX)
        elif rotation == SpritePackingRotation.kSPRFlipVertical:
            sprite_image = sprite_image.transpose(Image.FLIP_TOP_BOTTOM)
        # spriteImage.RotateFlip(RotateFlipType.RotateNoneFlipY)
        elif rotation == SpritePackingRotation.kSPRRotate180:
            sprite_image = sprite_image.transpose(Image.ROTATE_180)
        # spriteImage.RotateFlip(RotateFlipType.Rotate180FlipNone)
        elif rotation == SpritePackingRotation.kSPRRotate90:
            sprite_image = sprite_image.transpose(Image.ROTATE_270)
        # spriteImage.RotateFlip(RotateFlipType.Rotate270FlipNone)

    if settings_raw.packingMode == SpritePackingMode.kSPMTight:
        mesh = MeshHandler(m_Sprite.m_RD, m_Sprite.object_reader.version)
        mesh.process()

        if any(u or v for u, v in mesh.m_UV0):
            # copy triangles from mesh
            sprite_image = render_sprite_mesh(m_Sprite, mesh, original_image)
        else:
            # create mask to keep only the polygon
            sprite_image = mask_sprite(m_Sprite, mesh, sprite_image)

    return sprite_image.transpose(Image.FLIP_TOP_BOTTOM)


def mask_sprite(
    m_Sprite: Sprite, mesh: MeshHandler, sprite_image: Image.Image
) -> Image.Image:
    mask_img = Image.new("1", sprite_image.size, color=0)
    draw = ImageDraw.ImageDraw(mask_img)

    # normalize the points
    #  shift the whole point matrix into the positive space
    #  multiply them with a factor to scale them to the image
    positions = mesh.m_Vertices
    min_x = min(x for x, _y, _z in positions)
    min_y = min(y for _x, y, _z in positions)
    factor = m_Sprite.m_PixelsToUnits
    positions_2d = [
        ((x - min_x) * factor, (y - min_y) * factor) for x, y, _z in positions
    ]

    # generate triangles from the given points
    triangles = [
        (
            positions_2d[a],
            positions_2d[b],
            positions_2d[c],
        )
        for submesh in mesh.get_triangles()
        for a, b, c in submesh
    ]

    for triangle in triangles:
        draw.polygon(triangle, fill=1)

    # apply the mask
    if sprite_image.mode == "RGBA":
        # the image already has an alpha channel,
        # so we have to use composite to keep it
        empty_img = Image.new(sprite_image.mode, sprite_image.size, color=0)
        sprite_image = Image.composite(sprite_image, empty_img, mask_img)
    else:
        # add mask as alpha-channel to keep the polygon clean
        sprite_image.putalpha(mask_img)

    return sprite_image


def render_sprite_mesh(
    m_Sprite: Sprite, mesh: MeshHandler, texture: Image.Image
) -> Image.Image:
    for triangles in mesh.get_triangles():
        positions = mesh.m_Vertices
        uv = mesh.m_UV0

        # 2. patch position data
        # 2.1 make positions 2d
        # find the axis that has only one value - can be removed
        # usually the z axis
        axis_values = [[pos[i] for pos in positions] for i in range(3)]
        for i in range(2, -1, -1):
            if len(set(axis_values[i])) == 1:
                break
        else:
            raise ValueError("Can't process 3d sprites!")
        axis_values = axis_values[:i] + axis_values[i + 1 :]
        x_min = min(axis_values[0])
        y_min = min(axis_values[1])
        x_max = max(axis_values[0])
        y_max = max(axis_values[1])

        # 2.2 map positions from middle to top left
        # 2.3 convert relative positions to absolute
        pixels_to_units = m_Sprite.m_PixelsToUnits
        positions_abs = [
            (round((x - x_min) * pixels_to_units), round((y - y_min) * pixels_to_units))
            for x, y in zip(*axis_values)
        ]
        width, height = texture.size
        uv_abs = [(round(u * width), round(v * height)) for u, v in uv]

        # 2.4 generate final image size
        size = (
            round((x_max - x_min) * pixels_to_units),
            round((y_max - y_min) * pixels_to_units),
        )
        sprite = Image.new(texture.mode, size)

        for tri in triangles:
            copy_triangle(
                texture,
                [uv_abs[i] for i in tri],
                sprite,
                [positions_abs[i] for i in tri],
            )

        return sprite


def copy_triangle(
    src_img: Image.Image,
    src_tri: Tuple[float, float],
    dst_img: Image.Image,
    dst_tri: Tuple[float, float],
) -> None:
    src_off = (
        (src_tri[1][0] - src_tri[0][0], src_tri[1][1] - src_tri[0][1]),
        (src_tri[2][0] - src_tri[0][0], src_tri[2][1] - src_tri[0][1]),
    )
    dst_off = (
        (dst_tri[1][0] - dst_tri[0][0], dst_tri[1][1] - dst_tri[0][1]),
        (dst_tri[2][0] - dst_tri[0][0], dst_tri[2][1] - dst_tri[0][1]),
    )

    # check if transform is necessary by comparing the triangle sizes
    if src_off[0] == dst_off[0] and src_off[1] == dst_off[1]:
        # no transform necessary, just copy the triangle

        # make rectangle that contains the triangle
        upper_left, _, lower_right = sorted(src_tri)
        src_part = src_img.crop((*upper_left, *lower_right))

        # create mask for triangle
        mask_box = [(x - upper_left[0], y - upper_left[1]) for x, y in src_tri]
        mask = Image.new("1", src_part.size)
        maskdraw = ImageDraw.Draw(mask)
        maskdraw.polygon(mask_box, fill=255)

        # paste triangle into destination image
        dst_img.paste(src_part, min(dst_tri), mask=mask)
    else:
        # transform is necessary, use affine transformation
        # https://stackoverflow.com/a/6959111
        ((x11, x12), (x21, x22), (x31, x32)) = src_tri
        ((y11, y12), (y21, y22), (y31, y32)) = dst_tri

        # Construct matrix M manually
        M = [
            [y11, y12, 1, 0, 0, 0],
            [y21, y22, 1, 0, 0, 0],
            [y31, y32, 1, 0, 0, 0],
            [0, 0, 0, y11, y12, 1],
            [0, 0, 0, y21, y22, 1],
            [0, 0, 0, y31, y32, 1],
        ]

        # Vector y corresponds to the x coordinates in the source triangle
        y = [x11, x21, x31, x12, x22, x32]

        if np:
            A = np.linalg.solve(M, y)
        else:
            # np.lingal.solve - obviously way faster, but numpy will only come with 2.0
            A = linalg_solve(M, y)

        transformed = src_img.transform(dst_img.size, Image.AFFINE, A)

        mask = Image.new("1", dst_img.size)
        maskdraw = ImageDraw.Draw(mask)
        maskdraw.polygon(dst_tri, fill=255)

        dst_img.paste(transformed, mask=mask)


def linalg_solve(M: List[List[float]], y: List[float]) -> List[float]:
    # M^-1 * y
    M_i = get_matrix_inverse(M)
    return [sum(M_i[i][j] * y[j] for j in range(len(y))) for i in range(len(M_i))]


def transpose_matrix(m: List[List[float]]) -> List[List[float]]:
    # https://stackoverflow.com/a/39881366
    return map(list, zip(*m))


def get_matrix_minor(m: List[List[float]], i: int, j: int) -> List[float]:
    # https://stackoverflow.com/a/39881366
    return [row[:j] + row[j + 1 :] for row in (m[:i] + m[i + 1 :])]


def get_matrix_determinant(m: List[List[float]]) -> float:
    # https://stackoverflow.com/a/39881366
    # base case for 2x2 matrix
    if len(m) == 2:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]

    return sum(
        ((-1) ** c) * m[0][c] * get_matrix_determinant(get_matrix_minor(m, 0, c))
        for c in range(len(m))
    )


def get_matrix_inverse(m: List[List[float]]) -> List[List[float]]:
    # https://stackoverflow.com/a/39881366
    determinant = get_matrix_determinant(m)
    # special case for 2x2 matrix:
    if len(m) == 2:
        return [
            [m[1][1] / determinant, -1 * m[0][1] / determinant],
            [-1 * m[1][0] / determinant, m[0][0] / determinant],
        ]

    # find matrix of cofactors
    cofactors = [
        [
            ((-1) ** (r + c)) * get_matrix_determinant(get_matrix_minor(m, r, c))
            for c in range(len(m))
        ]
        for r in range(len(m))
    ]
    cofactors = list(transpose_matrix(cofactors))

    return [[c / determinant for c in row] for row in cofactors]


__all__ = ["get_image_from_sprite"]

from ..generated import Sprite


def _Sprite_image(self: Sprite):
    from ...export import SpriteHelper

    return SpriteHelper.get_image_from_sprite(self)


Sprite.image = property(_Sprite_image)

__all__ = ("Sprite",)

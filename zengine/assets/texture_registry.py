# zengine/assets/texture_registry.py
from zengine.assets.texture_asset import TextureAsset


class TextureRegistry:
    _textures: dict[str, TextureAsset] = {}

    @classmethod
    def register(cls, tex: TextureAsset):
        cls._textures[tex.name] = tex

    @classmethod
    def get(cls, name: str) -> TextureAsset:
        return cls._textures[name]

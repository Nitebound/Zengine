# zengine/assets/texture_asset.py
from dataclasses import dataclass
from typing import Any

@dataclass
class TextureAsset:
    name: str
    texture: Any   # your moderngl.Texture

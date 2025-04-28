from dataclasses import dataclass

@dataclass
class Transform:
    x: float
    y: float
    rotation: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0

@dataclass
class SpriteRenderer:
    texture: any  # Texture object

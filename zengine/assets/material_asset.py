# zengine/assets/material_asset.py
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

@dataclass
class MaterialAsset:
    name: str
    shader: Any                   # e.g. a shader‐key or moderngl.Program
    albedo: Tuple[float,float,float,float] = (1,1,1,1)
    textures: Dict[str,str]       = field(default_factory=dict)
    # you can extend with metallic/roughness/etc.

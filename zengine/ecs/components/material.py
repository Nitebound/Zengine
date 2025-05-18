# zengine/ecs/components/material.py

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

@dataclass
class Material:
    shader: Any

    # Surface
    albedo:            Tuple[float, float, float, float] = (1,1,1,1)
    ambient_strength:  float                           = 0.1
    specular_strength: float                           = 0.5
    shininess:         float                           = 32.0

    textures:     Dict[str, Any] = field(default_factory=dict)
    extra_uniforms: Dict[str, Any] = field(default_factory=dict)

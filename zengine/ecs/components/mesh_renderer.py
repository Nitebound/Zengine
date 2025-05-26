# zengine/ecs/components/mesh_renderer.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from moderngl import Texture
from zengine.graphics.shader import Shader

@dataclass
class MeshRenderer:
    """
    Material data: which shader to use, optional texture, plus
    any extra uniform overrides.
    """
    shader: Shader
    texture: Optional[Texture] = None
    uniforms: Dict[str, Any] = field(default_factory=dict)

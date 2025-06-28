# zengine/ecs/components/material.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from zengine.graphics.shader import Shader
from zengine.assets.texture_asset import TextureAsset


@dataclass
class Material:
    shader: Shader

    # Common Unity-like surface properties
    albedo: tuple = (1.0, 1.0, 1.0, 1.0)
    metallic: float = 0.0
    smoothness: float = 0.5
    normal_map: Optional[TextureAsset] = None
    main_texture: Optional[TextureAsset] = None
    emission_color: tuple = (0.0, 0.0, 0.0, 1.0)
    emission_intensity: float = 0.0

    # Lighting flags
    use_texture: bool = True
    use_lighting: bool = True
    receive_shadows: bool = True

    # Shader-specific extra values
    custom_uniforms: Dict[str, Any] = field(default_factory=dict)

    # Optional rendering control
    render_queue: int = 2000  # Opaque = 2000, Transparent = 3000

    def get_all_uniforms(self):
        """Combine built-in + custom uniforms for shader assignment."""
        data = {
            "albedo": self.albedo,
            "metallic": float(self.metallic),
            "smoothness": float(self.smoothness),
            "emission_color": self.emission_color,
            "emission_intensity": float(self.emission_intensity),
            "useTexture": float(self.use_texture),
            "useLighting": float(self.use_lighting)
        }

        data.update(self.custom_uniforms)
        data["useTexture"] = float(self.use_texture)
        data["useLighting"] = float(self.use_lighting)

        return data

    def get_all_textures(self):
        """Return a dict of bound textures to uniforms."""
        result = {}
        if self.main_texture:
            result["main_texture"] = self.main_texture
        if self.normal_map:
            result["normal_map"] = self.normal_map
        return result

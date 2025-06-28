from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from zengine.graphics.shader import Shader
from zengine.assets.texture_asset import TextureAsset


@dataclass
class Material:
    shader: Shader

    # Surface properties
    albedo: tuple = (1.0, 1.0, 1.0, 1.0)  # Used when no texture is set
    metallic: float = 0.0
    smoothness: float = 0.5

    # Textures
    albedo_texture: Optional[TextureAsset] = None
    normal_map: Optional[TextureAsset] = None
    metallic_map: Optional[TextureAsset] = None
    roughness_map: Optional[TextureAsset] = None

    # Emission
    emission_color: tuple = (0.0, 0.0, 0.0, 1.0)
    emission_intensity: float = 0.0

    # Lighting toggles
    use_texture: bool = True
    use_lighting: bool = True
    receive_shadows: bool = True

    # Shader-specific overrides
    custom_uniforms: Dict[str, Any] = field(default_factory=dict)

    # Render order
    render_queue: int = 2000  # Opaque by default

    def get_all_uniforms(self) -> Dict[str, Any]:
        uniforms = {
            "albedo": self.albedo,
            "metallic": float(self.metallic),
            "smoothness": float(self.smoothness),
            "emission_color": self.emission_color,
            "emission_intensity": float(self.emission_intensity),
            "useTexture": float(self.use_texture),
            "useLighting": float(self.use_lighting),
            "u_has_albedo_map": int(self.albedo_texture is not None),
            "u_has_normal_map": int(self.normal_map is not None),
            "u_has_metallic_map": float(self.metallic_map is not None),
            "u_has_roughness_map": float(self.roughness_map is not None)
        }

        uniforms.update(self.custom_uniforms)
        return uniforms

    def get_all_textures(self) -> Dict[str, TextureAsset]:
        """Returns a mapping from shader uniform names to texture assets"""
        result = {}
        if self.normal_map:
            result["normal_map"] = self.normal_map
        if self.metallic_map:
            result["metallic_map"] = self.metallic_map
        if self.roughness_map:
            result["roughness_map"] = self.roughness_map
        if self.albedo_texture:
            result["albedo_texture"] = self.albedo_texture
        return result

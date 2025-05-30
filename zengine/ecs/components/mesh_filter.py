# zengine/ecs/components/mesh_filter.py
from dataclasses import dataclass
from zengine.assets.mesh_asset import MeshAsset

@dataclass
class MeshFilter:
    """
    Pure data: your raw MeshAsset (vertices, normals, uvs, indices).
    """
    asset: MeshAsset

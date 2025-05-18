# zengine/ecs/components/mesh_filter.py

from dataclasses import dataclass
from zengine.assets.mesh_asset import MeshAsset

@dataclass
class MeshFilter:
    mesh: MeshAsset

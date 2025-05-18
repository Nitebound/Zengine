# zengine/ecs/components/skinned_mesh.py

from dataclasses import dataclass

@dataclass
class SkinnedMesh:
    mesh_key:     str   # which MeshAsset
    material_key: str
    skin_key:     str
    node_index:   int   # glTF node that this primitive is attached to
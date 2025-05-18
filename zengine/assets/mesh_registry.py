# zengine/assets/mesh_registry.py

from zengine.assets.mesh_asset import MeshAsset
class MeshRegistry:
    _meshes: dict[str, MeshAsset] = {}

    @classmethod
    def register(cls, mesh: MeshAsset):
        cls._meshes[mesh.name] = mesh

    @classmethod
    def get(cls, name: str) -> MeshAsset:
        return cls._meshes[name]

    @classmethod
    def all_names(cls) -> list[str]:
        return list(cls._meshes.keys())

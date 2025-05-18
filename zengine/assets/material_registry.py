# zengine/assets/material_registry.py
from zengine.assets.material_asset import MaterialAsset


class MaterialRegistry:
    _materials: dict[str, MaterialAsset] = {}

    @classmethod
    def register(cls, mat: MaterialAsset):
        cls._materials[mat.name] = mat

    @classmethod
    def get(cls, name: str) -> MaterialAsset:
        return cls._materials[name]

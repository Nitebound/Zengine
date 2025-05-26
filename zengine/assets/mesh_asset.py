# zengine/assets/mesh_asset.py
from dataclasses import dataclass
import numpy as np

@dataclass
class MeshAsset:
    name: str
    vertices: np.ndarray   # (N,3)
    normals:  np.ndarray   # (N,3)
    indices:  np.ndarray   # (M,)
    uvs:      np.ndarray   # (N,2)
    joints:   np.ndarray | None = None  # (N,4) or None
    weights:  np.ndarray | None = None  # (N,4) or None


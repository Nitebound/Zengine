from dataclasses import dataclass
import numpy as np

@dataclass
class MeshAsset:
    name: str
    vertices:   np.ndarray   # (N,3) float32
    normals:    np.ndarray   # (N,3) float32
    indices:    np.ndarray   # (M,)  int32
    uvs:        np.ndarray   # (N,2) float32

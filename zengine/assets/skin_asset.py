from dataclasses import dataclass
import numpy as np

@dataclass
class SkinAsset:
    joint_names: list[str]                     # Bone names
    joint_nodes: list[int]                     # Node indices
    inverse_bind_matrices: np.ndarray          # (J, 4, 4)

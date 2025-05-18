# zengine/ecs/components/skin.py

from dataclasses import dataclass
import numpy as np

@dataclass
class Skin:
    joint_nodes:             list[int]
    inverse_bind_matrices:   np.ndarray  # (J,4,4)

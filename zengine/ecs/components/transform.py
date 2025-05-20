from dataclasses import dataclass

@dataclass
class Transform:
    # Position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Full 3D rotation stored as quaternion
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    rotation_w: float = 1.0

    # Scale
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0




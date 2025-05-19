from dataclasses import dataclass

@dataclass
class Transform:
    # Position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Full 3D rotation stored as quaternion
    rot_qx: float = 0.0
    rot_qy: float = 0.0
    rot_qz: float = 0.0
    rot_qw: float = 1.0

    # Scale
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0

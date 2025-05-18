from dataclasses import dataclass

@dataclass
class Transform:
    # position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # store true 3D orientation as a quaternion (x,y,z,w)
    rot_qx: float = 0.0
    rot_qy: float = 0.0
    rot_qz: float = 0.0
    rot_qw: float = 1.0

    # uniform scale
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0

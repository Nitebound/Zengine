from dataclasses import dataclass, field
from scipy.spatial.transform import Rotation as R

@dataclass
class Transform:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Euler degrees for intuitive control
    euler_x: float = 0.0
    euler_y: float = 0.0
    euler_z: float = 0.0

    # Quaternion rotation (used internally)
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    rotation_w: float = 1.0

    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0

    def update_quaternion_from_euler(self):
        quat = R.from_euler('xyz', [self.euler_x, self.euler_y, self.euler_z], degrees=True).as_quat()
        self.rotation_x, self.rotation_y, self.rotation_z, self.rotation_w = quat

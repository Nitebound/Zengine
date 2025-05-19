import numpy as np

def quat_to_mat4(x: float, y: float, z: float, w: float) -> np.ndarray:
    """
    Turn the quaternion (x,y,z,w) into a 4×4 rotation matrix.
    """
    xx, yy, zz = x*x, y*y, z*z
    xy, xz, yz = x*y, x*z, y*z
    wx, wy, wz = w*x, w*y, w*z

    return np.array([
        [1 - 2*(yy + zz),   2*(xy - wz),       2*(xz + wy),     0.0],
        [2*(xy + wz),       1 - 2*(xx + zz),   2*(yz - wx),     0.0],
        [2*(xz - wy),       2*(yz + wx),       1 - 2*(xx + yy), 0.0],
        [0.0,               0.0,               0.0,             1.0],
    ], dtype='f4')

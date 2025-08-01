import numpy as np
import math
from typing import Tuple


def quat_to_mat4(x, y, z, w):
    """Convert quaternion to 4x4 rotation matrix."""
    xx, yy, zz = x*x, y*y, z*z
    xy, xz, yz = x*y, x*z, y*z
    wx, wy, wz = w*x, w*y, w*z

    return np.array([
        [1 - 2*(yy + zz),     2*(xy - wz),     2*(xz + wy), 0],
        [    2*(xy + wz), 1 - 2*(xx + zz),     2*(yz - wx), 0],
        [    2*(xz - wy),     2*(yz + wx), 1 - 2*(xx + yy), 0],
        [              0,               0,               0, 1]
    ], dtype='f4')

def quat_to_forward(x, y, z, w):
    """Returns the forward (-Z) direction vector from a quaternion."""
    mat = quat_to_mat4(x, y, z, w)
    return -mat[:3, 2]

def quat_to_right(x, y, z, w):
    """Returns the right (+X) direction vector from a quaternion."""
    mat = quat_to_mat4(x, y, z, w)
    return mat[:3, 0]

def quat_to_up(x, y, z, w):
    """Returns the up (+Y) direction vector from a quaternion."""
    mat = quat_to_mat4(x, y, z, w)
    return mat[:3, 1]


def quat_from_euler(yaw, pitch, roll):
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)

    return np.array([
        sr * cp * cy - cr * sp * sy,  # x
        cr * sp * cy + sr * cp * sy,  # y
        cr * cp * sy - sr * sp * cy,  # z
        cr * cp * cy + sr * sp * sy   # w
    ], dtype='f4')


def quat_mul(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
        w1*w2 - x1*x2 - y1*y2 - z1*z2
    ], dtype='f4')


def normalize_quat(q):
    return q / np.linalg.norm(q)


def from_axis_angle(axis: Tuple[float, float, float], angle_rad: float) -> Tuple[float, float, float, float]:
    """
    Convert an axis-angle rotation to a quaternion.

    Parameters:
        axis (Tuple[float, float, float]): The axis of rotation (must be a 3D vector).
        angle_rad (float): The rotation angle in radians.

    Returns:
        Tuple[float, float, float, float]: The quaternion (x, y, z, w).
    """
    x, y, z = axis
    length = math.sqrt(x * x + y * y + z * z)
    if length == 0:
        raise ValueError("Axis vector cannot be zero-length")

    # Normalize the axis
    x /= length
    y /= length
    z /= length

    half_angle = angle_rad / 2.0
    sin_half = math.sin(half_angle)
    cos_half = math.cos(half_angle)

    return (
        x * sin_half,  # qx
        y * sin_half,  # qy
        z * sin_half,  # qz
        cos_half       # qw
    )

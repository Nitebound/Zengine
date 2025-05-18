# zengine/ecs/systems/render_system.py

import numpy as np

from zengine.ecs.components import SpriteRenderer
from zengine.ecs.components.transform import Transform
from zengine.ecs.systems.system import System


def quat_to_mat4(x,y,z,w):
    # builds a 4×4 rotation matrix from quaternion
    xx, yy, zz = x*x, y*y, z*z
    xy, xz, yz = x*y, x*z, y*z
    wx, wy, wz = w*x, w*y, w*z

    return np.array([
        [1-2*(yy+zz),  2*(xy - wz),  2*(xz + wy), 0],
        [2*(xy + wz),  1-2*(xx+zz),  2*(yz - wx), 0],
        [2*(xz - wy),  2*(yz + wx),  1-2*(xx+yy), 0],
        [0,            0,            0,           1],
    ], dtype='f4')

def compute_model_matrix(t: Transform) -> np.ndarray:
    # 1) translation
    T = np.eye(4, dtype='f4')
    T[:3,3] = (t.x, t.y, t.z)

    # 2) rotation from quaternion
    R = quat_to_mat4(t.rot_qx, t.rot_qy, t.rot_qz, t.rot_qw)

    # 3) scale
    S = np.eye(4, dtype='f4')
    S[0,0], S[1,1], S[2,2] = (t.scale_x, t.scale_y, t.scale_z)

    return T @ R @ S




class GizmoRenderSystem(System):
    def __init__(self):
        super().__init__()

    def on_render(self, renderer):
        cam = self.scene.active_camera
        if not cam:
            return
        vp = cam.vp_matrix

        for eid in self.em.get_entities_with(Transform, SpriteRenderer):
            tr = self.em.get_component(eid, Transform)
            sr = self.em.get_component(eid, SpriteRenderer)
            model = compute_model_matrix(tr)
            renderer.draw_quad(model, vp, sr.texture)

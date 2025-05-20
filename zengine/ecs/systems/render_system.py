# zengine/ecs/systems/render_system.py

import numpy as numpy

from zengine.ecs.components import SpriteRenderer
from zengine.ecs.components.transform import Transform
from zengine.ecs.systems.system import System
import numpy

from zengine.util.quaternion import quat_to_mat4
# zengine/ecs/systems/render_system.py

import numpy as np

def compute_model_matrix(tr):
    """
    Build a 4×4 model matrix from a Transform that carries:
      • tr.x, tr.y, tr.z        (translation)
      • tr.rotation_x…_w        (quaternion)
      • tr.scale_x…_z           (scale)
    """
    # 1) Translation
    T = np.eye(4, dtype="f4")
    T[0, 3] = tr.x
    T[1, 3] = tr.y
    T[2, 3] = tr.z

    # 2) Normalize the quaternion
    qx, qy, qz, qw = (
        tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w
    )
    norm = np.sqrt(qx*qx + qy*qy + qz*qz + qw*qw)
    if norm > 0.0:
        qx, qy, qz, qw = qx/norm, qy/norm, qz/norm, qw/norm
    else:
        qw = 1.0  # fallback to identity

    # 3) Build a 3×3 rotation matrix from the quat
    R = np.array([
        [1 - 2*(qy*qy + qz*qz),     2*(qx*qy - qz*qw),     2*(qx*qz + qy*qw)],
        [    2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz),     2*(qy*qz - qx*qw)],
        [    2*(qx*qz - qy*qw),     2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy)],
    ], dtype="f4")

    # 4) Embed into 4×4
    M = np.eye(4, dtype="f4")
    M[:3, :3] = R

    # 5) Scale
    S = np.diag([tr.scale_x, tr.scale_y, tr.scale_z, 1.0]).astype("f4")

    # 6) Compose: T · M · S
    return T @ M @ S


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

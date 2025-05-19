# zengine/ecs/systems/render_system.py

import numpy as numpy

from zengine.ecs.components import SpriteRenderer
from zengine.ecs.components.transform import Transform
from zengine.ecs.systems.system import System
import numpy

from zengine.util.quaternion import quat_to_mat4


def compute_model_matrix(t: Transform) -> numpy.ndarray:
    """
    Build a 4×4 model matrix from a Transform:
      M = T · R · S
    where R comes from the quaternion in t.rot_q*.
    """
    # 1) Translation
    T = numpy.eye(4, dtype='f4')
    T[:3, 3] = (t.x, t.y, t.z)

    # 2) Rotation from quaternion
    R = quat_to_mat4(t.rot_qx, t.rot_qy, t.rot_qz, t.rot_qw)

    # 3) Scale
    S = numpy.eye(4, dtype='f4')
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

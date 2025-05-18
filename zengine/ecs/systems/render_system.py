# zengine/ecs/systems/render_system.py
import numpy
from zengine.ecs.systems.system import System
from zengine.ecs.components.transform import Transform
from zengine.ecs.components.sprite_renderer import SpriteRenderer
from zengine.ecs.components.transform import Transform

def compute_model_matrix(t: Transform) -> numpy.ndarray:
    # 1) Translation
    T = numpy.eye(4, dtype='f4')
    T[:3, 3] = (t.x, t.y, t.z)

    # 2) Rotations (pitch=X, yaw=Y, roll=Z)
    rx, ry, rz = numpy.radians([t.rot_x, t.rot_y, t.rot_z])
    cx, sx = numpy.cos(rx), numpy.sin(rx)
    cy, sy = numpy.cos(ry), numpy.sin(ry)
    cz, sz = numpy.cos(rz), numpy.sin(rz)

    Rx = numpy.array([
        [1,   0,    0, 0],
        [0,  cx, -sx, 0],
        [0,  sx,  cx, 0],
        [0,   0,   0, 1],
    ], dtype='f4')

    Ry = numpy.array([
        [ cy, 0, sy, 0],
        [  0, 1,  0, 0],
        [-sy, 0, cy, 0],
        [  0, 0,  0, 1],
    ], dtype='f4')

    Rz = numpy.array([
        [cz, -sz, 0, 0],
        [sz,  cz, 0, 0],
        [ 0,   0, 1, 0],
        [ 0,   0, 0, 1],
    ], dtype='f4')

    R = Rz @ Ry @ Rx

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

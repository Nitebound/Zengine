import numpy as np
from zengine.ecs.systems.system import System
from zengine.ecs.components.transform       import Transform
from zengine.ecs.components.sprite_renderer import SpriteRenderer

def compute_model_matrix(t: Transform) -> np.ndarray:
    T = np.eye(4, dtype='f4'); T[:3,3] = (t.x, t.y, t.z)
    a = np.radians(t.rotation)
    R = np.eye(4, dtype='f4')
    R[0,0],R[0,1] =  np.cos(a), -np.sin(a)
    R[1,0],R[1,1] =  np.sin(a),  np.cos(a)
    S = np.eye(4, dtype='f4')
    S[0,0],S[1,1],S[2,2] = (t.scale_x, t.scale_y, t.scale_z)
    return T @ R @ S

class RenderSystem(System):
    def __init__(self):
        super().__init__()

    def on_render(self, renderer):
        cam = self.scene.active_camera
        if not cam:
            return
        vp = cam.vp_matrix

        for eid in self.em.get_entities_with(Transform, SpriteRenderer):
            t  = self.em.get_component(eid, Transform)
            sr = self.em.get_component(eid, SpriteRenderer)
            m  = compute_model_matrix(t)
            renderer.draw_quad(m, vp, sr.texture)



# zengine/ecs/systems/render_system.py

import numpy as np
from numpy import cos, sin
from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, SpriteRenderer

def compute_model_matrix(t: Transform) -> np.ndarray:
    T = np.eye(4, dtype='f4'); T[0,3],T[1,3],T[2,3] = t.x,t.y,t.z
    a = np.radians(t.rotation)
    R = np.eye(4, dtype='f4')
    R[0,0],R[0,1] = cos(a), -sin(a)
    R[1,0],R[1,1] = sin(a),  cos(a)
    S = np.eye(4, dtype='f4'); S[0,0],S[1,1],S[2,2] = t.scale_x,t.scale_y,t.scale_z
    return T @ R @ S

class RenderSystem(System):
    def on_render(self, renderer, scene, em):
        cam = scene.active_camera
        if cam is None:
            return
        vp = cam.vp_matrix
        ents = list(em.get_entities_with(Transform, SpriteRenderer))
        ents.sort(key=lambda e: em.get_component(e, Transform).z)
        for eid in ents:
            t  = em.get_component(eid, Transform)
            sr = em.get_component(eid, SpriteRenderer)
            m  = compute_model_matrix(t)
            renderer.draw_quad(m, vp, sr.texture)

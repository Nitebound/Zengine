import numpy as np
from zengine.ecs.systems.system import System
from zengine.ecs.components.camera_view import CameraView
from zengine.ecs.components.transform   import Transform

class CameraSystem(System):
    def __init__(self, scene):
        self.scene = scene

    def on_update(self, dt, em):
        for eid in em.get_entities_with(CameraView, Transform):
            cam = em.get_component(eid, CameraView)
            if not cam.active:
                continue

            tr = em.get_component(eid, Transform)

            # 1) Orthographic projection
            l, r = cam.left,   cam.right
            b, t = cam.bottom, cam.top
            n, f = cam.near,   cam.far

            proj = np.array([
                [2/(r-l),      0,        0,  -(r+l)/(r-l)],
                [0,       2/(t-b),       0,  -(t+b)/(t-b)],
                [0,            0,  -2/(f-n),  -(f+n)/(f-n)],
                [0,            0,        0,           1    ],
            ], dtype='f4')

            # 2) Pure translation view
            view = np.eye(4, dtype='f4')
            view[0,3] = -tr.x
            view[1,3] = -tr.y
            view[2,3] = -tr.z

            cam.projection_matrix = proj
            cam.view_matrix       = view
            cam.vp_matrix         = proj @ view

            self.scene.active_camera = cam
            break

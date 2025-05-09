import numpy as np
from zengine.ecs.systems.system import System
from zengine.ecs.components.camera_view import CameraView, ProjectionType
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

            if cam.projection_type == ProjectionType.ORTHO:
                # orthographic
                l, r = cam.left, cam.right
                b, t = cam.bottom, cam.top
                n, f = cam.near, cam.far
                proj = np.array([
                    [2/(r-l),      0,        0,  -(r+l)/(r-l)],
                    [0,       2/(t-b),       0,  -(t+b)/(t-b)],
                    [0,            0,  -2/(f-n),  -(f+n)/(f-n)],
                    [0,            0,        0,           1    ],
                ], dtype='f4')

            else:
                # perspective
                fov_rad = np.deg2rad(cam.fov_deg)
                f = 1.0 / np.tan(fov_rad * 0.5)
                a = cam.aspect
                n = cam.p_near
                f_f = cam.p_far
                proj = np.array([
                    [f/a,  0,                          0,                   0],
                    [0,    f,                          0,                   0],
                    [0,    0,    (f_f + n)/(n - f_f), (2*f_f*n)/(n - f_f)],
                    [0,    0,                         -1,                   0],
                ], dtype='f4')

            # view matrix including Z
            view = np.eye(4, dtype='f4')
            view[0,3] = -tr.x
            view[1,3] = -tr.y
            view[2,3] = -tr.z

            # write back
            cam.projection_matrix = proj
            cam.view_matrix       = view
            cam.vp_matrix         = proj @ view

            self.scene.active_camera = cam
            break

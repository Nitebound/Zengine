# zengine/ecs/systems/camera_system.py

import numpy as np
from zengine.ecs.systems.system import System
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.transform import Transform
import pygame

class CameraSystem(System):
    def on_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # toggle active camera
                for eid in self.em.get_entities_with(CameraComponent):
                    cam = self.em.get_component(eid, CameraComponent)
                    if cam.active:
                        cam.projection = ProjectionType.ORTHO if cam.projection is ProjectionType.PERSPECTIVE else ProjectionType.PERSPECTIVE
                    else:
                        cam.active = True
                        break


    def on_update(self, dt):
        # pick the first active camera
        for eid in self.em.get_entities_with(CameraComponent, Transform):
            cam = self.em.get_component(eid, CameraComponent)
            if not cam.active:
                continue
            tr = self.em.get_component(eid, Transform)

            # 1) build projection matrix
            if cam.projection is ProjectionType.PERSPECTIVE:
                fov = np.radians(cam.fov_deg) * 0.5
                f   = 1.0 / np.tan(fov)
                a   = cam.aspect
                n, f_f = cam.p_near, cam.p_far
                proj = np.array([
                    [f/a,   0,                             0,                          0],
                    [  0,   f,                             0,                          0],
                    [  0,   0,   (f_f + n)/(n - f_f),  (2*f_f*n)/(n - f_f)],
                    [  0,   0,                            -1,                          0],
                ], dtype='f4')

            else:  # ORTHO
                # auto-compute if all four bounds are zero
                if (cam.left, cam.right, cam.bottom, cam.top) == (0.0, 0.0, 0.0, 0.0):
                    w, h = self.scene.window.width, self.scene.window.height
                    half_w, half_h = w * 0.5, h * 0.5
                    l, r = -half_w, half_w
                    b, t = -half_h, half_h
                else:
                    l, r = cam.left, cam.right
                    b, t = cam.bottom, cam.top

                n, f_f = cam.near, cam.far
                proj = np.array([
                    [ 2/(r-l),     0,            0,  -(r + l)/(r - l)],
                    [     0,   2/(t-b),          0,  -(t + b)/(t - b)],
                    [     0,        0,   -2/(f_f - n), -(f_f + n)/(f_f - n)],
                    [     0,        0,            0,              1     ],
                ], dtype='f4')

            # 2) build view matrix: translate + rotate Z
            trans = np.eye(4, dtype='f4')
            trans[0,3], trans[1,3], trans[2,3] = -tr.x, -tr.y, -tr.z

            theta = np.radians(-tr.rot_z)
            c, s = np.cos(theta), np.sin(theta)
            rot = np.eye(4, dtype='f4')
            rot[0,0], rot[0,1] =  c, -s
            rot[1,0], rot[1,1] =  s,  c

            # 3) stash into camera
            cam.projection_matrix = proj
            cam.view_matrix       = rot @ trans
            cam.vp_matrix         = proj @ cam.view_matrix

            # 4) expose to renderer
            self.scene.active_camera = cam
            break

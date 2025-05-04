# zengine/ecs/systems/camera_system.py
from dataclasses import dataclass
from enum import Enum

import numpy as np
from math import tan, radians
from zengine.ecs.systems.system import System
from zengine.ecs.components.camera_view import CameraView
from zengine.ecs.components.transform   import Transform

class ProjectionType(Enum):
    ORTHO = 1
    PERSPECTIVE = 2

@dataclass
class OrthoParams:
    left: float
    right: float
    bottom: float
    top: float
    near: float = -1000.0
    far: float  = 1000.0

@dataclass
class PerspectiveParams:
    fov_deg: float
    aspect: float
    near: float = 0.1
    far: float  = 1000.0

class CameraSystem(System):
    def __init__(self, scene):
        self.scene = scene

    def on_update(self, dt, em):
        # find the first active camera
        for eid in em.get_entities_with(CameraView, Transform):
            cam = em.get_component(eid, CameraView)
            if not cam.active:
                continue

            tr = em.get_component(eid, Transform)
            pos    = np.array([tr.x, tr.y, tr.z], dtype='f4')
            target = np.array([tr.x, tr.y, 0.0], dtype='f4')  # looking “down” at Z=0
            up     = np.array([0.0, 1.0, 0.0], dtype='f4')

            # -- build view matrix (look‐at) --
            f = (target - pos);  f /= np.linalg.norm(f)
            s = np.cross(f, up); s /= np.linalg.norm(s)
            u = np.cross(s, f)
            M = np.eye(4, dtype='f4')
            M[0,:3], M[1,:3], M[2,:3] = s, u, -f
            T = np.eye(4, dtype='f4'); T[:3,3] = -pos
            cam.view_matrix = M @ T

            # -- build projection matrix --
            if cam.projection_type is ProjectionType.ORTHO:
                l,r,b,t,n,f_ = cam.left,cam.right,cam.bottom,cam.top,cam.near,cam.far
                cam.projection_matrix = np.array([
                    [2/(r-l),      0,          0,      -(r+l)/(r-l)],
                    [0,         2/(t-b),       0,      -(t+b)/(t-b)],
                    [0,            0,     -2/(f_-n),  -(f_+n)/(f_-n)],
                    [0,            0,          0,            1      ],
                ], dtype='f4')
            else:
                fov = radians(cam.fov_deg)
                fval = 1.0/ tan(fov/2)
                a    = cam.aspect; n=cam.p_near; f_=cam.p_far
                cam.projection_matrix = np.array([
                    [fval/a, 0,      0,            0],
                    [0,      fval,   0,            0],
                    [0,      0,  (f_+n)/(n-f_),  (2*f_*n)/(n-f_)],
                    [0,      0,     -1,            0],
                ], dtype='f4')

            cam.vp_matrix = cam.projection_matrix @ cam.view_matrix
            self.scene.active_camera = cam
            break

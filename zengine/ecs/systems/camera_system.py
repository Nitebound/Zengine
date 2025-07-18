import numpy as np
from zengine.ecs.systems.system import System
from zengine.util.quaternion import quat_to_mat4
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.transform import Transform

class CameraSystem(System):
    def on_update(self, dt):
        for eid in self.em.get_entities_with(CameraComponent, Transform):
            cam = self.em.get_component(eid, CameraComponent)
            if not cam.active:
                continue
            tr = self.em.get_component(eid, Transform)

            if cam.projection is ProjectionType.PERSPECTIVE:
                f = 1.0 / np.tan(np.radians(cam.fov_deg) * 0.5)
                nf = 1 / (cam.p_near - cam.p_far)
                proj = np.array([
                    [f / cam.aspect, 0, 0, 0],
                    [0, f, 0, 0],
                    [0, 0, (cam.p_far + cam.p_near) * nf, (2 * cam.p_far * cam.p_near) * nf],
                    [0, 0, -1, 0],
                ], dtype='f4')
            else:
                # Orthographic (unchanged)
                proj = np.array([
                    [2/(cam.right-cam.left), 0, 0, -(cam.right+cam.left)/(cam.right-cam.left)],
                    [0, 2/(cam.top-cam.bottom), 0, -(cam.top+cam.bottom)/(cam.top-cam.bottom)],
                    [0, 0, 2/(cam.near-cam.far), -(cam.far+cam.near)/(cam.far-cam.near)],
                    [0, 0, 0, 1],
                ], dtype='f4')

            # Build view matrix
            T_inv = np.eye(4, dtype='f4')
            T_inv[:3,3] = (-tr.x, -tr.y, -tr.z)
            R = quat_to_mat4(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            R_inv = R.T  # Transpose = inverse for rotation matrix

            T_inv = np.eye(4, dtype='f4')
            T_inv[:3, 3] = (-tr.x, -tr.y, -tr.z)

            view = R_inv @ T_inv

            cam.projection_matrix = proj
            cam.view_matrix = view
            cam.vp_matrix = proj @ view
            self.scene.active_camera = eid
            break

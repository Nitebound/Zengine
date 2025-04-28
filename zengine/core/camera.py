import numpy as np

class Camera:
    def __init__(self, fov=60, aspect_ratio=4/3, near=0.1, far=10.0):
        self.fov = np.radians(fov)
        self.aspect_ratio = aspect_ratio
        self.near = near
        self.far = far

    def get_view_projection(self):
        proj = self._perspective(self.fov, self.aspect_ratio, self.near, self.far)
        view = self._look_at(eye=np.array([0, 0, 3], dtype='f4'), target=np.array([0, 0, 0], dtype='f4'),
                             up=np.array([0, 1, 0], dtype='f4'))
        return proj @ view

    def _look_at(self, eye, target, up):
        f = target - eye
        f = f / np.linalg.norm(f)

        s = np.cross(f, up)
        s = s / np.linalg.norm(s)

        u = np.cross(s, f)

        result = np.identity(4, dtype='f4')
        result[0, :3] = s
        result[1, :3] = u
        result[2, :3] = -f
        result[0, 3] = -np.dot(s, eye)
        result[1, 3] = -np.dot(u, eye)
        result[2, 3] = np.dot(f, eye)
        return result

    def _perspective(self, fov, aspect, near, far):
        f = 1.0 / np.tan(fov / 2.0)
        nf = 1 / (near - far)

        return np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) * nf, (2 * far * near) * nf],
            [0, 0, -1, 0]
        ], dtype='f4')

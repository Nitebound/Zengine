import moderngl
import numpy as np

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, MeshFilter, Material, MeshRenderer
from zengine.ecs.components.camera import CameraComponent
from zengine.util.quaternion import quat_to_mat4


def compute_model_matrix(tr: Transform) -> np.ndarray:
    T = np.eye(4, dtype='f4')
    T[:3, 3] = (tr.x, tr.y, tr.z)

    R = quat_to_mat4(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)

    S = np.eye(4, dtype='f4')
    S[0, 0] = tr.scale_x
    S[1, 1] = tr.scale_y
    S[2, 2] = tr.scale_z

    # 🟢 TRS order: model = T @ R @ S (correct local pivot)
    return T @ R @ S

class RenderSystem(System):
    def __init__(self, ctx, scene):
        super().__init__()
        self.ctx = ctx
        self.scene = scene
        self._vao_cache = {}

        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.CULL_FACE)
        self.ctx.front_face = 'ccw'
        self.ctx.cull_face = 'back'

    def on_update(self, dt):
        pass

    def on_render(self, renderer):
        cam_e = self.scene.active_camera
        tr_cam = self.scene.entity_manager.get_component(cam_e, Transform)
        cp_cam = self.scene.entity_manager.get_component(cam_e, CameraComponent)

        proj = cp_cam.projection_matrix
        view = cp_cam.view_matrix

        for eid in self.scene.entity_manager.get_entities_with(Transform, MeshFilter, Material, MeshRenderer):
            tr = self.scene.entity_manager.get_component(eid, Transform)
            mf = self.scene.entity_manager.get_component(eid, MeshFilter)
            mat = self.scene.entity_manager.get_component(eid, Material)

            model = compute_model_matrix(tr)
            prog = mat.shader.program

            prog['model'].write(model.astype('f4').T.tobytes())
            prog['view'].write(view.astype('f4').T.tobytes())
            prog['projection'].write(proj.astype('f4').T.tobytes())

            for uname, val in {
                'useTexture':     mat.extra_uniforms.get('useTexture', False),
                'useLighting':    mat.extra_uniforms.get('useLighting', False),
                'baseColor':      mat.albedo,
                'lightDirection': mat.extra_uniforms.get('lightDirection', (0, 11, 0)),
                'ambientColor':   mat.extra_uniforms.get('ambientColor', (0.1, 0.1, 0.1, 1)),
            }.items():
                if uname in prog:
                    prog[uname].value = val

            for slot, (uniform_name, tex) in enumerate(mat.textures.items()):
                tex.use(location=slot)
                if uniform_name in prog:
                    prog[uniform_name].value = slot

            for uname, val in mat.extra_uniforms.items():
                if uname in prog:
                    prog[uname].value = val

            key = (mf.asset.name, prog.glo)
            if key not in self._vao_cache:
                # 🚨 FIX: Bind normals along with position (3f 3f)
                vertices = np.hstack([mf.asset.vertices, mf.asset.normals]).astype('f4')
                vbo = self.ctx.buffer(vertices.tobytes())
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [(vbo, '3f 3f', 'in_position', 'in_normal')]
                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao

            self._vao_cache[key].render()

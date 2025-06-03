import moderngl
import numpy as np

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, MeshFilter, Material, MeshRenderer
from zengine.ecs.components.camera import CameraComponent
from zengine.util.quaternion import quat_to_mat4


def compute_model_matrix(tr: Transform) -> np.ndarray:
    T = np.eye(4, dtype='f4'); T[:3, 3] = (tr.x, tr.y, tr.z)
    R = quat_to_mat4(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
    S = np.diag([tr.scale_x, tr.scale_y, tr.scale_z, 1.0]).astype('f4')
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

    def on_update(self, dt):
        pass

    def on_render(self, renderer):
        cam_e = self.scene.active_camera
        tr_cam = self.scene.entity_manager.get_component(cam_e, Transform)
        cp_cam = self.scene.entity_manager.get_component(cam_e, CameraComponent)

        proj = cp_cam.projection_matrix
        view = cp_cam.view_matrix

        for eid in self.scene.entity_manager.get_entities_with(Transform, MeshFilter, Material, MeshRenderer):
            tr  = self.scene.entity_manager.get_component(eid, Transform)
            mf  = self.scene.entity_manager.get_component(eid, MeshFilter)
            mat = self.scene.entity_manager.get_component(eid, Material)

            model = compute_model_matrix(tr)
            prog  = mat.shader.program

            # Core transforms
            if 'model'      in prog: prog['model'].write(model.T.astype('f4').tobytes())
            if 'view'       in prog: prog['view'].write(view.T.astype('f4').tobytes())
            if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())

            # Material-sourced uniforms
            for uname, val in mat.get_all_uniforms().items():
                if uname in prog:
                    prog[uname].value = val

            # Texture binding
            for slot, (uname, tex) in enumerate(mat.get_all_textures().items()):
                tex.use(location=slot)
                if uname in prog:
                    prog[uname].value = slot

            # VAO caching
            key = (mf.asset.name, prog.glo)
            if key not in self._vao_cache:
                vertices = np.hstack([
                    mf.asset.vertices,  # 3f position
                    mf.asset.normals,   # 3f normal
                    mf.asset.uvs        # 2f uv
                ]).astype('f4')

                vbo = self.ctx.buffer(vertices.tobytes())
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_uv')]
                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao

            self._vao_cache[key].render()

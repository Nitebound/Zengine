# zengine/ecs/systems/render_system.py

import moderngl
import numpy as np

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, MeshFilter
from zengine.ecs.components.material import Material   # your material dataclass :contentReference[oaicite:0]{index=0}
from zengine.ecs.components.camera import CameraComponent
from zengine.util.quaternion import quat_to_mat4

def compute_model_matrix(tr: Transform) -> np.ndarray:
    """T · R · S from your Transform dataclass."""
    T = np.eye(4, dtype='f4'); T[:3,3] = (tr.x, tr.y, tr.z)
    R = quat_to_mat4(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
    S = np.diag([tr.scale_x, tr.scale_y, tr.scale_z, 1.0]).astype('f4')
    return T @ R @ S

class RenderSystem(System):
    def __init__(self, ctx, scene):
        super().__init__()
        self.ctx        = ctx
        self.scene      = scene
        self._vao_cache = {}

        # one-time OpenGL state
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.front_face = 'ccw'
        self.ctx.cull_face  = 'back'

    def _get_vao(self, asset, prog):
        """Build (once) a VAO for this MeshAsset + shader program."""
        name = asset.name
        if name not in self._vao_cache:
            # upload raw buffers
            vbo = self.ctx.buffer(asset.vertices.astype('f4').tobytes())
            nbo = self.ctx.buffer(asset.normals.astype( 'f4').tobytes())
            tbo = self.ctx.buffer(asset.uvs.astype(     'f4').tobytes())
            ibo = self.ctx.buffer(asset.indices.astype( 'i4').tobytes())
            # must match your vertex shader 'in' names:
            content = [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_texcoord')]
            vao = self.ctx.vertex_array(prog, content, ibo)
            self._vao_cache[name] = vao
        return self._vao_cache[name]

    def on_update(self, dt):
        # clear color & depth
        self.ctx.clear(0.1, 0.1, 0.1, 1.0, depth=1.0)

        # camera
        cam_e  = self.scene.active_camera
        tr_cam = self.scene.entity_manager.get_component(cam_e, Transform)
        cp_cam = self.scene.entity_manager.get_component(cam_e, CameraComponent)
        proj   = cp_cam.projection_matrix
        view   = cp_cam.view_matrix

        # draw all Transform + MeshFilter + Material
        for eid in self.em.get_entities_with(Transform, MeshFilter, Material):
            tr   = self.em.get_component(eid, Transform)
            mf   = self.em.get_component(eid, MeshFilter)    # holds your MeshAsset :contentReference[oaicite:1]{index=1}
            mat  = self.em.get_component(eid, Material)      # surface data

            model = compute_model_matrix(tr)
            prog  = mat.shader.program

            # inside RenderSystem.on_update, after computing `model`, `proj`, `view`…

            # 1) grab the Material component
            mat = self.scene.entity_manager.get_component(eid, Material)
            prog = mat.shader.program

            # 2) set the three core matrices (must exist)
            prog['projection'].write(proj.astype('f4').tobytes())
            prog['view'].write(view.astype('f4').tobytes())
            prog['model'].write(model.astype('f4').tobytes())

            # 3) try binding the built‐in material properties
            for name in ('albedo', 'ambient_strength', 'specular_strength', 'shininess'):
                try:
                    prog[name].value = getattr(mat, name)
                except KeyError:
                    # this shader simply doesn’t use that property
                    pass

            # 4) bind textures by the uniform names you provided in mat.textures
            for slot, (uniform_name, tex) in enumerate(mat.textures.items()):
                tex.use(location=slot)
                try:
                    prog[uniform_name].value = slot
                except KeyError:
                    pass

            # 5) finally, any truly custom extras
            for name, val in mat.extra_uniforms.items():
                try:
                    prog[name].value = val
                except KeyError:
                    pass

            # then build/fetch your VAO and call vao.render() as before

            # 5) finally draw the VAO
            vao = self._get_vao(mf.asset, prog)
            vao.render()

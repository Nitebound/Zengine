# zengine/ecs/systems/render_system.py

import moderngl
import numpy as np

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, MeshFilter, Material, MeshRenderer
from zengine.ecs.components.camera import CameraComponent
from zengine.ecs.components.light import LightComponent, LightType
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

    def on_update(self, dt): pass

    def on_render(self, renderer):
        cam_e = self.scene.active_camera
        tr_cam = self.scene.entity_manager.get_component(cam_e, Transform)
        cp_cam = self.scene.entity_manager.get_component(cam_e, CameraComponent)

        proj = cp_cam.projection_matrix
        view = cp_cam.view_matrix

        # Collect lights
        light_data = []
        for eid in self.scene.entity_manager.get_entities_with(Transform, LightComponent):
            light = self.scene.entity_manager.get_component(eid, LightComponent)
            tr = self.scene.entity_manager.get_component(eid, Transform)
            light_data.append((light, tr))

        for eid in self.scene.entity_manager.get_entities_with(Transform, MeshFilter, Material, MeshRenderer):
            tr  = self.scene.entity_manager.get_component(eid, Transform)
            mf  = self.scene.entity_manager.get_component(eid, MeshFilter)
            mat = self.scene.entity_manager.get_component(eid, Material)

            model = compute_model_matrix(tr)
            prog  = mat.shader.program

            if 'model' in prog:      prog['model'].write(model.T.astype('f4').tobytes())
            if 'view' in prog:       prog['view'].write(view.T.astype('f4').tobytes())
            if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())

            # ✅ Pass lighting data
            if 'light_count' in prog:
                prog['light_count'].value = len(light_data)

                for i, (light, l_tr) in enumerate(light_data[:8]):
                    prog[f'light_type[{i}]'].value = light.type.value
                    prog[f'light_position[{i}]'].value = (l_tr.x, l_tr.y, l_tr.z)
                    prog[f'light_color[{i}]'].value = light.color
                    prog[f'light_intensity[{i}]'].value = light.intensity

            # Built-in material values
            for uname, val in mat.get_all_uniforms().items():
                if uname in prog:
                    prog[uname].value = val

            for slot, (uname, tex) in enumerate(mat.get_all_textures().items()):
                tex.use(location=slot)
                if uname in prog:
                    prog[uname].value = slot

            # Build or fetch VAO
            key = (mf.asset.name, prog.glo)
            if key not in self._vao_cache:
                vertices = np.hstack([
                    mf.asset.vertices, mf.asset.normals, mf.asset.uvs
                ]).astype('f4')

                vbo = self.ctx.buffer(vertices.tobytes())
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_uv')]
                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao

            self._vao_cache[key].render()

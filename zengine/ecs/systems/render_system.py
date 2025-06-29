# zengine/ecs/systems/render_system.py
import struct

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
        camera_position = (tr_cam.x, tr_cam.y, tr_cam.z)

        # Collect lights
        light_data = []
        for eid in self.scene.entity_manager.get_entities_with(Transform, LightComponent):
            light = self.scene.entity_manager.get_component(eid, LightComponent)
            tr = self.scene.entity_manager.get_component(eid, Transform)
            light_data.append((light, tr))

        for eid in self.scene.entity_manager.get_entities_with(Transform, MeshFilter, Material, MeshRenderer):
            tr = self.scene.entity_manager.get_component(eid, Transform)
            mf = self.scene.entity_manager.get_component(eid, MeshFilter)
            mat = self.scene.entity_manager.get_component(eid, Material)

            model = compute_model_matrix(tr)
            prog = mat.shader.program

            # Basic matrices
            if 'model' in prog:      prog['model'].write(model.T.astype('f4').tobytes())
            if 'view' in prog:       prog['view'].write(view.T.astype('f4').tobytes())
            if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())

            # ✅ Lighting
            if 'light_count' in prog:
                prog['light_count'].value = len(light_data)

                MAX_LIGHTS = 8
                light_positions = []
                light_colors = []
                light_intensities = []
                light_ranges = []

                for light, l_tr in light_data[:MAX_LIGHTS]:
                    light_model = compute_model_matrix(l_tr)
                    world_pos = light_model[:3, 3]

                    light_positions.extend(world_pos)
                    light_colors.extend(light.color[:3])
                    light_intensities.append(light.intensity)
                    light_ranges.append(light.range)

                # Pad arrays to expected uniform array sizes
                while len(light_positions) < MAX_LIGHTS * 3:
                    light_positions.extend((0.0, 0.0, 0.0))
                while len(light_colors) < MAX_LIGHTS * 3:
                    light_colors.extend((0.0, 0.0, 0.0))
                while len(light_intensities) < MAX_LIGHTS:
                    light_intensities.append(0.0)
                while len(light_ranges) < MAX_LIGHTS:
                    light_ranges.append(0.001)  # prevent div/0

                prog['light_position'].write(np.array(light_positions, dtype='f4').tobytes())
                prog['light_color'].write(np.array(light_colors, dtype='f4').tobytes())
                prog['light_intensity'].write(np.array(light_intensities, dtype='f4').tobytes())
                prog['light_range'].write(np.array(light_ranges, dtype='f4').tobytes())
            # Material
            for uname, val in mat.get_all_uniforms().items():
                if uname in prog:
                    # Safe uniform push: prevents textures or unsupported types from crashing
                    try:
                        prog[uname].value = val
                    except (KeyError, struct.error, TypeError, AttributeError) as e:
                        print(f"⚠️ Skipping uniform '{uname}': {e}")

            for slot, (uname, tex) in enumerate(mat.get_all_textures().items()):
                tex.use(location=slot)
                if uname in prog:
                    prog[uname].value = slot

            # VAO cache key
            key = (mf.asset.name, prog.glo)
            if key not in self._vao_cache:
                v = mf.asset.vertices
                n = mf.asset.normals
                uv = mf.asset.uvs

                fmt = '3f'
                attrs = ['in_position']
                streams = [v]

                if 'in_normal' in prog._members:
                    fmt += ' 3f'
                    attrs.append('in_normal')
                    streams.append(n)

                if 'in_normal' in prog._members and mf.asset.normals is not None:
                    print("→ Binding normals to shader")
                    fmt += ' 3f'
                    attrs.append('in_normal')
                    streams.append(mf.asset.normals)
                else:
                    print("⚠️ Not binding normals!")

                if 'in_uv' in prog._members and uv is not None:
                    if uv.ndim == 1:
                        uv = uv.reshape(-1, 2)
                    fmt += ' 2f'
                    attrs.append('in_uv')
                    streams.append(uv)

                t = mf.asset.tangents if hasattr(mf.asset, 'tangents') else None
                if 'in_tangent' in prog._members and mf.asset.tangents is not None:
                    fmt += ' 3f'
                    attrs.append('in_tangent')
                    streams.append(mf.asset.tangents)
                    print("→ Binding tangents to shader")

                vertices = np.hstack(streams).astype('f4')

                vbo = self.ctx.buffer(vertices.tobytes())
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [(vbo, fmt, *attrs)]

                print("Normals:", np.min(mf.asset.normals), np.max(mf.asset.normals))
                print("Shader expects:", prog._members.keys())
                print("Mesh has normals:", mf.asset.normals.shape if mf.asset.normals is not None else None)

                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao

            #     print(np.min(n), np.max(n))
            #
            # print("Lighting uniforms sent:")
            # print("  → light_position:", light_positions)
            # print("  → light_color:   ", light_colors)
            # print("  → light_intensity:", light_intensities)
            #
            # print("Shader program contains:")
            # for name in prog._members:
            #     print("  →", name)

            self._vao_cache[key].render()


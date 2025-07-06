# zengine/ecs/systems/render_system.py
import struct

import moderngl
import numpy as np
import math

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

            if 'model' in prog:      prog['model'].write(model.T.astype('f4').tobytes())
            if 'view' in prog:       prog['view'].write(view.T.astype('f4').tobytes())
            if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())

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

                while len(light_positions) < MAX_LIGHTS * 3:
                    light_positions.extend((0.0, 0.0, 0.0))
                while len(light_colors) < MAX_LIGHTS * 3:
                    light_colors.extend((0.0, 0.0, 0.0))
                while len(light_intensities) < MAX_LIGHTS:
                    light_intensities.append(0.0)
                while len(light_ranges) < MAX_LIGHTS:
                    light_ranges.append(0.001)

                prog['light_position'].write(np.array(light_positions, dtype='f4').tobytes())
                prog['light_color'].write(np.array(light_colors, dtype='f4').tobytes())
                prog['light_intensity'].write(np.array(light_intensities, dtype='f4').tobytes())
                prog['light_range'].write(np.array(light_ranges, dtype='f4').tobytes())

            for uname, val in mat.get_all_uniforms().items():
                if uname in prog:
                    try:
                        prog[uname].value = val
                    except (KeyError, struct.error, TypeError, AttributeError) as e:
                        print(f"⚠️ Skipping uniform '{uname}': {e}")

            for slot, (uname, tex) in enumerate(mat.get_all_textures().items()):
                tex.use(location=slot)
                if uname in prog:
                    prog[uname].value = slot

            key = (mf.asset.name, prog.glo)
            if key not in self._vao_cache:
                v = mf.asset.vertices
                n = mf.asset.normals
                uv = mf.asset.uvs
                j = mf.asset.joints
                w = mf.asset.weights
                t = mf.asset.tangents if hasattr(mf.asset, 'tangents') else None

                fmt = '3f'
                attrs = ['in_position']
                streams = [v]

                if 'in_normal' in prog._members and n is not None:
                    fmt += ' 3f'
                    attrs.append('in_normal')
                    streams.append(n)
                    print("→ Binding normals to shader")

                if 'in_uv' in prog._members and uv is not None:
                    if uv.ndim == 1:
                        uv = uv.reshape(-1, 2)
                    fmt += ' 2f'
                    attrs.append('in_uv')
                    streams.append(uv)

                if 'in_tangent' in prog._members and t is not None:
                    fmt += ' 3f'
                    attrs.append('in_tangent')
                    streams.append(t)
                    print("→ Binding tangents to shader")

                if 'in_joints' in prog._members and j is not None:
                    fmt += ' 4f'
                    attrs.append('in_joints')
                    streams.append(j)
                    print("→ Binding joints to shader")

                if 'in_weights' in prog._members and w is not None:
                    fmt += ' 4f'
                    attrs.append('in_weights')
                    streams.append(w)
                    print("→ Binding weights to shader")

                vertices = np.hstack(streams).astype('f4')
                vbo = self.ctx.buffer(vertices.tobytes())
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [(vbo, fmt, *attrs)]
                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao

            # 🔗 Skinning: Compute joint_matrices[] with optional pose override
            if hasattr(mf.asset, 'skin_asset') and mf.asset.skin_asset is not None:
                from zengine.animation.skin_utils import compute_joint_matrices
                from scipy.spatial.transform import Rotation as R

                pose_overrides = {}

                # 🧠 Override joint 6 — "arm_joint_L_2"
                override_index = 6
                # override = np.eye(4, dtype=np.float32)
                # override[:3, 3] = np.array([0.0, 0.0, 0.0])
                # pose_overrides[6] = override
                #
                # # pose_overrides[override_index] = override

                # from scipy.spatial.transform import Rotation as R
                # rot = R.from_euler('z', 0).as_matrix()
                # override = np.eye(4, dtype=np.float32)
                import time
                # angle = np.sin(time.time() * 2.0) * 45  # oscillate between -45 and 45
                #
                # override[:3, :3] = angle
                # pose_overrides[6] = override

                # Inside RenderSystem, before compute_joint_matrices()
                from scipy.spatial.transform import Rotation as R

                pose_overrides = {}

                # Get the original local transform of the joint
                joint_idx = 2  # arm_joint_L_2
                # for joint_idx in range(4, 5):
                node = mf.asset.gltf_data.nodes[joint_idx]
                print("Joint:", joint_idx, node.name)
                T = np.eye(4, dtype=np.float32)
                R_ = np.eye(4, dtype=np.float32)
                S = np.eye(4, dtype=np.float32)

                if node.translation:
                    T[:3, 3] = node.translation
                angle = np.sin(time.time() * 2.0) * 30  # oscillate between -45 and 45

                # Apply local rotation override (e.g. 45° Z rotation)
                rot = R.from_euler('z', -angle, degrees=True)
                R_[:3, :3] = rot.as_matrix()

                if node.scale:
                    S = np.diag(node.scale + [1.0])

                # Final local matrix = T @ R_ @ S (local-space override!)
                pose_overrides[joint_idx] = T @ R_ @ S

                joint_matrices = compute_joint_matrices(
                    mf.asset.gltf_data,
                    mf.asset.skin_asset,
                    pose_overrides=pose_overrides
                )

                # Pad to 64 matrices
                MAX_JOINTS = 64
                joint_matrices_padded = np.tile(np.eye(4, dtype='f4'), (MAX_JOINTS, 1)).reshape((MAX_JOINTS, 4, 4))
                joint_matrices_padded[:len(joint_matrices)] = joint_matrices

                if 'joint_matrices' in prog:
                    prog['joint_matrices'].write(joint_matrices_padded.flatten().astype('f4').tobytes())

            self._vao_cache[key].render()

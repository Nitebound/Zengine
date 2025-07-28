# zengine/ecs/systems/render_system.py
import struct
import time

import moderngl
import numpy as np
import math

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, MeshFilter, Material, MeshRenderer
from zengine.ecs.components.camera import CameraComponent
from zengine.ecs.components.light import LightComponent, LightType
from zengine.util.quaternion import quat_to_mat4
from zengine.animation.skin_utils import compute_joint_matrices
from scipy.spatial.transform import Rotation as R

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
        camera_position = (tr_cam.x, tr_cam.y, tr_cam.z) # Get camera's world position

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
            # Pass camera position to the shader for specular calculations
            if 'camera_position' in prog: prog['camera_position'].write(np.array(camera_position, dtype='f4').tobytes())
            # Pass ambient color to the shader
            if 'u_ambient_color' in prog: prog['u_ambient_color'].value = (0.1, 0.1, 0.1) # Or make this configurable


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

                # Pad light arrays to MAX_LIGHTS to avoid shader errors if less lights are present
                while len(light_positions) < MAX_LIGHTS * 3:
                    light_positions.extend((0.0, 0.0, 0.0))
                while len(light_colors) < MAX_LIGHTS * 3:
                    light_colors.extend((0.0, 0.0, 0.0))
                while len(light_intensities) < MAX_LIGHTS:
                    light_intensities.append(0.0)
                while len(light_ranges) < MAX_LIGHTS:
                    light_ranges.append(0.001) # Use a small non-zero range to avoid division by zero in shader

                prog['light_position'].write(np.array(light_positions, dtype='f4').tobytes())
                prog['light_color'].write(np.array(light_colors, dtype='f4').tobytes())
                prog['light_intensity'].write(np.array(light_intensities, dtype='f4').tobytes())
                prog['light_range'].write(np.array(light_ranges, dtype='f4').tobytes())

            for uname, val in mat.get_all_uniforms().items():
                if uname in prog:
                    try:
                        # Ensure tuples are converted to numpy arrays for writing to uniforms if needed
                        if isinstance(val, tuple):
                            prog[uname].value = np.array(val, dtype='f4')
                        else:
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

                # Dynamically add attributes based on what the shader program expects
                if 'in_normal' in prog._members and n is not None:
                    fmt += ' 3f'
                    attrs.append('in_normal')
                    streams.append(n)

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

                if 'in_joints' in prog._members and j is not None:
                    fmt += ' 4f'
                    attrs.append('in_joints')
                    streams.append(j)

                if 'in_weights' in prog._members and w is not None:
                    fmt += ' 4f'
                    attrs.append('in_weights')
                    streams.append(w)

                # Concatenate all vertex data streams horizontally
                if len(streams) > 0:
                    vertices_combined = np.hstack(streams).astype('f4')
                else:
                    vertices_combined = v.astype('f4') # Only position if no other streams

                vbo = self.ctx.buffer(vertices_combined.tobytes())
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [(vbo, fmt, *attrs)]
                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao
            else:
                vao = self._vao_cache[key] # Retrieve from cache

            # 🔗 Skinning: Compute joint_matrices[] with optional pose override
            if hasattr(mf.asset, 'skin_asset') and mf.asset.skin_asset is not None:
                pose_overrides = {}

                joint_idx = 2  # Example joint index from your original code
                if joint_idx < len(mf.asset.gltf_data.nodes):
                    node = mf.asset.gltf_data.nodes[joint_idx]

                    T = np.eye(4, dtype=np.float32)
                    R_ = np.eye(4, dtype=np.float32)
                    S = np.eye(4, dtype=np.float32)

                    if node.translation:
                        T[:3, 3] = node.translation

                    angle = np.sin(time.time() * 45.0) * 1.1
                    rot = R.from_euler('x', -angle, degrees=True)
                    R_[:3, :3] = rot.as_matrix()

                    pose_overrides[joint_idx] = T @ R_ @ S

                joint_matrices = compute_joint_matrices(
                    mf.asset.gltf_data,
                    mf.asset.skin_asset,
                    pose_overrides=pose_overrides
                )

                MAX_JOINTS = 64
                joint_matrices_padded = np.tile(np.eye(4, dtype='f4'), (MAX_JOINTS, 1)).reshape((MAX_JOINTS, 4, 4))
                joint_matrices_padded[:len(joint_matrices)] = joint_matrices

                if 'joint_matrices' in prog:
                    prog['joint_matrices'].write(joint_matrices_padded.flatten().astype('f4').tobytes())

            vao.render()

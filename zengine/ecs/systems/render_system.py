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
    Rm = quat_to_mat4(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
    S = np.diag([tr.scale_x, tr.scale_y, tr.scale_z, 1.0]).astype('f4')
    return T @ Rm @ S


class RenderSystem(System):
    def __init__(self, ctx, scene):
        super().__init__()
        self.ctx = ctx
        self.scene = scene
        self._vao_cache = {}

        # Depth/cull as you had
        self.ctx.enable(moderngl.DEPTH_TEST)
        # self.ctx.disable(moderngl.CULL_FACE)
        self.ctx.front_face = 'ccw'

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        self.ctx.blend_equation = moderngl.FUNC_ADD

    def on_update(self, dt):
        pass

    def _collect_lights(self):
        """Collect lights once per frame, return padded arrays ready for upload and used count."""
        MAX_LIGHTS = 16
        positions = []
        colors = []
        intensities = []
        ranges = []

        # Use entity_manager consistently
        for eid in self.scene.entity_manager.get_entities_with(Transform, LightComponent):
            lc = self.scene.entity_manager.get_component(eid, LightComponent)
            tr = self.scene.entity_manager.get_component(eid, Transform)
            if lc is None or tr is None:
                continue

            if lc.type == LightType.DIRECTIONAL:
                # derive forward from quaternion (x, y, z, w)
                fwd = R.from_quat([tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w]).apply([0.0, 0.0, -1.0])
                far = 1e6
                pos = (-np.asarray(fwd, dtype='f4') * far)
                positions.append((float(pos[0]), float(pos[1]), float(pos[2])))
                ranges.append(float(far))
            else:
                positions.append((float(tr.x), float(tr.y), float(tr.z)))
                ranges.append(float(lc.range))

            colors.append((float(lc.color[0]), float(lc.color[1]), float(lc.color[2])))
            intensities.append(float(lc.intensity))

        used = min(len(positions), MAX_LIGHTS)

        # pad/clip
        if used < MAX_LIGHTS:
            pad = MAX_LIGHTS - used
            positions += [(0.0, 0.0, 0.0)] * pad
            colors    += [(0.0, 0.0, 0.0)] * pad
            intensities += [0.0] * pad
            ranges      += [0.0] * pad

        positions = positions[:MAX_LIGHTS]
        colors    = colors[:MAX_LIGHTS]
        intensities = intensities[:MAX_LIGHTS]
        ranges      = ranges[:MAX_LIGHTS]

        # pack to contiguous arrays
        pos_arr = np.asarray(positions, dtype='f4').reshape(MAX_LIGHTS, 3)
        col_arr = np.asarray(colors, dtype='f4').reshape(MAX_LIGHTS, 3)
        int_arr = np.asarray(intensities, dtype='f4').reshape(MAX_LIGHTS)
        rng_arr = np.asarray(ranges, dtype='f4').reshape(MAX_LIGHTS)
        return used, pos_arr, col_arr, int_arr, rng_arr

    def on_render(self, renderer):
        cam_e = self.scene.active_camera
        tr_cam = self.scene.entity_manager.get_component(cam_e, Transform)
        cp_cam = self.scene.entity_manager.get_component(cam_e, CameraComponent)

        proj = cp_cam.projection_matrix
        view = cp_cam.view_matrix
        camera_position = (tr_cam.x, tr_cam.y, tr_cam.z)

        # Collect lights once
        used_lights, lp_arr, lc_arr, li_arr, lr_arr = self._collect_lights()

        for eid in self.scene.entity_manager.get_entities_with(Transform, MeshFilter, Material, MeshRenderer):
            tr = self.scene.entity_manager.get_component(eid, Transform)
            mf = self.scene.entity_manager.get_component(eid, MeshFilter)
            mat = self.scene.entity_manager.get_component(eid, Material)

            model = compute_model_matrix(tr)
            prog = mat.shader.program

            # matrices
            if 'model' in prog:      prog['model'].write(model.T.astype('f4').tobytes())
            if 'view' in prog:       prog['view'].write(view.T.astype('f4').tobytes())
            if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())

            # camera + ambient
            if 'camera_position' in prog:
                prog['camera_position'].write(np.asarray(camera_position, dtype='f4').tobytes())
            if 'u_ambient_color' in prog:
                prog['u_ambient_color'].value = (0.0, 0.0, 0.0)

            # lights
            if 'light_count' in prog:
                prog['light_count'].value = used_lights
                if 'light_position' in prog:  prog['light_position'].write(lp_arr.tobytes())
                if 'light_color' in prog:     prog['light_color'].write(lc_arr.tobytes())
                if 'light_intensity' in prog: prog['light_intensity'].write(li_arr.tobytes())
                if 'light_range' in prog:     prog['light_range'].write(lr_arr.tobytes())

            # material uniforms
            for uname, val in mat.get_all_uniforms().items():
                if uname in prog:
                    try:
                        if isinstance(val, np.ndarray):
                            prog[uname].value = tuple(val.tolist())
                        elif isinstance(val, (tuple, list)):
                            prog[uname].value = tuple(val)
                        else:
                            prog[uname].value = val
                    except (KeyError, struct.error, TypeError, AttributeError) as e:
                        print(f"⚠️ Skipping uniform '{uname}': {e}")

            # textures
            for slot, (uname, tex) in enumerate(mat.get_all_textures().items()):
                tex.use(location=slot)
                if uname in prog:
                    prog[uname].value = slot

            # build/reuse VAO
            key = (mf.asset.name, prog.glo)
            if key not in self._vao_cache:
                v = mf.asset.vertices
                n = mf.asset.normals
                uv = mf.asset.uvs
                j = getattr(mf.asset, 'joints', None)
                w = getattr(mf.asset, 'weights', None)
                t = getattr(mf.asset, 'tangents', None)

                fmt = '3f'
                attrs = ['in_position']
                streams = [v]

                # Only attach attributes the shader declares
                members = getattr(prog, '_members', {})

                if 'in_normal' in members and n is not None:
                    fmt += ' 3f'
                    attrs.append('in_normal')
                    streams.append(n)

                if 'in_uv' in members and uv is not None:
                    if uv.ndim == 1:
                        uv = uv.reshape(-1, 2)
                    fmt += ' 2f'
                    attrs.append('in_uv')
                    streams.append(uv)

                if 'in_tangent' in members:
                    if t is None:
                        t = np.zeros((v.shape[0], 3), dtype='f4')
                    fmt += ' 3f'
                    attrs.append('in_tangent')
                    streams.append(t)

                if 'in_joints' in members:
                    if j is None:
                        j = np.zeros((v.shape[0], 4), dtype='f4')
                    fmt += ' 4f'
                    attrs.append('in_joints')
                    streams.append(j.astype('f4'))

                if 'in_weights' in members:
                    if w is None:
                        w = np.zeros((v.shape[0], 4), dtype='f4')
                    fmt += ' 4f'
                    attrs.append('in_weights')
                    streams.append(w.astype('f4'))

                # Concatenate all vertex data streams horizontally
                if streams:
                    vertices_combined = np.hstack(streams).astype('f4')
                else:
                    vertices_combined = v.astype('f4')  # Only position if no other streams

                vbo = self.ctx.buffer(vertices_combined.tobytes())
                ibo = self.ctx.buffer(mf.asset.indices.astype('i4').tobytes())
                content = [(vbo, fmt, *attrs)]
                vao = self.ctx.vertex_array(prog, content, ibo)
                self._vao_cache[key] = vao
            else:
                vao = self._vao_cache[key]

            # Skinning uniform (mat4[64])
            if 'joint_matrices' in prog:
                MAX_JOINTS = 64
                if hasattr(mf.asset, 'skin_asset') and mf.asset.skin_asset is not None:
                    joint_matrices = compute_joint_matrices(
                        mf.asset.gltf_data,
                        mf.asset.skin_asset,
                        pose_overrides={}
                    )
                    jm = np.tile(np.eye(4, dtype='f4'), (MAX_JOINTS, 1)).reshape((MAX_JOINTS, 4, 4))
                    jm[:len(joint_matrices)] = joint_matrices
                    prog['joint_matrices'].write(jm.astype('f4').tobytes())
                else:
                    identity_joints = np.tile(np.eye(4, dtype='f4'), (MAX_JOINTS, 1)).reshape((MAX_JOINTS, 4, 4))
                    prog['joint_matrices'].write(identity_joints.astype('f4').tobytes())

            # Render
            self.ctx.depth_mask = True
            vao.render()

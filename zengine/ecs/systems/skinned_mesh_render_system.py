# zengine/ecs/systems/skinned_mesh_render_system.py

import numpy as np
from zengine.ecs.systems.system         import System
from zengine.ecs.components.transform   import Transform
from zengine.ecs.components.skinned_mesh import SkinnedMesh
from zengine.ecs.components.skin         import Skin
from zengine.ecs.components.material     import Material
from zengine.ecs.components.camera       import CameraComponent
from zengine.assets.mesh_registry        import MeshRegistry
from zengine.ecs.systems.render_system   import compute_model_matrix

class SkinnedMeshRenderSystem(System):
    def __init__(self):
        super().__init__()
        self._cache = {}  # mesh_key → (vao, index_count)

    def on_added(self, scene):
        super().on_added(scene)
        # register built-in default meshes if needed
        import zengine.assets.default_meshes  # noqa

    def on_render(self, renderer):
        # 1) find the active camera & its transform
        cam_comp = None
        cam_tr   = None
        for cid in self.em.get_entities_with(CameraComponent, Transform):
            c = self.em.get_component(cid, CameraComponent)
            if c.active:
                cam_comp = c
                cam_tr   = self.em.get_component(cid, Transform)
                break
        if cam_comp is None:
            return

        view_mat = cam_comp.view_matrix
        proj_mat = cam_comp.projection_matrix
        cam_pos  = (cam_tr.x, cam_tr.y, cam_tr.z)
        ctx      = self.scene.window.ctx

        # 2) draw every skinned-mesh entity
        for eid in self.em.get_entities_with(Transform, SkinnedMesh, Skin, Material):
            tr   = self.em.get_component(eid, Transform)
            sm   = self.em.get_component(eid, SkinnedMesh)
            skin = self.em.get_component(eid, Skin)
            mat  = self.em.get_component(eid, Material)
            mesh = MeshRegistry.get(sm.mesh_key)

            prog = getattr(mat.shader, "program", mat.shader)

            # 3) cache or build VAO
            if sm.mesh_key not in self._cache:
                # static buffers
                vbo = ctx.buffer(mesh.vertices.tobytes())
                nbo = ctx.buffer(mesh.normals.tobytes())
                ibo = ctx.buffer(mesh.indices.tobytes())

                # UVs
                uvbo = None
                if hasattr(mesh, "uvs") and mesh.uvs is not None:
                    uvbo = ctx.buffer(mesh.uvs.tobytes())

                # joints & weights
                jbo = None
                if mesh.joints is not None:
                    # cast to signed int32 to match ivec4 in the shader
                    jbo = ctx.buffer(mesh.joints.astype("i4").tobytes())
                wbo = None
                if mesh.weights is not None:
                    wbo = ctx.buffer(mesh.weights.astype("f4").tobytes())

                attribs = [
                    (vbo, "3f", "in_position"),
                    (nbo, "3f", "in_normal"),
                ]
                if "in_uv"      in prog and uvbo is not None:
                    attribs.append((uvbo, "2f", "in_uv"))
                if "in_joints"  in prog and jbo  is not None:
                    attribs.append((jbo,  "4i", "in_joints"))
                if "in_weights" in prog and wbo  is not None:
                    attribs.append((wbo,  "4f", "in_weights"))

                vao = ctx.vertex_array(prog, attribs, ibo)
                self._cache[sm.mesh_key] = (vao, len(mesh.indices))

            vao, count = self._cache[sm.mesh_key]

            # 4) set transform uniforms
            model = compute_model_matrix(tr)
            prog["model"].write(model.T.tobytes())
            prog["view"].write(view_mat.T.tobytes())
            prog["projection"].write(proj_mat.T.tobytes())
            prog["view_pos"].value = cam_pos

            # 5) upload jointMatrices if shader expects them
            if "jointMatrices" in prog:
                uni = prog["jointMatrices"]
                expected = uni.array_length
                jm = skin.joint_matrices.astype("f4")  # (J,4,4)
                J = jm.shape[0]
                if J < expected:
                    pad = np.tile(np.eye(4, dtype="f4")[None, ...], (expected - J, 1, 1))
                    jm_full = np.concatenate([jm, pad], axis=0)
                else:
                    jm_full = jm[:expected]
                uni.write(jm_full.reshape(-1).tobytes())

            # 6) bind textures & material properties
            unit = 0
            for name, tex in mat.textures.items():
                if name in prog:
                    tex.use(unit)
                    prog[name].value = unit
                    unit += 1
            prog["object_color"].write(np.array(mat.albedo, dtype="f4").tobytes())
            prog["ambient_strength"].value   = mat.ambient_strength
            prog["specular_strength"].value  = mat.specular_strength
            prog["shininess"].value          = mat.shininess

            # 7) draw the mesh
            vao.render(mode=ctx.TRIANGLES, vertices=count)

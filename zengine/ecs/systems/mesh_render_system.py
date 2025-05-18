# zengine/ecs/systems/mesh_render_system.py

import numpy as np
from zengine.ecs.systems.system       import System
from zengine.ecs.components.transform import Transform
from zengine.ecs.components.camera    import CameraComponent
from zengine.ecs.components.light     import LightComponent, LightType
from zengine.ecs.components.mesh_filter import MeshFilter
from zengine.ecs.components.material  import Material
from zengine.ecs.systems.render_system import compute_model_matrix

MAX_LIGHTS = 8

class MeshRenderSystem(System):
    def __init__(self):
        super().__init__()
        self._cache = {}

    def on_added(self, scene):
        super().on_added(scene)
        import zengine.assets.default_meshes

    def on_render(self, renderer):
        # 1) gather camera
        cam_c, cam_t = None, None
        for eid in self.em.get_entities_with(CameraComponent, Transform):
            c = self.em.get_component(eid, CameraComponent)
            if c.active:
                cam_c = c
                cam_t = self.em.get_component(eid, Transform)
                break
        if cam_c is None:
            return

        view_mat = cam_c.view_matrix
        proj_mat = cam_c.projection_matrix
        view_pos = (cam_t.x, cam_t.y, cam_t.z)
        ctx      = self.scene.window.ctx

        # 2) gather lights
        types, poses, dirs, cols, ints = [], [], [], [], []
        for eid in self.em.get_entities_with(LightComponent):
            if len(types) >= MAX_LIGHTS:
                break
            lc = self.em.get_component(eid, LightComponent)
            types.append(int(lc.type.value))
            cols.append(lc.color)
            ints.append(lc.intensity)
            if lc.type == LightType.POINT:
                tr = self.em.get_component(eid, Transform)
                poses.append((tr.x, tr.y, tr.z))
                dirs.append((0.0,0.0,0.0))
            else:
                poses.append((0.0,0.0,0.0))
                dirs.append(lc.direction)

        # pad to MAX_LIGHTS
        while len(types) < MAX_LIGHTS:
            types.append(0); poses.append((0,0,0))
            dirs.append((0,0,0)); cols.append((0,0,0)); ints.append(0.0)

        # 3) render each mesh+material
        for eid in self.em.get_entities_with(Transform, MeshFilter, Material):
            tr  = self.em.get_component(eid, Transform)
            mf  = self.em.get_component(eid, MeshFilter)
            mat = self.em.get_component(eid, Material)
            mesh= mf.mesh
            prog= getattr(mat.shader, "program", mat.shader)

            # cache VAO
            if mesh.name not in self._cache:
                vbo  = ctx.buffer(mesh.vertices.tobytes())
                nbo  = ctx.buffer(mesh.normals.tobytes())
                uvbo = ctx.buffer(mesh.uvs.tobytes())
                ibo  = ctx.buffer(mesh.indices.tobytes())
                vao = ctx.vertex_array(
                    prog,
                    [
                      (vbo,  "3f", "in_position"),
                      (nbo,  "3f", "in_normal"),
                      (uvbo, "2f", "in_uv"),
                    ],
                    ibo
                )
                self._cache[mesh.name] = (vao, len(mesh.indices))
            vao, count = self._cache[mesh.name]

            # upload transforms
            model = compute_model_matrix(tr)
            prog["model"].write(model.T.tobytes())
            prog["view"].write(view_mat.T.tobytes())
            prog["projection"].write(proj_mat.T.tobytes())
            prog["view_pos"].value = view_pos

            # upload lights
            prog["numLights"].value           = len(types)
            prog["light_types"].write(
                np.array(types, dtype="i4").tobytes()
            )
            prog["light_positions"].write(
                np.array(poses, dtype="f4").tobytes()
            )
            prog["light_directions"].write(
                np.array(dirs, dtype="f4").tobytes()
            )
            prog["light_colors"].write(
                np.array(cols, dtype="f4").tobytes()
            )
            prog["light_intensities"].write(
                np.array(ints, dtype="f4").tobytes()
            )

            # upload material
            prog["ambient_strength"].value   = mat.ambient_strength
            prog["specular_strength"].value  = mat.specular_strength
            prog["shininess"].value          = mat.shininess
            prog["object_color"].write(
                np.array(mat.albedo, dtype="f4").tobytes()
            )

            # bind textures
            unit = 0
            for name, tex in mat.textures.items():
                if name in prog:
                    tex.use(unit)
                    prog[name].value = unit
                    unit += 1

            # extra uniforms
            for name,val in mat.extra_uniforms.items():
                if name in prog:
                    if hasattr(val,"tobytes"):
                        prog[name].write(val.tobytes())
                    else:
                        prog[name].value = val

            vao.render(mode=ctx.TRIANGLES, vertices=count)

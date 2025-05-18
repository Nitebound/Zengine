import math
from pygltflib import GLTF2
import numpy as np

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, SkinnedMesh, Skin, Skeleton
from zengine.ecs.components.material import Material
from zengine.assets.mesh_registry     import MeshRegistry
from zengine.assets.material_registry import MaterialRegistry
from zengine.assets.texture_registry  import TextureRegistry
from zengine.assets.gltf_loader       import load_gltf, gltf_cache, read_inverse_bind_matrices

def quat_to_euler_deg(q):
    x, y, z, w = q
    # roll (X axis)
    t0 = +2.0 * (w*x + y*z)
    t1 = +1.0 - 2.0 * (x*x + y*y)
    roll = math.atan2(t0, t1)
    # pitch (Y axis)
    t2 = +2.0 * (w*y - z*x)
    t2 = max(min(t2, 1.0), -1.0)
    pitch = math.asin(t2)
    # yaw (Z axis)
    t3 = +2.0 * (w*z + x*y)
    t4 = +1.0 - 2.0 * (y*y + z*z)
    yaw = math.atan2(t3, t4)
    return (math.degrees(roll), math.degrees(pitch), math.degrees(yaw))


class GLTFImportSystem(System):
    def __init__(self, path: str, ctx, skin_shader):
        super().__init__()
        self.path        = path
        self.ctx         = ctx
        self.skin_shader = skin_shader

    def on_added(self, scene):
        super().on_added(scene)

        # load glTF
        model_id = load_gltf(self.path, self.ctx)
        gltf     = gltf_cache[model_id]

        # prepare maps: node_index → entity_id, and parent
        scene.node_map    = {}
        scene.node_parent = {}

        def recurse(node_idx, parent_idx=None):
            node = gltf.nodes[node_idx]
            eid  = scene.entity_manager.create_entity()

            # record
            scene.node_map[node_idx]    = eid
            scene.node_parent[node_idx] = parent_idx

            # 1) Transform with safe defaults
            t = node.translation or [0.0, 0.0, 0.0]
            s = node.scale       or [1.0, 1.0, 1.0]
            r = node.rotation    or [0.0, 0.0, 0.0, 1.0]
            rx, ry, rz = quat_to_euler_deg(r)
            scene.entity_manager.add_component(eid, Transform(
                x=t[0], y=t[1], z=t[2],
                rot_x=rx, rot_y=ry, rot_z=rz,
                scale_x=s[0], scale_y=s[1], scale_z=s[2]
            ))

            # 2) If node has mesh, attach SkinnedMesh + Material
            if node.mesh is not None:
                mesh_def = gltf.meshes[node.mesh]
                for pi, prim in enumerate(mesh_def.primitives or []):
                    mesh_key = f"{mesh_def.name or 'mesh'}_prim{pi}"
                    mat_idx  = prim.material or 0
                    mat_name = gltf.materials[mat_idx].name or f"material_{mat_idx}"

                    # SkinnedMesh marker
                    scene.entity_manager.add_component(eid,
                        SkinnedMesh(
                            mesh_key     = mesh_key,
                            material_key = mat_name,
                            skin_key     = node.skin or "",
                            node_index   = node_idx
                        )
                    )

                    # pick up the registered MaterialAsset
                    ma = MaterialRegistry.get(mat_name)
                    textures = {}
                    for uni, key in ma.textures.items():
                        tex_asset     = TextureRegistry.get(key)
                        textures[uni] = tex_asset.texture

                    # attach live Material
                    scene.entity_manager.add_component(eid,
                        Material(
                            shader            = self.skin_shader,
                            albedo            = ma.albedo,
                            ambient_strength  = getattr(ma, "ambient_strength", 0.1),
                            specular_strength = getattr(ma, "specular_strength", 0.5),
                            shininess         = getattr(ma, "shininess", 32.0),
                            textures          = textures
                        )
                    )

            # 3) If node has skin, attach Skin + Skeleton
            if node.skin is not None:
                skin_def = gltf.skins[node.skin]
                ibms     = read_inverse_bind_matrices(gltf, skin_def)
                scene.entity_manager.add_component(eid,
                    Skin(
                        joint_nodes           = skin_def.joints,
                        inverse_bind_matrices = ibms
                    )
                )
                scene.entity_manager.add_component(eid,
                    Skeleton(
                        root_node = node_idx,
                        joints    = skin_def.joints
                    )
                )

            # 4) Recurse children
            for child in node.children or []:
                recurse(child, node_idx)

        # Kick off recursion from all scene roots
        roots = []
        if gltf.scenes:
            for sd in gltf.scenes:
                roots += sd.nodes or []
        else:
            roots = list(range(len(gltf.nodes)))

        for r in roots:
            recurse(r)

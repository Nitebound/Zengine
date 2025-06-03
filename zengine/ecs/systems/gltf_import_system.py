# zengine/ecs/systems/gltf_import_system.py

import math
import numpy as np
from pygltflib import GLTF2
from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform, SkinnedMesh, Skin, Skeleton, Material
from zengine.ecs.components.mesh_filter import MeshFilter       # ← NEW
from zengine.assets.mesh_registry import MeshRegistry
from zengine.assets.material_registry import MaterialRegistry
from zengine.assets.texture_registry import TextureRegistry
from zengine.assets.gltf_loader import load_gltf, gltf_cache, read_inverse_bind_matrices

def quat_to_euler_deg(q):
    x, y, z, w = q
    # (existing conversion–unused below, but you can keep it for debugging)
    # …

class GLTFImportSystem(System):
    def __init__(self, path: str, ctx, skin_shader):
        super().__init__()
        self.path        = path
        self.ctx         = ctx
        self.skin_shader = skin_shader

    def on_added(self, scene):
        super().on_added(scene)
        model_id = load_gltf(self.path, self.ctx)
        gltf     = gltf_cache[model_id]

        scene.node_map    = {}
        scene.node_parent = {}

        def recurse(node_idx, parent_idx=None):
            node = gltf.nodes[node_idx]
            eid  = scene.entity_manager.create_entity()
            scene.node_map[node_idx]    = eid
            scene.node_parent[node_idx] = parent_idx

            # --- HANDLE TRS FROM GLTF ---
            # fallback T/R/S
            t = node.translation if node.translation is not None else [0.0, 0.0, 0.0]
            s = node.scale       if node.scale       is not None else [1.0, 1.0, 1.0]
            r = node.rotation    if node.rotation    is not None else [0.0, 0.0, 0.0, 1.0]

            # **Store quaternion directly** so your render compute uses it
            scene.entity_manager.add_component(eid, Transform(
                x      = float(t[0]),
                y      = float(t[1]),
                z      = float(t[2]),
                rotation_x = float(r[0]),
                rotation_y = float(r[1]),
                rotation_z = float(r[2]),
                rotation_w = float(r[3]),
                scale_x= float(s[0]),
                scale_y= float(s[1]),
                scale_z= float(s[2]),
            ))

            # --- IMPORT MESH PRIMITIVES ---
            if node.mesh is not None:
                mesh_def = gltf.meshes[node.mesh]
                for pi, prim in enumerate(mesh_def.primitives or []):
                    mesh_key = f"{mesh_def.name or 'mesh'}_prim{pi}"
                    # 1) attach MeshFilter so the renderer has the buffers
                    mesh_asset = MeshRegistry.get(mesh_key)
                    scene.entity_manager.add_component(eid, MeshFilter(mesh_asset))

                    # 2) let the SkinnedMeshRenderSystem know this is skinned
                    mat_idx  = prim.material or 0
                    mat_name = (gltf.materials[mat_idx].name
                                if gltf.materials and gltf.materials[mat_idx].name
                                else f"material_{mat_idx}")

                    scene.entity_manager.add_component(eid, SkinnedMesh(
                        mesh_key     = mesh_key,
                        material_key = mat_name,
                        skin_key     = node.skin or "",
                        node_index   = node_idx
                    ))

                    # 3) attach the Material component
                    ma = MaterialRegistry.get(mat_name)
                    textures = {}
                    for uni, key in ma.textures.items():
                        tex_asset = TextureRegistry.get(key)
                        if tex_asset:
                            textures[uni] = tex_asset.texture

                    scene.entity_manager.add_component(eid, Material(
                        shader            = self.skin_shader,
                        albedo            = ma.albedo,
                        ambient_strength  = getattr(ma, "ambient_strength", 0.1),
                        specular_strength = getattr(ma, "specular_strength", 0.5),
                        shininess         = getattr(ma, "shininess", 32.0),
                        textures          = textures
                    ))

            # --- IMPORT SKIN & SKELETON ---
            if node.skin is not None:
                skin_def = gltf.skins[node.skin]
                ibms     = read_inverse_bind_matrices(gltf, skin_def)
                scene.entity_manager.add_component(eid, Skin(
                    joint_nodes           = skin_def.joints or [],
                    inverse_bind_matrices = ibms
                ))
                scene.entity_manager.add_component(eid, Skeleton(
                    root_node = node_idx,
                    joints    = skin_def.joints or []
                ))

            # recurse children
            for child_idx in node.children or []:
                recurse(child_idx, node_idx)

        # kick off at all scene roots
        roots = []
        if gltf.scenes:
            for sd in gltf.scenes:
                roots += sd.nodes or []
        else:
            roots = list(range(len(gltf.nodes)))

        for r in roots:
            recurse(r)

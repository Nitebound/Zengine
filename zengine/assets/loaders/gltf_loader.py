import os
import io
import trimesh
import numpy as np
from PIL import Image
from pygltflib import GLTF2
from zengine.assets.mesh_asset import MeshAsset
from zengine.assets.skin_asset import SkinAsset
from zengine.ecs.components import Material

def create_texture_from_numpy(ctx, image_data, width, height):
    return ctx.texture((width, height), 4, image_data.tobytes())

def generate_tangents(vertices, normals, uvs, indices):
    tangents = np.zeros_like(vertices, dtype=np.float32)
    tan1 = np.zeros_like(vertices, dtype=np.float32)

    for i in range(0, len(indices), 3):
        i1, i2, i3 = indices[i], indices[i+1], indices[i+2]
        v1, v2, v3 = vertices[i1], vertices[i2], vertices[i3]
        w1, w2, w3 = uvs[i1], uvs[i2], uvs[i3]

        x1, x2 = v2 - v1, v3 - v1
        y1, y2 = w2 - w1, w3 - w1

        r = 1.0 / (y1[0] * y2[1] - y2[0] * y1[1] + 1e-8)
        sdir = (y2[1] * x1 - y1[1] * x2) * r
        tan1[i1] += sdir
        tan1[i2] += sdir
        tan1[i3] += sdir

    for i in range(len(vertices)):
        n = normals[i]
        t = tan1[i]
        tangents[i] = (t - n * np.dot(n, t))
        tangents[i] = tangents[i] / (np.linalg.norm(tangents[i]) + 1e-6)

    return tangents

def load_accessor_data(gltf, accessor_idx):
    accessor = gltf.accessors[accessor_idx]
    buffer_view = gltf.bufferViews[accessor.bufferView]
    buffer = gltf.buffers[buffer_view.buffer]
    data = np.frombuffer(
        bytes(gltf.get_data_from_buffer_uri(buffer.uri)),
        dtype=np.uint8
    )

    offset = buffer_view.byteOffset or 0
    start = offset + (accessor.byteOffset or 0)

    component_type = {
        5120: np.int8,
        5121: np.uint8,
        5122: np.int16,
        5123: np.uint16,
        5125: np.uint32,
        5126: np.float32
    }[accessor.componentType]

    type_count = {
        "SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16
    }[accessor.type]


    count = accessor.count
    dtype = np.dtype(component_type)
    data = data[start:start + count * type_count * dtype.itemsize]
    return np.frombuffer(data, dtype=component_type).reshape((count, type_count))

import numpy as np
from scipy.spatial.transform import Rotation as R
from zengine.assets.skin_asset import SkinAsset  # Adjust path if needed

def build_local_matrix(node):
    T = np.eye(4, dtype=np.float32)
    Rm = np.eye(4, dtype=np.float32)
    S = np.eye(4, dtype=np.float32)

    if node.translation:
        T[:3, 3] = node.translation
    if node.rotation:
        r = R.from_quat(node.rotation)
        Rm[:3, :3] = r.as_matrix()
    if node.scale:
        S = np.diag(node.scale + [1.0])

    return T @ Rm @ S

def compute_global_transforms(gltf, node_transforms):
    global_transforms = [None] * len(gltf.nodes)

    def traverse(node_idx, parent_mat):
        local = node_transforms[node_idx]
        global_transforms[node_idx] = parent_mat @ local
        children = gltf.nodes[node_idx].children or []
        for child in children:
            traverse(child, global_transforms[node_idx])

    all_children = set(c for n in gltf.nodes if n.children for c in n.children)
    root_nodes = [i for i in range(len(gltf.nodes)) if i not in all_children]
    for root in root_nodes:
        traverse(root, np.eye(4, dtype=np.float32))

    return global_transforms

def load_skin_data(gltf, skin):
    skin_obj = gltf.skins[skin] if isinstance(skin, int) else skin
    joint_nodes = skin_obj.joints
    joint_names = [gltf.nodes[j].name for j in joint_nodes]

    # Build transforms
    node_transforms = [build_local_matrix(n) for n in gltf.nodes]
    global_transforms = compute_global_transforms(gltf, node_transforms)

    # Lock in inverse bind matrices from rest pose
    inverse_binds = [np.linalg.inv(global_transforms[j]) for j in joint_nodes]

    return SkinAsset(
        joint_names=joint_names,
        joint_nodes=joint_nodes,
        inverse_bind_matrices=inverse_binds
    )

def load_gltf_model(ctx, path: str, shader):
    path = os.path.abspath(path)
    directory = os.path.dirname(path)

    gltf = GLTF2().load(path)
    scene = trimesh.load(path, resolver=trimesh.resolvers.FilePathResolver(directory), force='scene')

    result = []

    for mesh_index, (name, geom) in enumerate(scene.geometry.items()):
        verts = geom.vertices
        norms = geom.vertex_normals
        uvs = geom.visual.uv if geom.visual.kind == 'texture' else None
        tris = geom.faces.flatten()

        tangents = None
        if uvs is not None and verts is not None and tris is not None:
            try:
                tangents = generate_tangents(verts, norms, uvs, tris)
                print(f"✅ Tangents generated for {name}: {tangents.shape}")
            except Exception as e:
                print(f"⚠️ Tangent generation failed for {name}: {e}")

        joints = weights = None
        skin_asset = None

        if mesh_index < len(gltf.meshes):
            mesh = gltf.meshes[mesh_index]
            prim = mesh.primitives[0]

            j_idx = prim.attributes.JOINTS_0
            w_idx = prim.attributes.WEIGHTS_0

            if j_idx is not None and w_idx is not None:
                try:
                    joints = load_accessor_data(gltf, j_idx).astype(np.float32)
                    weights = load_accessor_data(gltf, w_idx).astype(np.float32)
                    # print(f"🦴 Extracted joints/weights for {name}: {joints.shape}, {weights.shape}")
                    # print(f"   → JOINTS min/max: {joints.min()} / {joints.max()}")
                    # print(f"   → WEIGHTS row 0 sum: {np.sum(weights[0])}")
                    # print(f"   → WEIGHTS row 0: {weights[0]}")
                    # print(f"   → JOINTS row 0: {joints[0]}")
                    v = 100  # Or pick any vertex index
                    print(f"\n🎯 Vertex {v} joints: {joints[v]}")
                    print(f"🎯 Vertex {v} weights: {weights[v]}")

                except Exception as e:
                    print(f"⚠️ Failed to load joint/weight data for {name}: {e}")
            else:
                print(f"🚫 JOINTS_0 or WEIGHTS_0 missing in GLTF for {name}")

            # Find the node that uses this mesh
            skin_index = None
            for i, node in enumerate(gltf.nodes):
                if node.mesh == mesh_index:
                    skin_index = node.skin
                    break

            if skin_index is not None:
                try:
                    skin_asset = load_skin_data(gltf, skin_index)
                    print(f"🔗 Skin loaded for {name}: {len(skin_asset.joint_names)} joints")
                except Exception as e:
                    print(f"⚠️ Failed to load skin data for {name}: {e}")

        mesh = MeshAsset(
            name=name,
            vertices=verts.astype('f4'),
            normals=norms.astype('f4'),
            indices=tris.astype('i4'),
            uvs=uvs.astype('f4') if uvs is not None else None,
            tangents=tangents.astype('f4') if tangents is not None else None,
            joints=joints if joints is not None else None,
            weights=weights if weights is not None else None
        )

        texture = None
        fallback_color = (1.0, 1.0, 1.0, 1.0)

        try:
            mat = getattr(geom.visual, 'material', None)
            if mat:
                if hasattr(mat, 'baseColorFactor') and mat.baseColorFactor:
                    fallback_color = tuple(mat.baseColorFactor)
                    print(f"🎨 baseColorFactor for {name}: {fallback_color}")

                if hasattr(mat, 'baseColorTexture'):
                    tex = mat.baseColorTexture
                    if isinstance(tex, Image.Image):
                        image = tex.convert("RGBA")
                        img_np = np.array(image, dtype=np.uint8)
                        width, height = image.size
                        texture = create_texture_from_numpy(ctx, img_np, width, height)
                        print(f"🖼️ baseColorTexture loaded for {name}")
                elif hasattr(mat, 'image') and mat.image and hasattr(mat.image, 'data'):
                    image = Image.open(io.BytesIO(mat.image.data)).convert("RGBA")
                    img_np = np.array(image, dtype=np.uint8)
                    width, height = image.size
                    texture = create_texture_from_numpy(ctx, img_np, width, height)
                    print(f"🖼️ Embedded texture loaded for {name}")
        except Exception as e:
            print(f"⚠️ Material parse failed for {name}: {e}")

        mat = Material(
            shader=shader,
            albedo=fallback_color,
            albedo_texture=texture,
            custom_uniforms={
                "u_has_albedo_map": texture is not None,
                "albedo": fallback_color,
                "u_ambient_color": (0.05, 0.05, 0.05)
            }
        )

        mesh.gltf_data = gltf  # Attach to MeshAsset for later matrix calculations
        mesh.skin_asset = skin_asset  # Attach SkinAsset for render-time skinning
        result.append((mesh, mat, skin_asset))

        print(f"{name} has normals: {hasattr(geom, 'vertex_normals')}, min/max: {np.min(norms)} / {np.max(norms)}")

    return result

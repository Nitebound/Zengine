import os
import io
import trimesh
import numpy as np
from PIL import Image
from zengine.assets.mesh_asset import MeshAsset
from zengine.ecs.components import Material

# 💡 You may need to move this where your render context is available
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

def load_gltf_model(ctx, path: str, shader):
    path = os.path.abspath(path)
    directory = os.path.dirname(path)

    scene = trimesh.load(path, resolver=trimesh.resolvers.FilePathResolver(directory), force='scene')
    result = []

    for name, geom in scene.geometry.items():
        verts = geom.vertices
        norms = geom.vertex_normals
        uvs = geom.visual.uv if geom.visual.kind == 'texture' else None
        tris = geom.faces.flatten()

        if uvs is not None:
            print(f"🧵 Sample UVs for {name}: {uvs[:5]}")

        tangents = None
        if uvs is not None and verts is not None and tris is not None:
            try:
                tangents = generate_tangents(verts, norms, uvs, tris)
                print(f"✅ Tangents generated for {name}: {tangents.shape}")
            except Exception as e:
                print(f"⚠️ Tangent generation failed for {name}: {e}")

        mesh = MeshAsset(
            name=name,
            vertices=verts.astype('f4'),
            normals=norms.astype('f4'),
            indices=tris.astype('i4'),
            uvs=uvs.astype('f4') if uvs is not None else None,
            tangents=tangents.astype('f4') if tangents is not None else None
        )

        texture = None
        fallback_color = (1.0, 1.0, 1.0, 1.0)

        try:
            mat = getattr(geom.visual, 'material', None)
            if mat:
                if hasattr(mat, 'baseColorFactor') and mat.baseColorFactor:
                    fallback_color = tuple(mat.baseColorFactor)
                    print(f"🎨 Using baseColorFactor for {name}: {fallback_color}")

                if hasattr(mat, 'baseColorTexture'):
                    tex = mat.baseColorTexture
                    if isinstance(tex, Image.Image):
                        image = tex.convert("RGBA")
                        img_np = np.array(image, dtype=np.uint8)
                        width, height = image.size
                        texture = create_texture_from_numpy(ctx, img_np, width, height)
                        print(f"🖼️ baseColorTexture (PIL) loaded for {name}")
                    else:
                        print(f"⚠️ baseColorTexture is not PIL.Image: {type(tex)}")

                elif hasattr(mat, 'image') and mat.image and hasattr(mat.image, 'data'):
                    image = Image.open(io.BytesIO(mat.image.data)).convert("RGBA")
                    img_np = np.array(image, dtype=np.uint8)
                    width, height = image.size
                    texture = create_texture_from_numpy(ctx, img_np, width, height)
                    print(f"🖼️ Embedded image loaded for {name}")
        except Exception as e:
            print(f"⚠️ Material parsing failed for {name}: {e}")

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

        result.append((mesh, mat))

        print(f"{name} kind = {geom.visual.kind}")
        print(f"{name} has normals:", hasattr(geom, 'vertex_normals'))
        print("normals min/max:", np.min(norms), np.max(norms))

    return result

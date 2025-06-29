import os
import trimesh
import numpy as np
from zengine.assets.mesh_asset import MeshAsset
from zengine.graphics.texture_loader import load_texture_2d
from zengine.ecs.components import Material

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

        tangents = None
        if uvs is not None and hasattr(geom, 'faces'):
            try:
                geom_copy = geom.copy()
                geom_copy.fix_normals()
                geom_copy.visual.uv = uvs
                geom_copy.generate_vertex_normals()
                geom_copy = geom_copy.process(validate=True)
                tan = geom_copy.vertex_attributes.get('tangent', None)

                if tan is not None:
                    tangents = tan[:, :3]
                    print(f"✅ Tangents loaded for {name}: {tangents.shape}")
                else:
                    print(f"⚠️ No tangents generated for {name}")
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
        try:
            mat = getattr(geom.visual, 'material', None)
            if mat:
                tex_path = getattr(mat, 'image', None)
                if tex_path:
                    texture = load_texture_2d(ctx, tex_path)
                elif hasattr(mat, 'baseColorTexture') and isinstance(mat.baseColorTexture, str):
                    texture = load_texture_2d(ctx, os.path.join(directory, mat.baseColorTexture))
        except Exception as e:
            print(f"⚠️ Texture load failed for {name}: {e}")

        fallback_color = (1.0, 1.0, 1.0, 1.0)

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

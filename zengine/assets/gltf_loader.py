# zengine/assets/gltf_loader.py

import base64
import re
from pathlib import Path

import numpy as np
from pygltflib import GLTF2

from zengine.assets.mesh_asset     import MeshAsset
from zengine.assets.texture_asset  import TextureAsset
from zengine.assets.material_asset import MaterialAsset
from zengine.assets.mesh_registry    import MeshRegistry
from zengine.assets.texture_registry import TextureRegistry
from zengine.assets.material_registry import MaterialRegistry
from zengine.graphics.texture_loader import load_texture_2d

# cache parsed GLTF2 objects by filename
gltf_cache: dict[str, GLTF2] = {}

# regex to detect data-URI buffers
_DATA_URI = re.compile(r"^data:.*;base64,")

# mapping from glTF componentType to numpy dtype
_COMPONENT_DTYPE = {
    5120: np.int8,
    5121: np.uint8,
    5122: np.int16,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32,
}

# how many components per accessor type
_TYPE_NUM = {
    "SCALAR": 1,
    "VEC2":   2,
    "VEC3":   3,
    "VEC4":   4,
    "MAT2":   4,
    "MAT3":   9,
    "MAT4":   16,
}


def read_accessor(gltf: GLTF2, acc_index: int) -> np.ndarray:
    """
    Read any glTF accessor into a (count × num_components) numpy array.
    Expects that gltf._buffers has been populated by load_gltf().
    """
    accessor = gltf.accessors[acc_index]
    view     = gltf.bufferViews[accessor.bufferView]
    raw_buf  = gltf._buffers[view.buffer]
    start    = view.byteOffset or 0
    length   = view.byteLength
    chunk    = raw_buf[start : start + length]

    dtype    = _COMPONENT_DTYPE[accessor.componentType]
    num_comp = _TYPE_NUM[accessor.type]
    offset   = accessor.byteOffset or 0

    arr = np.frombuffer(
        chunk,
        dtype=dtype,
        count=accessor.count * num_comp,
        offset=offset
    )
    return arr.reshape((accessor.count, num_comp))


def read_inverse_bind_matrices(gltf: GLTF2, skin) -> np.ndarray:
    """
    Returns an (n_joints × 4 × 4) float32 array of
    inverse-bind matrices for the given Skin.
    """
    if skin.inverseBindMatrices is None:
        count = len(skin.joints)
        # identity for each joint
        return np.tile(np.eye(4, dtype='f4')[None, ...], (count, 1, 1))

    ibm_flat = read_accessor(gltf, skin.inverseBindMatrices)  # (count×16)
    return ibm_flat.astype('f4').reshape(-1, 4, 4)


def load_gltf(path: str, ctx) -> str:
    """
    Loads a .gltf or .glb file, registers all contained MeshAsset,
    TextureAsset, and MaterialAsset entries, and returns the path key.
    """
    gltf = GLTF2().load(path)
    gltf_cache[path] = gltf
    base_dir = Path(path).parent

    # 1) Load raw buffer blobs into gltf._buffers
    buffers = []
    for buf in gltf.buffers or []:
        uri = buf.uri
        if uri and _DATA_URI.match(uri):
            # data:...;base64,
            b64 = uri.split(",", 1)[1]
            buffers.append(base64.b64decode(b64))
        elif uri:
            buffers.append((base_dir / uri).read_bytes())
        else:
            # .glb binary section
            buffers.append(gltf.binary_blob())
    gltf._buffers = buffers

    # 2) Images → TextureAsset
    for i, img in enumerate(gltf.images or []):
        if not img.uri:
            continue
        tex = load_texture_2d(ctx, str(base_dir / img.uri))
        TextureRegistry.register(TextureAsset(f"gltf_img_{i}", tex))

    # 3) Materials → MaterialAsset
    for i, mat in enumerate(gltf.materials or []):
        key = mat.name or f"material_{i}"
        pbr = mat.pbrMetallicRoughness
        textures = {}
        if pbr.baseColorTexture:
            tidx   = pbr.baseColorTexture.index
            src    = gltf.textures[tidx].source
            texkey = f"gltf_img_{src}"
            textures["albedo_map"] = texkey
        ma = MaterialAsset(
            name     = key,
            shader   = "skinning_phong",    # your skinning shader key
            albedo   = (1, 1, 1, 1),
            textures = textures
        )
        MaterialRegistry.register(ma)

    # 4) Meshes & Primitives → MeshAsset
    for mesh in gltf.meshes or []:
        mesh_name = mesh.name or "mesh"
        for pi, prim in enumerate(mesh.primitives or []):
            pos    = read_accessor(gltf, prim.attributes.POSITION)
            nrm    = read_accessor(gltf, prim.attributes.NORMAL)
            if prim.attributes.TEXCOORD_0 is not None:
                uv = read_accessor(gltf, prim.attributes.TEXCOORD_0)
            else:
                uv = np.zeros((pos.shape[0], 2), dtype='f4')
            idxs = read_accessor(gltf, prim.indices).astype('i4').ravel()

            joints  = None
            weights = None
            if prim.attributes.JOINTS_0 is not None:
                joints = read_accessor(gltf, prim.attributes.JOINTS_0).astype('u2').reshape(-1,4)
            if prim.attributes.WEIGHTS_0 is not None:
                weights = read_accessor(gltf, prim.attributes.WEIGHTS_0).astype('f4').reshape(-1,4)

            key = f"{mesh_name}_prim{pi}"
            ma = MeshAsset(
                name     = key,
                vertices = pos.astype('f4').reshape(-1,3),
                normals  = nrm.astype('f4').reshape(-1,3),
                indices  = idxs,
                uvs      = uv.astype('f4').reshape(-1,2),
                joints   = joints,
                weights  = weights,
            )
            MeshRegistry.register(ma)

    # skins/nodes/animations handled elsewhere
    return path

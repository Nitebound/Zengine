import numpy as np
from zengine.assets.mesh_asset import MeshAsset

class MeshFactory:
    @staticmethod
    def rectangle(name: str, width=1.0, height=1.0) -> MeshAsset:
        w, h = width / 2, height / 2
        verts = np.array([
            [-w, -h, 0], [w, -h, 0], [w, h, 0], [-w, h, 0]
        ], dtype='f4')
        norms = np.array([
            [0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]
        ], dtype='f4')
        uvs = np.array([
            [0, 0], [1, 0], [1, 1], [0, 1]
        ], dtype='f4')
        idxs = np.array([0, 1, 2, 2, 3, 0], dtype='i4')
        return MeshAsset(name, verts, norms, idxs, uvs)

    @staticmethod
    def cube(name: str, size=1.0) -> MeshAsset:
        s = size / 2
        corners = [(-s,-s,-s),( s,-s,-s),( s, s,-s),(-s, s,-s),
                   (-s,-s, s),( s,-s, s),( s, s, s),(-s, s, s)]
        faces = [
            ([0,1,2,3], ( 0,  0,-1)),
            ([4,5,6,7], ( 0,  0, 1)),
            ([0,4,7,3], (-1,  0, 0)),
            ([1,5,6,2], ( 1,  0, 0)),
            ([3,2,6,7], ( 0,  1, 0)),
            ([0,1,5,4], ( 0, -1, 0)),
        ]
        verts, norms, idxs, uvs = [], [], [], []
        face_uvs = [(0,0),(1,0),(1,1),(0,1)]
        for quad, n in faces:
            base = len(verts)
            for i, corner in enumerate(quad):
                verts.append(corners[corner])
                norms.append(n)
                uvs.append(face_uvs[i])
            idxs += [base, base+1, base+2, base, base+2, base+3]
        return MeshAsset(
            name,
            np.array(verts, 'f4'),
            np.array(norms, 'f4'),
            np.array(idxs, 'i4'),
            np.array(uvs, 'f4')
        )

    @staticmethod
    def sphere(name: str, radius=1.0, subdivisions=16) -> MeshAsset:
        verts, norms, uvs, idxs = [], [], [], []
        for i in range(subdivisions + 1):
            lat = np.pi * i / subdivisions
            sin_t, cos_t = np.sin(lat), np.cos(lat)
            for j in range(subdivisions + 1):
                lon = 2 * np.pi * j / subdivisions
                x = radius * sin_t * np.cos(lon)
                y = radius * cos_t
                z = radius * sin_t * np.sin(lon)
                verts.append((x, y, z))
                norm = np.array((x, y, z), dtype='f4')
                norms.append(norm / np.linalg.norm(norm))
                uvs.append((j / subdivisions, i / subdivisions))
        rings = subdivisions + 1
        for i in range(subdivisions):
            for j in range(subdivisions):
                a = i * rings + j
                b = a + rings
                idxs += [a, b, a + 1, a + 1, b, b + 1]
        return MeshAsset(
            name,
            np.array(verts, 'f4'),
            np.array(norms, 'f4'),
            np.array(idxs, 'i4'),
            np.array(uvs, 'f4')
        )

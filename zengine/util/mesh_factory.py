import numpy as np
from zengine.assets.mesh_asset import MeshAsset

class MeshFactory:
    @staticmethod
    def cube(name: str, size=1.0) -> MeshAsset:
        s = size / 2
        corners = [(-s, -s, -s), ( s, -s, -s), ( s,  s, -s), (-s,  s, -s),
                   (-s, -s,  s), ( s, -s,  s), ( s,  s,  s), (-s,  s,  s)]
        faces = [
            ([0, 1, 2, 3], ( 0,  0, -1), (1, 0, 0)),  # Front
            ([4, 5, 6, 7], ( 0,  0,  1), (-1, 0, 0)), # Back
            ([0, 4, 7, 3], (-1,  0,  0), (0, 0, -1)), # Left
            ([1, 5, 6, 2], ( 1,  0,  0), (0, 0,  1)), # Right
            ([3, 2, 6, 7], ( 0,  1,  0), (1, 0, 0)),  # Top
            ([0, 1, 5, 4], ( 0, -1,  0), (1, 0, 0)),  # Bottom
        ]

        verts, norms, tangents, uvs, idxs = [], [], [], [], []
        face_uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]

        for quad, normal, tangent in faces:
            base = len(verts)
            for i, corner in enumerate(quad):
                verts.append(corners[corner])
                norms.append(normal)
                tangents.append(tangent)
                uvs.append(face_uvs[i])
            idxs += [base, base+1, base+2, base, base+2, base+3]

        return MeshAsset(
            name=name,
            vertices=np.array(verts, 'f4'),
            normals=np.array(norms, 'f4'),
            indices=np.array(idxs, 'i4'),
            uvs=np.array(uvs, 'f4'),
            tangents=np.array(tangents, 'f4')
        )

    @staticmethod
    def sphere(name: str, radius=1.0, subdivisions=16) -> MeshAsset:
        verts, norms, uvs, tangents, idxs = [], [], [], [], []
        for i in range(subdivisions + 1):
            lat = np.pi * i / subdivisions
            sin_t, cos_t = np.sin(lat), np.cos(lat)
            for j in range(subdivisions + 1):
                lon = 2 * np.pi * j / subdivisions
                sin_p, cos_p = np.sin(lon), np.cos(lon)

                x = radius * sin_t * cos_p
                y = radius * cos_t
                z = radius * sin_t * sin_p
                pos = np.array((x, y, z), dtype='f4')

                verts.append(pos)
                norm = pos / np.linalg.norm(pos)
                norms.append(norm)
                uvs.append((j / subdivisions, i / subdivisions))

                # Basic tangent approximation
                tangent = np.cross((0.0, 1.0, 0.0), norm)
                if np.linalg.norm(tangent) < 1e-5:
                    tangent = np.cross((1.0, 0.0, 0.0), norm)
                tangent /= np.linalg.norm(tangent)
                tangents.append(tangent)

        rings = subdivisions + 1
        for i in range(subdivisions):
            for j in range(subdivisions):
                a = i * rings + j
                b = a + rings
                idxs += [a, b, a+1, a+1, b, b+1]

        return MeshAsset(
            name=name,
            vertices=np.array(verts, 'f4'),
            normals=np.array(norms, 'f4'),
            indices=np.array(idxs, 'i4'),
            uvs=np.array(uvs, 'f4'),
            tangents=np.array(tangents, 'f4')
        )

    @staticmethod
    def plane(name: str, width=1.0, height=1.0) -> MeshAsset:
        w, h = width / 2, height / 2
        verts = [(-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0),
                 (-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0)]
        norms = [(0, 0, 1)] * 4 + [(0, 0, -1)] * 4
        tangents = [(1, 0, 0)] * 4 + [(-1, 0, 0)] * 4
        uvs = [(0, 0), (1, 0), (1, 1), (0, 1)] * 2
        idxs = [0, 1, 2, 2, 3, 0, 4, 6, 5, 6, 4, 7]

        return MeshAsset(
            name=name,
            vertices=np.array(verts, 'f4'),
            normals=np.array(norms, 'f4'),
            indices=np.array(idxs, 'i4'),
            uvs=np.array(uvs, 'f4'),
            tangents=np.array(tangents, 'f4')
        )

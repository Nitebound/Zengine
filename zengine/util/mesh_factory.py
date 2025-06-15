# zengine/util/mesh_factory.py

import numpy
from zengine.assets.mesh_asset import MeshAsset

class MeshFactory:
    @staticmethod
    def rectangle(name: str, width=1.0, height=1.0) -> MeshAsset:
        w,h = width/2, height/2
        verts = numpy.array([[-w, -h, 0], [w, -h, 0], [w, h, 0], [-w, h, 0]], dtype='f4')
        norms = numpy.tile((0, 0, 1), (4, 1)).astype('f4')
        idxs  = numpy.array([0, 1, 2, 2, 3, 0], dtype='i4')
        uvs   = numpy.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype='f4')
        return MeshAsset(name, verts, norms, idxs, uvs)

    @staticmethod
    def cube(name: str, size=1.0) -> MeshAsset:
        s = size/2
        corners = [(-s,-s,-s),( s,-s,-s),( s, s,-s),(-s, s,-s),
                   (-s,-s, s),( s,-s, s),( s, s, s),(-s, s, s)]
        faces = [
          ([0,1,2,3], ( 0,  0,-1)),
          ([4,5,6,7], ( 0,  0, 1)),
          ([0,4,7,3], (-1,  0, 0)),
          ([1,5,6,2], ( 1,  0, 0)),
          ([3,2,6,7], ( 0,  1, 0)),
          ([0,1,5,4], ( 0,-1, 0)),
        ]
        verts, norms, idxs, uvs = [], [], [], []
        # simple per-face planar UVs [0,0]->[1,1]
        face_uvs = [(0,0),(1,0),(1,1),(0,1)]
        for quad, n in faces:
            base = len(verts)
            for i, corner in enumerate(quad):
                verts.append(corners[corner])
                norms.append(n)
                uvs.append(face_uvs[i])
            idxs += [base,base+1,base+2, base,base+2,base+3]
        return MeshAsset(name,
                         numpy.array(verts, 'f4'),
                         numpy.array(norms, 'f4'),
                         numpy.array(idxs, 'i4'),
                         numpy.array(uvs, 'f4'))

    @staticmethod
    def sphere(name: str, radius=1.0, subdivisions=16) -> MeshAsset:
        verts, norms, uvs, idxs = [], [], [], []
        for i in range(subdivisions + 1):
            lat = numpy.pi * i / subdivisions
            sin_t, cos_t = numpy.sin(lat), numpy.cos(lat)
            for j in range(subdivisions + 1):
                lon = 2 * numpy.pi * j / subdivisions
                x = radius * sin_t * numpy.cos(lon)
                y = radius * cos_t
                z = radius * sin_t * numpy.sin(lon)
                verts.append((x, y, z))
                n = numpy.array((x, y, z), dtype='f4')
                norms.append(n / numpy.linalg.norm(n))
                uvs.append((j / subdivisions, i / subdivisions))  # 👈 Add UVs here
        rings = subdivisions + 1
        for i in range(subdivisions):
            for j in range(subdivisions):
                a = i * rings + j
                b = a + rings
                idxs += [a, b, a + 1, a + 1, b, b + 1]
        return MeshAsset(name,
                         numpy.array(verts, dtype='f4'),
                         numpy.array(norms, dtype='f4'),
                         numpy.array(idxs, dtype='i4'),
                         numpy.array(uvs, dtype='f4'))  # 👈 Make sure UVs are returned


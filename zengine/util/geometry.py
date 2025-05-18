# zengine/util/geometry.py

import numpy as np

def rectangle(width, height):
    w, h = width/2, height/2
    verts = np.array([
        [-w, -h, 0.0],
        [ w, -h, 0.0],
        [ w,  h, 0.0],
        [-w,  h, 0.0],
    ], dtype='f4')
    idxs = np.array([0,1,2, 2,3,0], dtype='i4')
    return verts, idxs

def triangle(width, height):
    w, h = width/2, height/2
    verts = np.array([
        [  0,  h, 0.0],
        [-w, -h, 0.0],
        [ w, -h, 0.0],
    ], dtype='f4')
    idxs = np.array([0,1,2], dtype='i4')
    return verts, idxs

def circle(radius, segments):
    verts = [(0.0,0.0,0.0)]
    for i in range(segments):
        a = 2*np.pi*i/segments
        verts.append((radius*np.cos(a), radius*np.sin(a), 0.0))
    verts = np.array(verts, dtype='f4')
    idxs = []
    for i in range(1, segments):
        idxs += [0, i, i+1]
    idxs += [0, segments, 1]
    return verts, np.array(idxs, dtype='i4')

# zengine/util/geometry.py

import numpy as np

def polygon(points):
    """
    points: list of (x,y) tuples in 2D
    returns: (vertices Nx3, indices M)
    """
    pts2d = np.array(points, dtype='f4')            # shape (N,2)
    # lift to 3D
    pts3d = np.column_stack([pts2d, np.zeros(len(pts2d), dtype='f4')])  # (N,3)

    # compute center in 3D
    center3d = np.array([pts2d[:,0].mean(),
                         pts2d[:,1].mean(),
                         0.0], dtype='f4')       # (3,)

    # build vertex list: center first, then perimeter
    verts = np.vstack([center3d[np.newaxis, :], pts3d])  # (N+1,3)

    # fan-triangulate around center
    idxs = []
    count = len(points)
    for i in range(1, count):
        idxs += [0, i, i+1]
    # close the fan
    idxs += [0, count, 1]

    return verts, np.array(idxs, dtype='i4')

def cube(size):
    """
    Returns: (vertices Nx3, normals Nx3, indices M)
    """
    s = size / 2
    # 8 unique corners
    corners = [
        (-s,-s,-s),( s,-s,-s),( s, s,-s),(-s, s,-s),
        (-s,-s, s),( s,-s, s),( s, s, s),(-s, s, s),
    ]
    # faces as quads + normals
    faces = [
        ([0,1,2,3], ( 0,  0, -1)),  # back
        ([4,5,6,7], ( 0,  0,  1)),  # front
        ([0,4,7,3], (-1,  0,  0)),  # left
        ([1,5,6,2], ( 1,  0,  0)),  # right
        ([3,2,6,7], ( 0,  1,  0)),  # top
        ([0,1,5,4], ( 0, -1,  0)),  # bottom
    ]

    verts, norms, idxs = [], [], []
    for quad, n in faces:
        start = len(verts)
        for i in quad:
            verts.append(corners[i])
            norms.append(n)
        # two tris per quad
        idxs += [start, start+1, start+2,  start, start+2, start+3]

    return (np.array(verts, dtype='f4'),
            np.array(norms, dtype='f4'),
            np.array(idxs, dtype='i4'))


def sphere(radius, subdivisions):
    """
    Returns a latitude/longitude sphere.
    """
    verts, norms, idxs = [], [], []
    for i in range(subdivisions+1):
        theta = np.pi * i / subdivisions
        sin_t, cos_t = np.sin(theta), np.cos(theta)
        for j in range(subdivisions+1):
            phi = 2*np.pi * j / subdivisions
            sin_p, cos_p = np.sin(phi), np.cos(phi)
            x = radius * sin_t * cos_p
            y = radius * cos_t
            z = radius * sin_t * sin_p
            verts.append((x,y,z))
            # normal is just position normalized
            n = np.array((x,y,z), dtype='f4')
            norms.append(n / np.linalg.norm(n))
    rings = subdivisions+1
    for i in range(subdivisions):
        for j in range(subdivisions):
            a = i*rings + j
            b = a + rings
            idxs += [a, b, a+1,  a+1, b, b+1]

    return (np.array(verts, dtype='f4'),
            np.array(norms, dtype='f4'),
            np.array(idxs, dtype='i4'))
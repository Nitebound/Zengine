# tests/race2d/race_track_test.py
# Race track ribbon on the XY plane via Centripetal Catmull–Rom.
# Uses ONE interleaved VBO (3f pos, 3f nrm, 2f uv, 4f tangent) to match RenderSystem VAO expectations.

from __future__ import annotations
from typing import List, Tuple, Optional, Dict
import numpy as np

from zengine.assets.mesh_asset import MeshAsset
from zengine.core.engine import Engine
from zengine.core.scene import Scene
from zengine.ecs.components import Transform, MeshFilter, MeshRenderer, Material
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.light import LightComponent, LightType
from zengine.ecs.systems.free_roam_camera_controller_system import FreeRoamCameraControllerSystem
from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.camera_system import CameraSystem
from zengine.ecs.systems.render_system import RenderSystem

Vec2 = Tuple[float, float]


# ---------- Centripetal Catmull–Rom (robust geometric form) ----------
def _tj(ti: float, pi: np.ndarray, pj: np.ndarray, alpha: float) -> float:
    d = np.linalg.norm(pj - pi)
    if d < 1e-8:
        d = 1e-8
    return ti + (d ** alpha)

def _cr_point_segment(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray,
                      s: float, t0: float, t1: float, t2: float, t3: float) -> np.ndarray:
    def lerp(pa, pb, ta, tb):
        if abs(tb - ta) < 1e-8:
            return pa
        a = (tb - s) / (tb - ta)
        b = (s - ta) / (tb - ta)
        return a * pa + b * pb

    A1 = lerp(p0, p1, t0, t1)
    A2 = lerp(p1, p2, t1, t2)
    A3 = lerp(p2, p3, t2, t3)
    B1 = lerp(A1, A2, t0, t2)
    B2 = lerp(A2, A3, t1, t3)
    return lerp(B1, B2, t1, t2)

def sample_catmull_rom_centripetal(points: List[Vec2],
                                   samples_per_segment: int = 48,
                                   loop: bool = True,
                                   alpha: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns (positions Nx2, arclen Nx1). Tangents are finite-differenced later.
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 guide points")

    P = np.asarray(points, dtype=np.float32)
    n = len(P)
    def idx(i: int) -> int:
        return (i % n) if loop else max(0, min(n - 1, i))

    positions: List[np.ndarray] = []
    seg_count = n if loop else (n - 1)
    for i in range(seg_count):
        p0, p1, p2, p3 = P[idx(i - 1)], P[idx(i)], P[idx(i + 1)], P[idx(i + 2)]
        t0 = 0.0
        t1 = _tj(t0, p0, p1, alpha)
        t2 = _tj(t1, p1, p2, alpha)
        t3 = _tj(t2, p2, p3, alpha)
        steps = samples_per_segment + (0 if (loop or i < seg_count - 1) else 1)
        for k in range(steps):
            u = k / samples_per_segment
            s = t1 + u * (t2 - t1)
            positions.append(_cr_point_segment(p0, p1, p2, p3, s, t0, t1, t2, t3))

    P2 = np.asarray(positions, dtype=np.float32)
    diffs = P2[1:] - P2[:-1]
    seg_lens = np.linalg.norm(diffs, axis=1)
    L = np.zeros((P2.shape[0],), dtype=np.float32)
    if seg_lens.size:
        L[1:] = np.cumsum(seg_lens)
    return P2, L

def compute_tangents(P2: np.ndarray, loop: bool) -> np.ndarray:
    n = len(P2)
    T = np.zeros_like(P2)
    for i in range(n):
        j = (i + 1) % n if loop else min(i + 1, n - 1)
        prev = (i - 1 + n) % n if loop else max(i - 1, 0)
        v = P2[j] - P2[prev]
        ln = np.linalg.norm(v)
        if ln < 1e-8:
            v = np.array([1.0, 0.0], dtype=np.float32)
            ln = 1.0
        T[i] = v / ln
    return T


# ---------- Ribbon mesh on XY plane (+Z normal), interleaved buffer ----------
def build_track_mesh_from_points(
    guide_points: List[Vec2],
    width: float = 2.0,
    loop: bool = True,
    samples_per_segment: int = 48,
    uv_per_meter: float = 0.35,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns:
        interleaved (N*2, 3+3+2+4) float32 array: [pos(3), nrm(3), uv(2), tan(4)]
        indices (M,) int32 for GL_TRIANGLES
        layout tuple used by VAO binding.
    """
    P, L = sample_catmull_rom_centripetal(guide_points, samples_per_segment, loop, alpha=0.5)
    T2 = compute_tangents(P, loop=loop)

    n = P.shape[0]
    if n < 2:
        raise ValueError("Not enough samples to build a strip")

    # 2D left normal = rotate T by +90° → (-ty, tx)
    N2 = np.stack([-T2[:, 1], T2[:, 0]], axis=1)
    N2 /= np.maximum(np.linalg.norm(N2, axis=1, keepdims=True), 1e-8)

    # Enforce continuity along the curve
    for i in range(1, n):
        if np.dot(N2[i - 1], N2[i]) < 0:
            N2[i] = -N2[i]
    # Also enforce seam continuity for closed loops
    if loop and np.dot(N2[-1], N2[0]) < 0:
        N2 = -N2  # flip whole frame to keep the seam consistent

    half = width * 0.5
    left = P + N2 * half
    right = P - N2 * half

    # Geometry
    pos = np.zeros((n * 2, 3), dtype=np.float32)
    pos[0::2, :2] = left
    pos[1::2, :2] = right

    nrm = np.zeros((n * 2, 3), dtype=np.float32)  # +Z
    nrm[:, 2] = 1.0

    uv = np.zeros((n * 2, 2), dtype=np.float32)
    uv[0::2, 0] = 0.0
    uv[1::2, 0] = 1.0
    uv[0::2, 1] = L * uv_per_meter
    uv[1::2, 1] = L * uv_per_meter

    tan = np.zeros((n * 2, 4), dtype=np.float32)
    tan[0::2, :3] = np.hstack([T2, np.zeros((n, 1), dtype=np.float32)])
    tan[1::2, :3] = np.hstack([T2, np.zeros((n, 1), dtype=np.float32)])
    tan[:, 3] = 1.0

    # Interleave into a single VBO: 3f pos, 3f nrm, 2f uv, 4f tangent
    interleaved = np.concatenate([pos, nrm, uv, tan], axis=1).astype("f4")

    # Tri indices
    quad_count = n if loop else (n - 1)
    inds = []
    for i in range(quad_count):
        i0 = (i * 2) % (n * 2)
        i1 = (i * 2 + 1) % (n * 2)
        i2 = ((i + 1) * 2) % (n * 2)
        i3 = ((i + 1) * 2 + 1) % (n * 2)
        inds.extend([i0, i1, i2,  i1, i3, i2])

    I = np.asarray(inds, dtype=np.int32)

    # Layout descriptor for VAO binding
    layout = ("3f 3f 2f 4f", ("in_position", "in_normal", "in_uv", "in_tangent"))
    return interleaved, I, layout


# ---------- MeshAsset with interleaved VBO ----------
class TrackMeshAsset(MeshAsset):
    def __init__(self, name: str, interleaved: np.ndarray, indices: np.ndarray, layout):
        super().__init__(name, )
        self.name = name
        self._interleaved = interleaved
        self._indices = indices
        self._layout_fmt, self._layout_names = layout

        self.gltf_data = None
        self.skin_asset = None
        self._vao_cache: Dict[int, object] = {}
        self._vbo = None
        self._ibo = None

    def get_vao(self, ctx, prog):
        pid = getattr(prog, "glo", None)
        if pid in self._vao_cache:
            return self._vao_cache[pid]

        if self._vbo is None:
            self._vbo = ctx.buffer(self._interleaved.tobytes())
        if self._ibo is None:
            self._ibo = ctx.buffer(self._indices.astype("i4").tobytes())

        content = [(self._vbo, self._layout_fmt, *self._layout_names)]
        vao = ctx.vertex_array(prog, content, self._ibo)
        self._vao_cache[pid] = vao
        return vao


def create_track_mesh_asset(
    name: str = "RaceTrack",
    width: float = 2.0,
    loop: bool = True,
    samples_per_segment: int = 48,
    uv_per_meter: float = 0.35,
    guide_points: Optional[List[Vec2]] = None,
) -> TrackMeshAsset:
    if guide_points is None:
        guide_points = [
            (-14.0, -6.0), (-8.0, -9.0), (-2.0, -10.0), (6.0, -7.0),
            (12.0, -1.0), (14.0, 6.0), (10.0, 11.0), (3.0, 12.0),
            (-6.0, 10.0), (-12.0, 5.5),
        ]
    interleaved, I, layout = build_track_mesh_from_points(
        guide_points,
        width=width,
        loop=loop,
        samples_per_segment=samples_per_segment,
        uv_per_meter=uv_per_meter,
    )
    return TrackMeshAsset(name, interleaved, I, layout)


# ---------- Demo scene ----------
class RaceTrackDemo(Engine):
    def __init__(self, size=(1200, 800), title="Race Track Demo"):
        super().__init__(size, title)

    def setup(self):
        scene = Scene()

        input_sys = InputSystem()
        scene.add_system(input_sys)
        scene.add_system(CameraSystem())
        scene.add_system(RenderSystem(self.window.ctx, scene))
        scene.add_system(FreeRoamCameraControllerSystem(input_sys))

        # Top-down ortho camera; Z is depth, XY is plane
        cam = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(cam, Transform(x=0.0, y=0.0, z=30.0))
        scene.entity_manager.add_component(
            cam,
            CameraComponent(
                active=True,
                projection=ProjectionType.ORTHOGRAPHIC,
                near=0.1,
                far=500.0,
            ),
        )

        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(x=12.0, y=10.0, z=20.0))
        scene.entity_manager.add_component(
            light,
            LightComponent(type=LightType.POINT, color=(1.0, 1.0, 1.0), intensity=1.0, range=400.0),
        )

        track_mesh = create_track_mesh_asset(
            name="RaceTrack",
            width=2.0,                 # try 1.5..4.0
            loop=True,
            samples_per_segment=48,    # smooth
            uv_per_meter=0.35,
        )

        track = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(track, Transform(z=0.0))
        scene.entity_manager.add_component(track, MeshFilter(track_mesh))
        scene.entity_manager.add_component(
            track,
            Material(
                use_texture=False,
                use_lighting=True,
                albedo=(0.22, 0.22, 0.22, 1.0),
                smoothness=0.11,
                shader=self.default_shader,
            ),
        )
        scene.entity_manager.add_component(track, MeshRenderer(self.default_shader))

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = RaceTrackDemo()
    app.setup()
    app.run()

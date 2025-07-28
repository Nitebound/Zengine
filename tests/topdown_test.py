import math
import numpy

from zengine.assets.mesh_asset import MeshAsset
from zengine.core.engine import Engine
from zengine.core.scene import Scene

from zengine.ecs.components import (
    Transform,
    PlayerController,
    MeshFilter,
    MeshRenderer,
    Material,
)
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.light import LightComponent, LightType
from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.camera_system import CameraSystem
from zengine.ecs.systems.player_controller_system import PlayerControllerSystem
from zengine.ecs.systems.debug_render_system import DebugRenderSystem
from zengine.ecs.systems.render_system import RenderSystem
from zengine.graphics.shader import Shader # Import Shader

from pathlib import Path # Import Path for shader loading


class MyGame(Engine):
    def __init__(self, size, title):
        # CRITICAL FIX: Call super().__init__ to ensure Engine's __init__ runs
        # This is where self.default_shader and self.debug_shader are initialized.
        super().__init__(size, title)


    def setup(self):
        # Vertices (x, y, z) - 4 vertices per face, 6 faces = 24 vertices
        vertices = numpy.array([
            # Front face (+Z)
            [-0.5, -0.5, 0.5],  # 0: Bottom-left-front
            [0.5, -0.5, 0.5],  # 1: Bottom-right-front
            [0.5, 0.5, 0.5],  # 2: Top-right-front
            [-0.5, 0.5, 0.5],  # 3: Top-left-front

            # Back face (-Z)
            [-0.5, -0.5, -0.5],  # 4: Bottom-left-back
            [-0.5, 0.5, -0.5],  # 5: Top-left-back
            [0.5, 0.5, -0.5],  # 6: Top-right-back
            [0.5, -0.5, -0.5],  # 7: Bottom-right-back

            # Right face (+X)
            [0.5, -0.5, -0.5],  # 8: Bottom-right-back
            [0.5, 0.5, -0.5],  # 9: Top-right-back
            [0.5, 0.5, 0.5],  # 10: Top-right-front
            [0.5, -0.5, 0.5],  # 11: Bottom-right-front

            # Left face (-X)
            [-0.5, -0.5, -0.5],  # 12: Bottom-left-back
            [-0.5, -0.5, 0.5],  # 13: Bottom-left-front
            [-0.5, 0.5, 0.5],  # 14: Top-left-front
            [-0.5, 0.5, -0.5],  # 15: Top-left-back

            # Top face (+Y)
            [-0.5, 0.5, -0.5],  # 16: Top-left-back
            [-0.5, 0.5, 0.5],  # 17: Top-left-front
            [0.5, 0.5, 0.5],  # 18: Top-right-front
            [0.5, 0.5, -0.5],  # 19: Top-right-back

            # Bottom face (-Y)
            [-0.5, -0.5, -0.5],  # 20: Bottom-left-back
            [0.5, -0.5, -0.5],  # 21: Bottom-right-back
            [0.5, -0.5, 0.5],  # 22: Bottom-right-front
            [-0.5, -0.5, 0.5]  # 23: Bottom-left-front
        ], dtype=numpy.float32)

        # Normals (one normal per face, applied to all 4 vertices of that face)
        normals = numpy.array([
            # Front face (+Z)
            [0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0],
            # Back face (-Z)
            [0.0, 0.0, -1.0], [0.0, 0.0, -1.0], [0.0, 0.0, -1.0], [0.0, 0.0, -1.0],
            # Right face (+X)
            [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0],
            # Left face (-X)
            [-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0],
            # Top face (+Y)
            [0.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 1.0, 0.0],
            # Bottom face (-Y)
            [0.0, -1.0, 0.0], [0.0, -1.0, 0.0], [0.0, -1.0, 0.0], [0.0, -1.0, 0.0],
        ], dtype=numpy.float32)

        # UVs (standard (0,0), (1,0), (1,1), (0,1) for each face)
        uvs = numpy.array([
            # Front face
            [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
            # Back face (adjusted for typical back face unwrapping)
            [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0],
            # Right face
            [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
            # Left face (adjusted for typical left face unwrapping)
            [1.0, 0.0], [0.0, 0.0], [0.0, 1.0], [1.0, 1.0],
            # Top face
            [0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0],
            # Bottom face
            [1.0, 0.0], [0.0, 0.0], [0.0, 1.0], [1.0, 1.0],
        ], dtype=numpy.float32)

        # Indices (12 triangles, 36 indices in total)
        indices = numpy.array([
            # Front face (vertices 0, 1, 2, 3)
            0, 1, 2, 0, 2, 3,
            # Back face (vertices 4, 5, 6, 7)
            4, 5, 6, 4, 6, 7,
            # Right face (vertices 8, 9, 10, 11)
            8, 9, 10, 8, 10, 11,
            # Left face (vertices 12, 13, 14, 15)
            12, 13, 14, 12, 14, 15,
            # Top face (vertices 16, 17, 18, 19)
            16, 17, 18, 16, 18, 19,
            # Bottom face (vertices 20, 21, 22, 23)
            20, 21, 22, 20, 22, 23,
        ], dtype=numpy.uint32)

        scene = Scene()

        # Create the MeshAsset instance
        mesh = MeshAsset("box", vertices, normals, indices, uvs)

        # --- Create and configure the cube entity ---
        boxid = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(boxid, Transform(x=0.0, y=0.0, z=0.0))
        scene.entity_manager.add_component(boxid, MeshFilter(mesh))

        # Ensure default_shader is not None before assigning
        if self.default_shader:
            scene.entity_manager.add_component(boxid, Material(albedo=(1.0, 1, 1, 1.0), shader=self.default_shader, use_texture=False))
            scene.entity_manager.add_component(boxid, MeshRenderer(shader=self.default_shader))
        else:
            print("WARNING: default_shader not loaded, cube might not render.")


        # — core systems —
        scene.add_system(InputSystem())
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(scene.systems[0]))
        render_sys = RenderSystem(self.window.ctx, scene)
        scene.add_system(render_sys)

        # — debug grid + axes so you can see your origin —
        # DebugRenderSystem now relies on Engine.debug_shader
        if self.debug_shader:
            debug_sys = DebugRenderSystem(self.window.ctx, scene)
            scene.add_system(debug_sys)
            debug_sys.set_enabled("grid", True)
            debug_sys.set_enabled("axes", True)
            debug_sys.set_enabled("bounding_boxes", True)
        else:
            print("WARNING: debug_shader not loaded, debug gizmos will not render.")


        # — camera at (0,0,-5), looking down +Z (identity rotation) —
        # For a top-down view where Z is depth (into screen), camera needs to be at a negative Z
        # and looking towards positive Z.
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0.0, y=0.0, z=1.0)) # Camera is 5 units back
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect=self.window.width / self.window.height,
            near=0.01, far=1000.0,
            fov_deg=60.0,
            projection=ProjectionType.PERSPECTIVE
        ))

        scene.entity_manager.add_component(cam, PlayerController(1, rotation_speed=1))

        # # — simple white point‑light out in front —
        # light = scene.entity_manager.create_entity()
        # scene.entity_manager.add_component(light, Transform(x=0.0, y=1.0, z=0.0)) # Light is above the cube
        # scene.entity_manager.add_component(light, LightComponent(
        #     type=LightType.POINT,
        #     color=(1.0, 1.0, 1.0),
        #     intensity=5.0,
        #     range=200.0,
        # ))

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024, 768), title="ZEngine Model Preview")
    app.setup()
    app.run()

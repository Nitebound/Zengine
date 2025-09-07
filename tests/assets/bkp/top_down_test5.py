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
from zengine.ecs.components.free_roam_camera_controller import FreeRoamCameraController
from zengine.ecs.systems.free_roam_camera_controller_system import FreeRoamCameraControllerSystem
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.light import LightComponent, LightType
from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.camera_system import CameraSystem
from zengine.ecs.systems.debug_render_system import DebugRenderSystem
from zengine.ecs.systems.render_system import RenderSystem
from zengine.assets.loaders.gltf_loader import load_gltf_model

from zengine.graphics.texture_loader import load_texture_2d
from zengine.ecs.systems.free_roam_camera_controller_system import FreeRoamCameraControllerSystem

class TopDownTest(Engine):
    def __init__(self, size, title):
        # This is where self.default_shader and self.debug_shader are initialized.
        super().__init__(size, title)

    def setup(self):
        # Vertices (x, y, z) - 4 vertices per face, 6 faces = 24 vertices

        cube_size = .1
        vertices = numpy.array([
            # Front face (+Z)
            [-cube_size, -cube_size, cube_size],  # 0: Bottom-left-front
            [cube_size, -cube_size, cube_size],  # 1: Bottom-right-front
            [cube_size, cube_size, cube_size],  # 2: Top-right-front
            [-cube_size, cube_size, cube_size],  # 3: Top-left-front

            # # Back face (-Z)
            # [-cube_size, -cube_size, -cube_size],  # 4: Bottom-left-back
            # [-cube_size, cube_size, -cube_size],  # 5: Top-left-back
            # [cube_size, cube_size, -cube_size],  # 6: Top-right-back
            # [cube_size, -cube_size, -cube_size],  # 7: Bottom-right-back
            #
            # # Right face (+X)
            # [cube_size, -cube_size, -cube_size],  # 8: Bottom-right-back
            # [cube_size, cube_size, -cube_size],  # 9: Top-right-back
            # [cube_size, cube_size, cube_size],  # 10: Top-right-front
            # [cube_size, -cube_size, cube_size],  # 11: Bottom-right-front
            #
            # # Left face (-X)
            # [-cube_size, -cube_size, -cube_size],  # 12: Bottom-left-back
            # [-cube_size, -cube_size, cube_size],  # 13: Bottom-left-front
            # [-cube_size, cube_size, cube_size],  # 14: Top-left-front
            # [-cube_size, cube_size, -cube_size],  # 15: Top-left-back
            #
            # # Top face (+Y)
            # [-cube_size, cube_size, -cube_size],  # 16: Top-left-back
            # [-cube_size, cube_size, cube_size],  # 17: Top-left-front
            # [cube_size, cube_size, cube_size],  # 18: Top-right-front
            # [cube_size, cube_size, -cube_size],  # 19: Top-right-back
            #
            # # Bottom face (-Y)
            # [-cube_size, -cube_size, -cube_size],  # 20: Bottom-left-back
            # [cube_size, -cube_size, -cube_size],  # 21: Bottom-right-back
            # [cube_size, -cube_size, cube_size],  # 22: Bottom-right-front
            # [-cube_size, -cube_size, cube_size]  # 23: Bottom-left-front
        ], dtype=numpy.float32)

        # Normals (one normal per face, applied to all 4 vertices of that face)
        normals = numpy.array([
            # Front face (+Z)
            [0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0],
            # # Back face (-Z)
            # [0.0, 0.0, -1.0], [0.0, 0.0, -1.0], [0.0, 0.0, -1.0], [0.0, 0.0, -1.0],
            # # Right face (+X)
            # [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0],
            # # Left face (-X)
            # [-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0],
            # # Top face (+Y)
            # [0.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 1.0, 0.0],
            # # Bottom face (-Y)
            # [0.0, -1.0, 0.0], [0.0, -1.0, 0.0], [0.0, -1.0, 0.0], [0.0, -1.0, 0.0],
        ], dtype=numpy.float32)

        # UVs (standard (0,0), (1,0), (1,1), (0,1) for each face)
        uvs = numpy.array([
            # Front face
            [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
            # # Back face (adjusted for typical back face unwrapping)
            # [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0],
            # # Right face
            # [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
            # # Left face (adjusted for typical left face unwrapping)
            # [1.0, 0.0], [0.0, 0.0], [0.0, 1.0], [1.0, 1.0],
            # # Top face
            # [0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0],
            # # Bottom face
            # [1.0, 0.0], [0.0, 0.0], [0.0, 1.0], [1.0, 1.0],
        ], dtype=numpy.float32)

        # Indices (12 triangles, 36 indices in total)
        indices = numpy.array([
            # Front face (vertices 0, 1, 2, 3)
            0, 1, 2, 0, 2, 3,
            # # Back face (vertices 4, 5, 6, 7)
            # 4, 5, 6, 4, 6, 7,
            # # Right face (vertices 8, 9, 10, 11)
            # 8, 9, 10, 8, 10, 11,
            # # Left face (vertices 12, 13, 14, 15)
            # 12, 13, 14, 12, 14, 15,
            # # Top face (vertices 16, 17, 18, 19)
            # 16, 17, 18, 16, 18, 19,
            # # Bottom face (vertices 20, 21, 22, 23)
            # 20, 21, 22, 20, 22, 23,
        ], dtype=numpy.uint32)

        scene = Scene()
        # mesh_texture = load_texture_2d(self.window.ctx, "./assets/images/166.JPG")
        # mesh_normal = load_texture_2d(self.window.ctx, "./assets/images/166_norm.JPG")
        input_sys = scene.get_system(InputSystem)

        # Create the MeshAsset instance
        mesh = MeshAsset("plane", vertices, normals, indices, uvs)
        models = load_gltf_model(self.window.ctx, "assets/models/RiggedFigure.gltf", self.default_shader)

        for mesh, mat, skin in models:
            eid = scene.entity_manager.create_entity()
            scene.entity_manager.add_component(eid, Transform(x=0.0, y=0.0, z=0.0))
            scene.entity_manager.add_component(eid, MeshFilter(mesh))
            scene.entity_manager.add_component(eid, mat)
            scene.entity_manager.add_component(eid, MeshRenderer(shader=self.default_shader))
            scene.entity_manager.add_component(eid, PlayerController(1, rotation_speed=1))
            
        # — core systems —
        scene.add_system(InputSystem())
        scene.add_system(CameraSystem())
        scene.add_system(FreeRoamCameraControllerSystem(input_sys))
        render_sys = RenderSystem(self.window.ctx, scene)
        scene.add_system(render_sys)



        # DebugRenderSystem now relies on Engine.debug_shader
        debug_sys = DebugRenderSystem(self.window.ctx, scene)
        scene.add_system(debug_sys)
        debug_sys.set_enabled("grid", True)
        debug_sys.set_enabled("axes", True)
        debug_sys.set_enabled("bounding_boxes", True)


        # Main Camera
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0.0, y=0.0, z=4.0))
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect=self.window.width / self.window.height,
            near=0.01, far=1000.0,
            fov_deg=60.0,
            projection=ProjectionType.PERSPECTIVE
        ))

        scene.entity_manager.add_component(cam, FreeRoamCameraController(11, 1))

        # Create a point light in the scene
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(x=0.0, y=0.0, z=10.0))
        scene.entity_manager.add_component(light, LightComponent(
            type=LightType.POINT,
            color=(1.0, 1.0, 1.0),
            intensity=20.0,
            range=400.0,
        ))

        #scene.entity_manager.add_component(light, PlayerController(11, rotation_speed=1))

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = TopDownTest(size=(1024, 768), title="ZEngine Model Preview")
    app.setup()
    app.run()

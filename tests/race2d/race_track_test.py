import numpy

from zengine.assets.mesh_asset import MeshAsset
from zengine.core.engine import Engine
from zengine.core.scene import Scene
from zengine.ecs.components.physics.rigid_body_2d import RigidBody2D
from zengine.ecs.systems.physics_system_2d import PhysicsSystem2D
from zengine.ecs.systems.player_controller_system import PlayerControllerSystem
from zengine.ecs.systems.top_down_car_controller_system import TopDownCarControllerSystem
from zengine.util.mesh_factory import MeshFactory
from zengine.ecs.components import (
    Transform,
    PlayerController,
    MeshFilter,
    MeshRenderer,
    Material,
    TopDownCarController
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
        scene = Scene()
        mesh_texture = load_texture_2d(self.window.ctx, "../assets/images/mech1 (Copy).png")
        # mesh_normal = load_texture_2d(self.window.ctx, "./assets/images/159_norm.JPG")
        input_sys = scene.get_system(InputSystem)

        mesh = MeshFactory.plane("MechMesh", 1,1)
        mat = Material(shader=self.default_shader, albedo_texture=mesh_texture)

        # — core systems —
        scene.add_system(InputSystem())
        scene.add_system(CameraSystem())
        scene.add_system(FreeRoamCameraControllerSystem(input_sys))
        scene.add_system(TopDownCarControllerSystem(input_sys))
        scene.add_system(PhysicsSystem2D(self.window.ctx, scene))

        render_sys = RenderSystem(self.window.ctx, scene)
        # debug_sys = DebugRenderSystem(self.window.ctx, scene)

        scene.add_system(render_sys)
        # scene.add_system(debug_sys)

        eid = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(eid, Transform(x=0,y=0, z=1))
        scene.entity_manager.add_component(eid, MeshFilter(mesh))
        scene.entity_manager.add_component(eid, mat)
        scene.entity_manager.add_component(eid, MeshRenderer(shader=self.default_shader, texture=mesh_texture))
        scene.entity_manager.add_component(eid, TopDownCarController(11, 11))
        scene.entity_manager.add_component(eid, RigidBody2D(1, [0,0,0], [0,0,0]))

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
            intensity=.50,
            range=400.0,
        ))

        # Generate mesh of a given track represented as continuous curves.

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = TopDownTest(size=(1024, 768), title="Race2D")
    app.setup()
    app.run()

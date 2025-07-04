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
from zengine.ecs.systems.render_system import RenderSystem
from zengine.ecs.systems.light_system import LightSystem

from zengine.assets.default_meshes import MeshFactory
from zengine.graphics.texture_loader import load_texture_2d


class WorldTest(Engine):
    def setup(self):
        scene = Scene()

        # 🧠 Core ECS Systems
        input_sys = InputSystem()
        scene.add_system(input_sys)
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(input_sys))
        scene.add_system(LightSystem(scene))
        scene.add_system(RenderSystem(self.window.ctx, scene))

        # 🎥 Camera
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0, y=0, z=4))
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect=self.window.width / self.window.height,
            near=0.001,
            far=100.0,
            fov_deg=60.0,
            projection=ProjectionType.PERSPECTIVE
        ))

        # 🖼 Load Texture
        tex = load_texture_2d(self.window.ctx, "assets/images/mech1.png")

        # 🧱 Sphere Mesh with Material
        eid = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(eid, Transform(0, 0, 0))
        scene.entity_manager.add_component(eid, MeshFilter(
            asset=MeshFactory.sphere("sphere", 1, 5)
        ))

        mat = Material(
            shader=self.default_shader,
            albedo=(1.0, 1.0, 1.0, 1.0),
            main_texture=tex,
            use_texture=True,
            use_lighting=True,
            emission_color=(0.0, 0.0, 0.0, 1.0),
            emission_intensity=0.0,
            custom_uniforms={
                "u_ambient_color": (0.2, 0.2, 0.2)
            }
        )

        scene.entity_manager.add_component(eid, mat)
        scene.entity_manager.add_component(eid, MeshRenderer(shader=self.default_shader))
        scene.entity_manager.add_component(eid, PlayerController(1, rotation_speed=8))

        # 💡 Bright White Point Light
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(0, 1, 1))
        scene.entity_manager.add_component(light, LightComponent(
            type=LightType.POINT,
            color=(1.0, 1.0, 1.0),  # white light
            intensity=10.0  # reasonable brightness
        ))

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = WorldTest(size=(1024, 768), title="ZEngine Lighting Test")
    app.setup()
    app.run()

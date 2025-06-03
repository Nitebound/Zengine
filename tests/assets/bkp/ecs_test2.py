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

from zengine.assets.default_meshes import MeshFactory
from zengine.graphics.texture_loader import load_texture_2d


class MyGame(Engine):
    def setup(self):
        scene = Scene()

        # 1) Core Systems
        input_sys = InputSystem()
        scene.add_system(input_sys)
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(input_sys))
        scene.add_system(RenderSystem(self.window.ctx, scene))

        # 2) Camera at z=10, looking toward -Z
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0, y=0, z=0))
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect=self.window.width / self.window.height,
            near=0.001,
            far=5000.0,
            fov_deg=70.0,
            projection=ProjectionType.PERSPECTIVE
        ))

        # 3) Create Renderable Cube at origin (visible at z=0)
        being = scene.entity_manager.create_entity()

        # 🟢 Origin is fine now
        scene.entity_manager.add_component(being, Transform(x=0, y=0, z=-11))

        # ✅ Smaller cube for visibility
        scene.entity_manager.add_component(being, MeshFilter(MeshFactory.cube("cube", 0.10)))
        scene.entity_manager.add_component(being, PlayerController(10))
        # 🎨 Pure color — no texture
        mat = Material(
            shader=self.default_shader,
            textures={},  # none needed
            extra_uniforms={
                'useTexture': False,
                'useLighting': False,
                'baseColor': (1.0, 0.0, 1.0, 1.0),  # Bright magenta
            }
        )

        scene.entity_manager.add_component(being, mat)
        scene.entity_manager.add_component(being, MeshRenderer(shader=self.default_shader))

        # 4) Light (optional)
        # light = scene.entity_manager.create_entity()
        # scene.entity_manager.add_component(light, Transform(x=0, y=10, z=10))
        # scene.entity_manager.add_component(light, LightComponent(
        #     type=LightType.POINT,
        #     color=(1.0, 1.0, 1.0),
        #     intensity=0.0
        # ))

        # 5) Launch
        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024, 768), title="ZEngine")
    app.setup()
    app.run()

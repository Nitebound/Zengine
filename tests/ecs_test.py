# tests/ecs_test.py

from zengine.core.engine import Engine
from zengine.core.scene  import Scene

# Components
from zengine.ecs.components import (
    Transform,
    PlayerController,
    MeshFilter,
    MeshRenderer, Material,
)
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.light  import LightComponent, LightType

# Systems
from zengine.ecs.systems.input_system             import InputSystem
from zengine.ecs.systems.camera_system            import CameraSystem
from zengine.ecs.systems.player_controller_system import PlayerControllerSystem
from zengine.ecs.systems.render_system            import RenderSystem

# Helpers
from zengine.assets.default_meshes import MeshFactory
from zengine.graphics.texture_loader import load_texture_2d

import math

class MyGame(Engine):
    def setup(self):
        scene = Scene()

        # 1) Core systems
        input_sys = InputSystem()
        scene.add_system(input_sys)
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(input_sys))
        # scene.add_system(RenderSystem(self.window.ctx, scene))


        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam,
                                           Transform(x=0, y=0, z=0)
                                           )

        scene.entity_manager.add_component(cam,
                                           CameraComponent(
                                               aspect=self.window.width / self.window.height,
                                               projection=ProjectionType.PERSPECTIVE
                                           )
                                           )

        being = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(being,
            Transform(x=0, y=0, z=100)
        )

        quad = MeshFactory.cube("cube", 1.0)
        print(quad)
        scene.entity_manager.add_component(being, MeshFilter(quad))
        scene.entity_manager.add_component(being, MeshRenderer(self.default_shader))

        tex = load_texture_2d(self.window.ctx, "assets/images/img.png")
        mat = Material(
            shader=self.default_shader,
            textures={'albedo': tex},  # use the texture we loaded
            # toggle the flags:
            extra_uniforms={
                'useTexture': True,
                'useLighting': False,  # sprites often don’t need lighting
                'baseColor': (1.0, 0.0, 5.0, 1.0),  # fallback
                'lightDirection': (1, 1, 1),
                'ambientColor': (.15, 0.1, 0.1, 1)
            }
        )

        scene.entity_manager.add_component(being, mat)

        # (optional) if you still want movement
        scene.entity_manager.add_component(cam,
            PlayerController(speed=5.0, rotation_speed=1.0)
        )

        # 5) Light (so phong/textured shader actually lights it)
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light,
            Transform(x=0, y=10, z=0)
        )
        scene.entity_manager.add_component(light,
            LightComponent(
                type=LightType.POINT,
                color=(1.0, 1.0, 1.0),
                intensity=1.0
            )
        )

        # 6) Kick off
        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024,768), title="ZEngine")
    app.setup()
    app.run()

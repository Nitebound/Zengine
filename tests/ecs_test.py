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


class MyGame(Engine):
    def setup(self):
        scene = Scene()

        # 1) Core systems
        input_sys = InputSystem()
        scene.add_system(input_sys)
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(input_sys))

        # 2) Camera — move it back so it can see the quad at origin
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam,
            Transform(x=0, y=0, z=5)    # ← z=5 so the camera sits 5 units out
        )
        scene.entity_manager.add_component(cam,
            CameraComponent(
                aspect=self.window.width/self.window.height,
                projection=ProjectionType.PERSPECTIVE
            )
        )

        # 3) Unified render system (handles all MeshRenderer components)
        scene.add_system(RenderSystem(self.window.ctx, scene))

        # 4) Your “cube” → rename to sprite_0 and give it a quad + texture
        sprite_0 = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(sprite_0,
            Transform(x=0, y=0, z=0)
        )

        quad = MeshFactory.rectangle("Quad", 1.0, 1.0)
        scene.entity_manager.add_component(sprite_0, MeshFilter(quad))

        tex = load_texture_2d(self.window.ctx, "assets/images/img.png")
        mat = Material(
            shader=self.phong_shader,
            albedo=(1, 1, 1, 1),
            ambient_strength=0.2,
            specular_strength=0.5,
            shininess=32.0,
            textures={'albedoMap': tex},
            extra_uniforms={}  # any extra per-object you need
        )
        scene.entity_manager.add_component(sprite_0, mat)
        # (optional) if you still want movement
        scene.entity_manager.add_component(sprite_0,
            PlayerController(speed=5.0, rotation_speed=1.0)
        )

        # 5) Light (so phong/textured shader actually lights it)
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light,
            Transform(x=5, y=5, z=5)
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

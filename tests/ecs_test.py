import numpy

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
from zengine.ecs.systems.light_system import LightSystem
from zengine.ecs.systems.render_system import RenderSystem

from zengine.assets.default_meshes import MeshFactory
from zengine.graphics.texture_loader import load_texture_2d


class MyGame(Engine):
    def setup(self):
        scene = Scene()

        # ——— core ECS systems ———
        scene.add_system(InputSystem())
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(scene.systems[0]))
        scene.add_system(LightSystem(scene))
        scene.add_system(RenderSystem(self.window.ctx, scene))

        # ——— camera ———
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0, y=0, z=1))
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect=self.window.width / self.window.height,
            near=0.01, far=1000.0,
            fov_deg=60.0,
            projection=ProjectionType.PERSPECTIVE
        ))



        # ——— add a single point-light up above the plane ———
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(0, 0, 0.5))
        scene.entity_manager.add_component(light, LightComponent(
            type=LightType.POINT,
            color=(1.0, 1.0, 1.0),
            intensity=2.0,  # no need to overcrank it
            range=2  # unused, but safe default
        ))

        # ——— load texture & spawn plane ———
        tex = load_texture_2d(self.window.ctx, "assets/images/img.png")
        tex_norm = load_texture_2d(self.window.ctx, "assets/images/img_norm.png")

        eid = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(eid, Transform(0,0,0))
        scene.entity_manager.add_component(eid, MeshFilter(
            MeshFactory.sphere("plane", 2, 90)
        ))

        mat = Material(
            shader=self.default_shader,
            albedo_texture=tex,
            normal_map=tex_norm,
            custom_uniforms={"u_ambient_color": (0.05, 0.05, 0.05)},
        )

        scene.entity_manager.add_component(eid, mat)
        scene.entity_manager.add_component(eid, MeshRenderer(shader=self.default_shader))
        scene.entity_manager.add_component(eid, PlayerController(1, rotation_speed=.8))

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024, 768), title="ZEngine Lighting Test")
    app.setup()
    app.run()

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
from zengine.ecs.systems.render_system import RenderSystem
from zengine.assets.loaders.gltf_loader import load_gltf_model
import math
from zengine.util.quaternion import from_axis_angle


class MyGame(Engine):
    def setup(self):
        scene = Scene()

        models = load_gltf_model(self.window.ctx, "assets/models/human1.glb", self.default_shader)

        for mesh, mat, skin in models:
            eid = scene.entity_manager.create_entity()


            # 90 degrees in radians
            angle_rad = math.radians(90)

            qx, qy, qz, qw = from_axis_angle((-90, 0, 0), angle_rad)

            transform = Transform(0, 0, -3, rotation_x=qx, rotation_y=qy, rotation_z=qz, rotation_w=qw)
            scene.entity_manager.add_component(eid, transform)
            scene.entity_manager.add_component(eid, MeshFilter(mesh))
            scene.entity_manager.add_component(eid, mat)
            scene.entity_manager.add_component(eid, MeshRenderer(shader=self.default_shader))
            scene.entity_manager.add_component(eid, PlayerController(1, rotation_speed=1))

        # ——— core ECS systems ———
        scene.add_system(InputSystem())
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(scene.systems[0]))
        scene.add_system(RenderSystem(self.window.ctx, scene))

        # ——— camera ———
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0, y=0, z=0))
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect=self.window.width / self.window.height,
            near=0.01, far=1000.0,
            fov_deg=60.0,
            projection=ProjectionType.PERSPECTIVE
        ))

        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(0, 0, 0))
        scene.entity_manager.add_component(light, LightComponent(
            type=LightType.POINT,
            color=(1.0, 1.0, 1.0),
            intensity=4.0,
            range=1000
        ))

        img_index = 158
        # img_fname = f"assets/images/{img_index}.JPG"
        # img_norm_fname = f"assets/images/{img_index}_norm.JPG"`

        # # ——— load texture & spawn plane ———
        # tex = load_texture_2d(self.window.ctx, img_fname)
        # tex_norm = load_texture_2d(self.window.ctx, img_norm_fname)

        # player = scene.entity_manager.create_entity()
        # scene.entity_manager.add_component(player, Transform(0,0,-3))
        # scene.entity_manager.add_component(player, MeshFilter(
        #     MeshFactory.sphere("plane", 2, 32)
        # ))
        #
        # mat = Material(
        #     shader=self.default_shader,
        #     albedo_texture=tex,
        #     normal_map=tex_norm,
        #     custom_uniforms={"u_ambient_color": (0.05, 0.05, 0.05)},
        # )
        #
        # scene.entity_manager.add_component(player, mat)
        # scene.entity_manager.add_component(player, MeshRenderer(shader=self.default_shader))
        # scene.entity_manager.add_component(player, PlayerController(1, rotation_speed=.8))

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024, 768), title="ZEngine Lighting Test")
    app.setup()
    app.run()

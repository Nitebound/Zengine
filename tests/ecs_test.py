import math
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
from zengine.ecs.systems.debug_render_system import DebugRenderSystem
from zengine.ecs.systems.render_system import RenderSystem

from zengine.assets.loaders.gltf_loader import load_gltf_model


class MyGame(Engine):
    def setup(self):
        scene = Scene()

        # — load all sub‑meshes/materials from the GLB —
        models = load_gltf_model(self.window.ctx, "assets/models/human1.glb", self.default_shader)

        # — spawn them at origin, no rotation, default scale —
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
        scene.add_system(PlayerControllerSystem(scene.systems[0]))

        # — debug grid + axes so you can see your origin —
        debug_sys = DebugRenderSystem(self.window.ctx, scene)
        scene.add_system(debug_sys)
        debug_sys.set_enabled("grid", True)
        debug_sys.set_enabled("axes", True)

        scene.add_system(RenderSystem(self.window.ctx, scene))

        # — camera at (0,0,5), looking down −Z (identity rotation) —
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0.0, y=0.0, z=5.0))
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect=self.window.width / self.window.height,
            near=0.01, far=1000.0,
            fov_deg=60.0,
            projection=ProjectionType.PERSPECTIVE
        ))

        # — simple white point‑light out in front —
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(x=2.0, y=2.0, z=2.0))
        scene.entity_manager.add_component(light, LightComponent(
            type=LightType.POINT,
            color=(1.0, 1.0, 1.0),
            intensity=2.0,
            range=10.0,
        ))

        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024, 768), title="ZEngine Model Preview")
    app.setup()
    app.run()

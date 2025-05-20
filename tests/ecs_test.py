# tests/ecs_test.py
import math

import moderngl
from zengine.core.engine import Engine
from zengine.core.scene  import Scene

# Components
from zengine.ecs.components      import Transform, PlayerController
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.light  import LightComponent, LightType

# Systems
from zengine.ecs.systems.input_system            import InputSystem
from zengine.ecs.systems.camera_system           import CameraSystem
from zengine.ecs.systems.player_controller_system import PlayerControllerSystem
from zengine.ecs.systems.gltf_import_system      import GLTFImportSystem
from zengine.ecs.systems.animation_system        import AnimationSystem
from zengine.ecs.systems.skinning_system         import SkinningSystem
from zengine.ecs.systems.skinned_mesh_render_system import SkinnedMeshRenderSystem

class MyGame(Engine):
    def setup(self):
        # 0) Scene + raw GL context tweaks
        scene = Scene()
        ctx   = self.window.ctx

        ctx.enable(moderngl.DEPTH_TEST)
        ctx.disable(moderngl.CULL_FACE)

        # 1) Core systems
        input_sys = InputSystem()
        scene.add_system(input_sys)
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(input_sys))

        # 2) Import GLTF first
        scene.add_system(GLTFImportSystem(
            "assets/models/RiggedFigure.gltf",
            ctx,
            self.skinning_shader
        ))

        # 3) Then animation, skinning, and render
        scene.add_system(AnimationSystem())
        scene.add_system(SkinningSystem())
        scene.add_system(SkinnedMeshRenderSystem())

        # 4) Camera setup at (0,0,30)
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam, Transform(x=0.0, y=0.0, z=30.0))
        scene.entity_manager.add_component(cam, CameraComponent(
            aspect     = self.window.width  / self.window.height,
            projection = ProjectionType.PERSPECTIVE
        ))
        scene.entity_manager.add_component(cam, PlayerController())

        # 5) A simple point light
        light = scene.entity_manager.create_entity()
        scene.entity_manager.add_component(light, Transform(x=5.0, y=5.0, z=5.0))
        scene.entity_manager.add_component(light, LightComponent(
            type      = LightType.POINT,
            color     = (1.0, 1.0, 1.0),
            intensity = 1.0
        ))
        # quaternion for -90° around X:
        angle = math.radians(-90.0)
        qx, qw = math.sin(angle / 2), math.cos(angle / 2)

        # apply to every node in the import
        for node_idx, eid in scene.node_map.items():
            tr = scene.entity_manager.get_component(eid, Transform)
            # premultiply (q_root * q_node)
            x2, y2, z2, w2 = tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w
            tr.rotation_x = qw * x2 + qx * w2
            tr.rotation_y = x2 * 0 + y2 * qw + z2 * qx - z2 * 0  # simplify since qy=qz=0
            tr.rotation_z = qw * z2 + qx * y2
            tr.rotation_w = qw * w2 - qx * x2
        # 6) Launch
        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024, 768), title="ZEngine")
    app.setup()
    app.run()

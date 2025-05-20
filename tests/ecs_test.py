# tests/ecs_test.py

from zengine.core.engine import Engine
from zengine.core.scene import Scene

# Components & Systems
from zengine.ecs.components import Transform, PlayerController
from zengine.ecs.components.camera import CameraComponent, ProjectionType
from zengine.ecs.components.light import LightComponent, LightType

from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.camera_system import CameraSystem
from zengine.ecs.systems.player_controller_system import PlayerControllerSystem
from zengine.ecs.systems.gltf_import_system import GLTFImportSystem
from zengine.ecs.systems.animation_system import AnimationSystem
from zengine.ecs.systems.skinning_system import SkinningSystem
from zengine.ecs.systems.skinned_mesh_render_system import SkinnedMeshRenderSystem
from zengine.ecs.components import Transform


class MyGame(Engine):
    def setup(self):
        scene = Scene()

        # 1) Core systems
        input_sys = InputSystem()
        scene.add_system(input_sys)
        scene.add_system(CameraSystem())
        scene.add_system(PlayerControllerSystem(input_sys))

        scene.add_system(AnimationSystem())
        # scene.add_system(SkinningSystem())
        # scene.add_system(SkinnedMeshRenderSystem())

        # 2) GLTF import + skinning pipeline
        scene.add_system(GLTFImportSystem(
            "assets/models/RiggedFigure.gltf",
            self.window.ctx,
            self.skinning_shader
        ))

        # 3) Camera
        cam = scene.entity_manager.create_entity()
        scene.active_camera = cam
        scene.entity_manager.add_component(cam,
                                           Transform(x=0, y=0, z=10)
                                           )

        scene.entity_manager.add_component(cam,
                                           CameraComponent(
                                               aspect=self.window.width / self.window.height,
                                               projection=ProjectionType.PERSPECTIVE
                                           )
                                           )

        scene.entity_manager.add_component(cam,
                                           PlayerController()
                                           )
        # 4) Light
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

        # 5) Launch
        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024, 768), title="ZEngine")
    app.setup()
    app.run()

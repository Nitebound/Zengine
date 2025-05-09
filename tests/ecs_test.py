from zengine.core.project_canvas import ProjectCanvas
from zengine.core.scene import Scene
from zengine.ecs.components import (
    Transform,
    SpriteRenderer,
    PlayerController,
)
from zengine.ecs.components.camera_view import CameraView, ProjectionType
from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.camera_controller_system import CameraControllerSystem
from zengine.ecs.systems.camera_system import CameraSystem
from zengine.ecs.systems.player_controller_system import PlayerControllerSystem
from zengine.ecs.systems.render_system import RenderSystem
from zengine.graphics.texture_loader import load_texture_2d

class MyGame(ProjectCanvas):
    def setup(self):
        scene = Scene()

        # inside MyGame.setup()

        cam_e = scene.entities.create_entity()
        scene.entities.add_component(cam_e, Transform(x=0, y=10, z=10))
        scene.entities.add_component(cam_e,
                                     CameraView(
                                         projection_type=ProjectionType.ORTHO,
                                         left=-512, right=512,
                                         bottom=-384, top=384,
                                         active=True
                                     )
                                     )

        # — Instantiate systems —
        input_sys = InputSystem()
        cam_ctrl  = CameraControllerSystem(input_sys, speed=5.0)
        pc_sys    = PlayerControllerSystem(input_sys)
        cam_sys   = CameraSystem(scene)

        render_sys = RenderSystem()

        # — Register systems in order —
        scene.add_system(input_sys)
        scene.add_system(cam_ctrl)
        scene.add_system(cam_sys)
        scene.add_system(pc_sys)
        scene.add_system(render_sys)

        # — Spawn your player quad —
        player = scene.entities.create_entity()
        scene.entities.add_component(player, Transform(x=0.0, y=0.0, z=0.0))
        scene.entities.add_component(player, PlayerController())
        tex = load_texture_2d(self.window.ctx, "assets/images/mech1.png")
        scene.entities.add_component(player, SpriteRenderer(tex))
        print("Created Player entity:", player)
        # — Finally, register the scene on the canvas —
        self.add_scene("main", scene, make_current=True)
        print("Scene added:", scene)

if __name__ == "__main__":
    app = MyGame(size=(1024,768), title="ZVisger Engine")
    app.run()

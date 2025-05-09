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
        # 1) Create Scene and core systems
        scene = Scene()
        input_sys = InputSystem()
        scene.add_system(input_sys)

        cam_ctrl = CameraControllerSystem(input_sys, speed=551.0, lock_z=10.0)
        scene.add_system(cam_ctrl)

        scene.add_system(CameraSystem(scene))
        scene.add_system(PlayerControllerSystem(input_sys))

        # 2) Camera Entity
        cam_ent = scene.entities.create_entity()
        # put camera at Z=10 looking toward Z=0
        scene.entities.add_component(cam_ent,
            Transform(x=0.0, y=0.0, z=10.0)
        )
        # orthographic bounds = half-width/height around 0
        w, h = self.window.width, self.window.height
        scene.entities.add_component(cam_ent,
            CameraView(
                projection_type=ProjectionType.ORTHO,
                left   = -w/2, right  =  w/2,
                bottom = -h/2, top    =  h/2,
                near   =  0.1, far    = 100.0,
                active = True
            )
        )

        # 3) Player (quad + sprite)
        player = scene.entities.create_entity()

        # load your sprite
        tex = load_texture_2d(self.window.ctx, "assets/images/mech1.png")
        # size the quad to the texture’s pixel dims:
        scene.entities.add_component(player,
            Transform(
                x=0.0, y=0.0, z=0.0,
                scale_x=tex.width, scale_y=tex.height, scale_z=1.0
            )
        )
        scene.entities.add_component(player, SpriteRenderer(tex))

        # 4) Rendering
        scene.add_system(RenderSystem())

        # 5) Register scene and go
        self.add_scene("main", scene, make_current=True)


if __name__ == "__main__":
    app = MyGame(size=(1024,768), title="ZVisger Engine")
    app.run()

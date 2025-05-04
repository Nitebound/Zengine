from zengine.core.project_canvas import ProjectCanvas
from zengine.core.scene    import Scene
from zengine.ecs.components.transform       import Transform
from zengine.ecs.components.sprite_renderer import SpriteRenderer
from zengine.ecs.components.player_controller import PlayerController
from zengine.ecs.components.camera_view       import CameraView, ProjectionType
from zengine.ecs.systems.input_system         import InputSystem
from zengine.ecs.systems.camera_controller_system import CameraControllerSystem
from zengine.ecs.systems.camera_system           import CameraSystem
from zengine.ecs.systems.player_controller_system import PlayerControllerSystem
from zengine.ecs.systems.render_system            import RenderSystem
from zengine.graphics.texture_loader               import load_texture_2d

class MyGame(ProjectCanvas):
    def setup(self):
        scene = Scene()

        # Camera entity at +Z looking straight down
        cam = scene.entities.create_entity()
        scene.entities.add_component(cam, Transform(x=0, y=0, z=10))
        scene.entities.add_component(cam,
            CameraView(
                projection_type=ProjectionType.ORTHO,
                left   = -self.window.width/2,
                right  =  self.window.width/2,
                bottom = -self.window.height/2,
                top    =  self.window.height/2,
                active=True
            )
        )

        # Systems
        inp    = InputSystem()
        cc_sys = CameraControllerSystem(inp, speed=5.0, lock_z=10.0)

        # cc_sys = CameraControllerSystem(inp, speed=5.0)
        c_sys  = CameraSystem(scene)
        pc_sys = PlayerControllerSystem(inp)
        r_sys  = RenderSystem()

        scene.add_system(inp)
        scene.add_system(cc_sys)
        scene.add_system(c_sys)
        scene.add_system(pc_sys)
        scene.add_system(r_sys)

        # Player quad at world origin
        p = scene.entities.create_entity()
        scene.entities.add_component(p, Transform(x=0, y=0, z=0))
        scene.entities.add_component(p, PlayerController())
        tex = load_texture_2d(self.window.ctx, "assets/images/mech1.png")
        scene.entities.add_component(p, SpriteRenderer(tex))

        self.add_scene("main", scene, make_current=True)

if __name__ == "__main__":
    app = MyGame(size=(1024,768), title="ZVisger Engine")
    app.run()

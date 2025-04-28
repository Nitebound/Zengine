from zengine.core.window import Window
from zengine.core.renderer import Renderer
from zengine.core.camera import Camera
from zengine.core.event_system import EventSystem
from zengine.graphics.shader import Shader
from zengine.graphics.texture_loader import load_texture_2d  # <--- FIXED!
from zengine.ecs.entity_manager import EntityManager
from zengine.ecs.components import Transform, SpriteRenderer
from zengine.ecs.systems.render_system import RenderSystem

def main():
    import moderngl_window as mglw
    mglw.run_window_config(ZengineApp)

class ZengineApp(Window):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.events = EventSystem()
        self.camera = Camera(90, self.window_size[0]/self.window_size[1], 0.001, 10000)
        self.entities = EntityManager()

        shader = Shader(self.ctx, "assets/shaders/basic.vert", "assets/shaders/basic.frag")
        self.renderer = Renderer(self.ctx, shader)

        # ✅ Manually load texture
        texture = load_texture_2d(self.ctx, "assets/images/mech1.png")

        player = self.entities.create_entity()
        self.entities.add_component(player, Transform(0,0, 0))
        self.entities.add_component(player, SpriteRenderer(texture))

        self.systems.append(RenderSystem())

    def on_render(self, time: float, frame_time: float):  # ✅ ModernGL expects this
        self.ctx.clear(0.1, 0.1, 0.1)

        for system in self.systems:
            system.process(self.renderer, self.camera, self.entities)

if __name__ == "__main__":
    main()

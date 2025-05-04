import time
from zengine.core.window    import Window
from zengine.core.renderer  import Renderer
from zengine.core.scene     import Scene
from zengine.graphics.shader import Shader

class ProjectCanvas:
    def __init__(self, size=(800,600), title="Zengine"):
        # 1) Window & GL
        self.window = Window(size, title)
        prog = Shader(self.window.ctx,
                      "assets/shaders/basic.vert",
                      "assets/shaders/basic.frag")
        self.window.renderer = Renderer(self.window.ctx, prog)

        # 2) ECS scene container
        self.scenes = {}
        self.current_scene = None

        # 3) User setup hook
        self.setup()

    def setup(self):
        """Override this to create Scene, add systems & entities."""
        pass

    def add_scene(self, name: str, scene: Scene, make_current=False):
        self.scenes[name] = scene
        if make_current or not self.current_scene:
            self.current_scene = scene

    def run(self):
        last = time.time()
        while self.window.running:
            # Poll and dispatch events
            for event in self.window.get_events():
                if self.current_scene:
                    self.current_scene.on_event(event)

            # Update
            now = time.time()
            dt  = now - last
            last = now
            if self.current_scene:
                self.current_scene.on_update(dt)

            # Render
            self.window.ctx.clear(0.1, 0.1, 0.1)
            if self.current_scene:
                self.current_scene.on_render(self.window.renderer)

            self.window.on_late_update(dt)

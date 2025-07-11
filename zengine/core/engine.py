# zengine/core/engine.py
import time
from pathlib import Path

from .window   import Window
from .renderer import Renderer
from zengine.core.scene import Scene
from ..graphics.shader import Shader

class Engine:
    def __init__(self, size=(800, 600), title="Zengine"):
        self.window = Window(size, title)

        base_dir = Path(__file__).parent.parent
        shaders = base_dir / "assets" / "shaders"

        # Absolute paths to the default shaders
        default_vert = shaders / "basic_vert.glsl"
        default_frag = shaders / "basic_frag.glsl"

        # load them by absolute path
        self.default_shader = Shader(
            self.window.ctx,
            str(default_vert),
            str(default_frag),
        )

        debug_vert = shaders / "debug_vert.glsl"
        debug_frag = shaders / "debug_frag.glsl"
        self.debug_shader = Shader(
            self.window.ctx,
            str(debug_vert),
            str(debug_frag),
        )

        # rest of your init…
        self.renderer = Renderer(self.window.ctx, self.default_shader)
        self.scenes = {}
        self.current = None

    def add_scene(self, name: str, scene: Scene, make_current=False):
        # keep a back-ref so systems can see window.width/height
        scene.window = self.window
        self.scenes[name] = scene
        if make_current or not self.current:
            self.current = scene

    def run(self):
        if not self.current:
            raise RuntimeError(
                "No current scene—did you forget add_scene(..., make_current=True)?"
            )

        last = time.time()
        while self.window.running:
            events = self.window.get_events()
            for e in events:
                self.current.on_event(e)

            now = time.time(); dt = now - last; last = now
            self.current.on_update(dt)

            self.window.ctx.clear(0,0,0, depth=1.0)
            self.current.on_render(self.renderer)

            self.window.on_late_update(dt)
            self.current.on_late_update(dt)

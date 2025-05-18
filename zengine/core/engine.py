# zengine/core/engine.py
import time
from pathlib import Path

from .window   import Window
from .renderer import Renderer
from zengine.core.scene import Scene
from ..graphics.shader import Shader

class Engine:
    def __init__(self, size=(800, 600), title="Zengine"):
        # create window/context first
        self.window = Window(size, title)

        # locate the shaders_x directory inside the installed package
        # e.g. <your-venv>/lib/python3.x/site-packages/zengine/assets/shaders_x
        base_dir = Path(__file__).parent.parent  # .../zengine/core -> .../zengine
        shaders = base_dir / "assets" / "shaders"

        # now build absolute paths to each file
        default_vert = shaders / "basic.vert"
        default_frag = shaders / "basic.frag"
        flat_vert = shaders / "flat_color.vert"
        flat_frag = shaders / "flat_color.frag"
        lit_vert = shaders / "lit.vert"
        lit_frag = shaders / "lit.frag"
        phong_vert = shaders / "phong.vert"
        phong_frag = shaders / "phong.frag"
        skinning_vert = shaders / "skinning_phong.vert"
        skinning_frag = shaders / "skinning_phong.frag"

        # load them by absolute path
        self.default_shader = Shader(
            self.window.ctx,
            str(default_vert),
            str(default_frag),
        )
        self.flat_shader = Shader(
            self.window.ctx,
            str(flat_vert),
            str(flat_frag),
        )
        self.lit_shader = Shader(
            self.window.ctx,
            str(lit_vert),
            str(lit_frag),
        )
        self.phong_shader = Shader(
            self.window.ctx,
            str(phong_vert),
            str(phong_frag),
        )

        self.skinning_shader = Shader(
            self.window.ctx,
            str(skinning_vert),
            str(skinning_frag)
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

            self.window.ctx.clear(0.0, 1, 1, 1.0, depth=1.0)
            self.current.on_render(self.renderer)
            self.window.on_late_update(dt)
            self.current.on_late_update(dt)

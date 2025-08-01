import time
from pathlib import Path

from .window   import Window
from .renderer import Renderer
from zengine.core.scene import Scene
from zengine.graphics.shader import Shader # Ensure Shader is imported

class Engine:
    def __init__(self, size=(800, 600), title="Zengine"):
        self.window = Window(size, title)
        self.window.ctx.clear(0.0, 0.0, 0.0, depth=1.0) # Clear once on init

        # --- CRITICAL FIX: Initialize shaders correctly here ---
        # Base directory for shaders, using your specified path structure
        shader_dir = Path(__file__).parent.parent / "assets" / "shaders"

        # Load default_shader (for main game objects, like your cube)
        default_vert_path = shader_dir / "basic_vert.glsl"
        default_frag_path = shader_dir / "basic_frag.glsl"
        try:
            self.default_shader = Shader(
                self.window.ctx,
                str(default_vert_path),
                str(default_frag_path),
            )

        except Exception as e:
            print(f"ERROR: Failed to load default_shader: {e}")
            self.default_shader = None # Set to None to prevent further errors

        # Load debug_shader (for gizmos)
        debug_vert_path = shader_dir / "debug_vert.glsl"
        debug_frag_path = shader_dir / "debug_frag.glsl"
        try:
            self.debug_shader = Shader(
                self.window.ctx,
                str(debug_vert_path),
                str(debug_frag_path),
            )
        except Exception as e:
            print(f"ERROR: Failed to load debug_shader: {e}")
            self.debug_shader = None # Set to None to prevent further errors


        self.renderer = Renderer(self.window.ctx, self.default_shader) # Renderer uses default_shader
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

            # Clear the screen each frame
            self.window.ctx.clear(.3,.3,.3, depth=1.0) # Black background, clear depth
            self.current.on_render(self.renderer)

            self.window.on_late_update(dt)
            self.current.on_late_update(dt)


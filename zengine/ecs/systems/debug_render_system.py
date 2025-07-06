from pathlib import Path

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform
import numpy as np

from zengine.graphics.shader import Shader


class DebugRenderSystem(System):
    def __init__(self, ctx, scene):
        super().__init__()
        self.ctx = ctx
        self.scene = scene
        self.enabled = {
            "grid": True,
            "axes": True,
            "bones": False,
            "bounding_boxes": False
        }

    def on_render(self, renderer):
        if self.enabled["grid"]:
            self.draw_grid()

        for eid in self.scene.entity_manager.get_entities_with(Transform):
            tr = self.scene.entity_manager.get_component(eid, Transform)

            if self.enabled["axes"]:
                self.draw_axes(tr)
            if self.enabled["bounding_boxes"]:
                self.draw_bounding_box(tr)

    def draw_grid(self):
        # Draw an infinite floor grid using lines (use shader or GL_LINES)
        ...

    def draw_axes(self, tr):
        # Draw RGB axes from tr position using a simple line shader
        ...

    def draw_bounding_box(self, tr):
        # Optional: draw wireframe box or debug cube
        ...

    def set_enabled(self, name, state=True):
        self.enabled[name] = state

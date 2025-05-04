# zengine/core/scene.py

from zengine.ecs.entity_manager import EntityManager
from zengine.ecs.systems.system import System

class Scene:
    def __init__(self):
        self.entities      = EntityManager()
        self.systems       = []            # type: list[System]
        self.active_camera = None          # gets set by CameraSystem

    def add_system(self, system: System):
        self.systems.append(system)

    def on_event(self, event):
        for sys in self.systems:
            sys.on_event(event)

    def on_update(self, dt: float):
        for sys in self.systems:
            sys.on_update(dt, self.entities)

    def on_render(self, renderer):
        for sys in self.systems:
            sys.on_render(renderer, self, self.entities)

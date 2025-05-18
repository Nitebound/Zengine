from zengine.ecs.entity_manager import EntityManager
from zengine.ecs.systems.system import System

class Scene:
    def __init__(self):
        self.entity_manager      = EntityManager()
        self.systems       = []            # list[System]
        self.active_camera = None
        self._systems_by_type = {}

    def add_system(self, system: System):
        system.on_added(self)
        self.systems.append(system)
        self._systems_by_type[type(system)] = system

    def on_event(self, event):
        for sys in self.systems:
            sys.on_event(event)

    def on_update(self, dt: float):
        for sys in self.systems:
            sys.on_update(dt)

    def on_render(self, renderer):
        for sys in self.systems:
            sys.on_render(renderer)

    def on_late_update(self, dt: float):
        for sys in self.systems:
            sys.on_late_update(dt)

    def get_system(self, system_type):
        return self._systems_by_type.get(system_type, None)

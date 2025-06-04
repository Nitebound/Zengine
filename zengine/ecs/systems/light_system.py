# zengine/ecs/systems/light_system.py

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform
from zengine.ecs.components.light import LightComponent


class LightSystem(System):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.lights = []

    def on_update(self, dt):
        self.lights.clear()

        em = self.scene.entity_manager
        for eid in em.get_entities_with(Transform, LightComponent):
            tr = em.get_component(eid, Transform)
            light = em.get_component(eid, LightComponent)
            self.lights.append((light, tr))

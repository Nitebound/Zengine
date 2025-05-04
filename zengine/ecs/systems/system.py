# zengine/ecs/system.py
class System:
    def on_event(self, event):        pass
    def on_update(self, dt: float, em): pass
    def on_render(self, renderer, camera, em): pass

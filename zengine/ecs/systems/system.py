# zengine/ecs/systems/system.py

class System:
    def __init__(self):
        # Will be set when the system is added to a Scene
        self.scene = None
        self.em = None
        self.active = True

    def on_added(self, scene):
        """Called by Scene.add_system() to inject Scene and EntityManager."""
        self.scene = scene
        self.em = scene.entity_manager

    # Override these in subclasses:
    def on_event(self, event):
        pass

    def on_update(self, dt):
        pass

    def on_render(self, renderer):
        pass

    def on_late_update(self, dt):
        pass

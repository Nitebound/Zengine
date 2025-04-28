import moderngl_window as mglw

class Window(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "Zengine"
    window_size = (800, 600)
    aspect_ratio = None
    resizable = True
    resource_dir = "assets/"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # The renderer will be attached after everything initializes
        self.renderer = None
        self.entities = None
        self.camera = None
        self.events = None
        self.systems = []

    def render(self, time, frame_time):
        # Clear the screen
        self.ctx.clear(0.1, 0.1, 0.1)

        # Call your ECS systems (rendering system)
        for system in self.systems:
            system.process(self.renderer, self.camera, self.entities)

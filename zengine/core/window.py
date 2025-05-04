import moderngl
import pygame


class Window:
    def __init__(
        self,
        size=(800, 600),
        title="Zengine",
        alpha_blending=True,
    ):
        pygame.init()
        pygame.display.set_mode(size, pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption(title)
        self.width, self.height = size

        # self.ctx = moderngl.create_context(require=gl_version)
        self.ctx = moderngl.create_context()

        if alpha_blending:
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = (
                moderngl.SRC_ALPHA,
                moderngl.ONE_MINUS_SRC_ALPHA,
            )

        self.running = True
        self.window_size = size
        self.systems     = []
        self.entities    = None
        self.camera      = None
        self.renderer    = None

    def get_events(self):
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

        return events

    def on_event(self, event):
        pass

    def on_update(self, dt):
        for sys in self.systems:
            # most systems expect update(dt, entities)
            if hasattr(sys, "on_update"):
                sys.update(dt, self.entities)

    def on_late_update(self, dt):
        pygame.display.flip()
        for sys in self.systems:
            # most systems expect late_update(dt, entities)
            if hasattr(sys, "on_late_update"):
                sys.on_late_update(dt, self.entities)
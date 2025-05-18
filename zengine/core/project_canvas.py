# import time
# from zengine.core.window import Window
# from zengine.core.renderer import Renderer
# from zengine.core.scene import Scene
# from zengine.graphics.shader import Shader
#
# class ProjectCanvas:
#     def __init__(self, size=(800,600), title="Zengine"):
#         # 1) Window & OpenGL context
#         self.window = Window(size, title)
#         shader = Shader(
#             self.window.ctx,
#             "assets/shaders_x/basic.vert",
#             "assets/shaders_x/basic.frag"
#         )
#         self.window.renderer = Renderer(self.window.ctx, shader)
#
#         # 2) ECS-managed scenes
#         self.scenes = {}
#         self.current_scene = None
#
#         # 3) Hook for user to set up scenes/systems/entities
#         self.setup()
#
#     def add_scene(self, name: str, scene: Scene, make_current=False):
#         self.scenes[name] = scene
#         if make_current or not self.current_scene:
#             self.current_scene = scene
#
#     def run(self):
#         last_time = time.time()
#         while self.window.running:
#             # 1) Poll and dispatch events
#             for event in self.window.get_events():
#                 if self.current_scene:
#                     self.current_scene.on_event(event)
#
#             # 2) Update
#             now = time.time()
#             dt = now - last_time
#             last_time = now
#             if self.current_scene:
#                 self.current_scene.on_update(dt)
#
#             # 3) Render (ECS CameraSystem must set scene.active_camera)
#             self.window.ctx.clear(0.5, 0.1, 0.1, 1.0, depth=1.0)
#
#             if self.current_scene:
#                 self.current_scene.on_render(self.window.renderer)
#
#             # 4) Swap buffers
#             self.window.on_late_update(dt)

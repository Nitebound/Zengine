import pygame
import moderngl
import glm
import numpy as np
import pygame
import moderngl
from pyglm import glm
import numpy as np
from imgui_bundle import imgui
from imgui_bundle.python_backends.python_backends_disabled.pygame_backend import PygameRenderer
# Initialize Pygame and create window
pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size, pygame.OPENGL | pygame.DOUBLEBUF)
pygame.display.set_caption("ImGui with Pygame and ModernGL")

# Create modernGL context
ctx = moderngl.create_context()

# Shader for rotating cube
vertex_shader = """
#version 330
uniform mat4 m_proj;
uniform mat4 m_model;
in vec3 in_position;
void main() {
    gl_Position = m_proj * m_model * vec4(in_position, 1.0);
}
"""
fragment_shader = """
#version 330
uniform vec4 color;
out vec4 f_color;
void main() {
    f_color = color;
}
"""
prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
prog["color"].value = (1.0, 0.5, 0.5, 1.0)  # Reddish tint
prog["m_proj"].write(glm.perspective(glm.radians(75), window_size[0]/window_size[1], 1, 100))

# Cube geometry
vertices = np.array([
    # Front face
    -1, -1,  1,   1, -1,  1,   1,  1,  1,  -1,  1,  1,
    # Back face
    -1, -1, -1,   1, -1, -1,   1,  1, -1,  -1,  1, -1,
], dtype=np.float32)
indices = np.array([
    0, 1, 2, 2, 3, 0,  # Front
    5, 4, 7, 7, 6, 5,  # Back
    4, 5, 1, 1, 0, 4,  # Bottom
    6, 7, 3, 3, 2, 6,  # Top
    4, 0, 3, 3, 7, 4,  # Left
    1, 5, 6, 6, 2, 1,  # Right
], dtype=np.uint32)
vbo = ctx.buffer(vertices.tobytes())
ibo = ctx.buffer(indices.tobytes())
vao = ctx.vertex_array(prog, [(vbo, "3f", "in_position")], ibo)

# Initialize ImGui
imgui.create_context()
io = imgui.get_io()
io.config_flags |= imgui.ConfigFlags_.docking_enable
io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard
io.mouse_draw_cursor = True  # Ensure ImGui cursor is visible
io.display_size = window_size  # Explicitly set display size
imgui_renderer = PygameRenderer()

# Main loop
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        imgui_renderer.process_event(event)
        print(f"Pygame event: type={event.type}, {event.__dict__}")  # Debug

    # Update ImGui
    imgui.new_frame()
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, _ = imgui.menu_item("Quit", "Cmd+Q", False, True)
            if clicked_quit:
                running = False
            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.show_demo_window()  # Demo window with buttons, labels, sliders, etc.

    imgui.begin("Custom window", True)
    imgui.text("This is a label")
    if imgui.button("Click me!"):
        print("Button clicked!")
    imgui.end()

    # # Render game graphics (rotating cube)
    # ctx.clear(0.2, 0.2, 0.2)
    # ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
    # rotation = glm.mat4(glm.quat(glm.vec3(pygame.time.get_ticks() * 0.001, pygame.time.get_ticks() * 0.001, 0)))
    # translation = glm.translate(glm.vec3(0.0, 0.0, -3.5))
    # model = translation * rotation
    # prog["m_model"].write(model)
    # vao.render(moderngl.TRIANGLES)

    # Render ImGui
    imgui.render()
    imgui_renderer.render(imgui.get_draw_data())

    pygame.display.flip()
    clock.tick(60)

# Cleanup
imgui_renderer.shutdown()
pygame.quit()
# Initialize Pygame and create window
pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size, pygame.OPENGL | pygame.DOUBLEBUF)
pygame.display.set_caption("ImGui with Pygame and ModernGL")

# Create modernGL context
ctx = moderngl.create_context()

# Shader for rotating cube
vertex_shader = """
#version 330
uniform mat4 m_proj;
uniform mat4 m_model;
in vec3 in_position;
void main() {
    gl_Position = m_proj * m_model * vec4(in_position, 1.0);
}
"""
fragment_shader = """
#version 330
uniform vec4 color;
out vec4 f_color;
void main() {
    f_color = color;
}
"""
prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
prog["color"].value = (1.0, 0.5, 0.5, 1.0)  # Reddish tint
prog["m_proj"].write(glm.perspective(glm.radians(75), window_size[0]/window_size[1], 1, 100))

# Cube geometry
vertices = np.array([
    # Front face
    -1, -1,  1,   1, -1,  1,   1,  1,  1,  -1,  1,  1,
    # Back face
    -1, -1, -1,   1, -1, -1,   1,  1, -1,  -1,  1, -1,
], dtype=np.float32)
indices = np.array([
    0, 1, 2, 2, 3, 0,  # Front
    5, 4, 7, 7, 6, 5,  # Back
    4, 5, 1, 1, 0, 4,  # Bottom
    6, 7, 3, 3, 2, 6,  # Top
    4, 0, 3, 3, 7, 4,  # Left
    1, 5, 6, 6, 2, 1,  # Right
], dtype=np.uint32)
vbo = ctx.buffer(vertices.tobytes())
ibo = ctx.buffer(indices.tobytes())
vao = ctx.vertex_array(prog, [(vbo, "3f", "in_position")], ibo)

# Initialize ImGui
imgui.create_context()
io = imgui.get_io()
io.config_flags |= imgui.ConfigFlags_.docking_enable
io.config_flags |= imgui.ConfigFlags_.nav_enable_keyboard
io.mouse_draw_cursor = True  # Ensure ImGui cursor is visible
io.display_size = window_size  # Explicitly set display size
imgui_renderer = PygameRenderer()

# Main loop
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        imgui_renderer.process_event(event)
        print(f"Pygame event: type={event.type}, {event.__dict__}")  # Debug

    # Update ImGui
    imgui.new_frame()
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            clicked_quit, _ = imgui.menu_item("Quit", "Cmd+Q", False, True)
            if clicked_quit:
                running = False
            imgui.end_menu()
        imgui.end_main_menu_bar()

    imgui.show_demo_window()  # Demo window with buttons, labels, sliders, etc.

    imgui.begin("Custom window", True)
    imgui.text("This is a label")
    if imgui.button("Click me!"):
        print("Button clicked!")
    imgui.end()

    # Render game graphics (rotating cube)
    ctx.clear(0.2, 0.2, 0.2)
    ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
    rotation = glm.mat4(glm.quat(glm.vec3(pygame.time.get_ticks() * 0.001, pygame.time.get_ticks() * 0.001, 0)))
    translation = glm.translate(glm.vec3(0.0, 0.0, -3.5))
    model = translation * rotation
    prog["m_model"].write(model)
    vao.render(moderngl.TRIANGLES)

    # Render ImGui
    imgui.render()
    imgui_renderer.render(imgui.get_draw_data())

    pygame.display.flip()
    clock.tick(60)

# Cleanup
imgui_renderer.shutdown()
pygame.quit()
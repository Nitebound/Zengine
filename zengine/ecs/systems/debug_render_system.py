from pathlib import Path

import moderngl
import numpy as np
import math

from zengine.ecs.systems.system import System
from zengine.ecs.components import Transform
from zengine.ecs.components.camera import CameraComponent # Assuming this path is correct based on your RenderSystem
from zengine.graphics.shader import Shader
from zengine.util.quaternion import quat_to_mat4 # Assuming this path is correct based on your RenderSystem


# Helper function to compute a model matrix from a Transform component.
# This is crucial for positioning and orienting debug elements.
# Copied from your RenderSystem for self-containment, but ideally shared.
def compute_model_matrix(tr: Transform) -> np.ndarray:
    """
    Computes a 4x4 model matrix from a Transform component's position, rotation, and scale.
    """
    # Translation matrix
    T = np.eye(4, dtype='f4')
    T[:3, 3] = (tr.x, tr.y, tr.z)

    # Rotation matrix from quaternion
    R_mat = quat_to_mat4(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)

    # Scale matrix
    S = np.diag([tr.scale_x, tr.scale_y, tr.scale_z, 1.0]).astype('f4')

    # Model matrix is T @ R @ S
    return T @ R_mat @ S


class DebugRenderSystem(System):
    """
    A system for rendering debug visualizations in the scene, such as a grid,
    entity axes, and bounding boxes.
    """
    def __init__(self, ctx, scene):
        super().__init__()
        self.ctx = ctx
        self.scene = scene
        self.enabled = {
            "grid": True,
            "axes": True,
            "bones": False, # Bones rendering would require skeleton data and is not implemented here
            "bounding_boxes": False
        }

        # --- Debug Shaders Initialization ---
        # Using your specified shader path: Path(__file__).parent.parent / "assets" / "shaders"
        shader_dir = Path(__file__).parent.parent.parent / "assets" / "shaders"

        # Load the shader programs using your existing debug_vert.glsl and debug_frag.glsl.
        # All debug elements will share these shaders and rely on setting the 'color' uniform.
        self.grid_shader = Shader(self.ctx, str(shader_dir / "debug_vert.glsl"), str(shader_dir / "debug_frag.glsl"))
        self.axes_shader = Shader(self.ctx, str(shader_dir / "debug_vert.glsl"), str(shader_dir / "debug_frag.glsl"))
        self.bbox_shader = Shader(self.ctx, str(shader_dir / "debug_vert.glsl"), str(shader_dir / "debug_frag.glsl"))

        # --- VAOs for Debug Geometry ---
        # Initialize Vertex Array Objects (VAOs) for the static debug geometries.
        # These are created once and reused for rendering.
        self._grid_vao = None
        self._init_grid_vao()

        self._axes_vao = None
        self._init_axes_vao()

        self._bbox_vao = None
        self._init_bbox_vao()

        # --- ModernGL Context Settings ---
        # Enable depth testing to ensure debug elements are correctly occluded by scene geometry.
        # Disable face culling as we are drawing lines, not solid surfaces.
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.CULL_FACE)
        # Optionally set line width for better visibility of debug lines
        self.ctx.line_width = 2.0 # You can adjust this value

    def _init_grid_vao(self):
        """
        Initializes the VAO for drawing a large floor grid on the XY plane (Z=0).
        The grid is composed of lines parallel to the X and Y axes.
        """
        size = 50.0 # Grid extends from -size to +size on X and Y
        step = 1.0  # Spacing between grid lines
        lines = []
        # Generate lines parallel to the Y-axis (fixed X, varying Y, Z=0)
        for i in range(int(-size / step), int(size / step) + 1):
            lines.append((i * step, -size, 0.0)) # Start point (X, Y, Z=0)
            lines.append((i * step, size, 0.0))  # End point (X, Y, Z=0)
        # Generate lines parallel to the X-axis (varying X, fixed Y, Z=0)
        for i in range(int(-size / step), int(size / step) + 1):
            lines.append((-size, i * step, 0.0)) # Start point (X, Y, Z=0)
            lines.append((size, i * step, 0.0))  # End point (X, Y, Z=0)

        vertices = np.array(lines, dtype='f4')
        vbo = self.ctx.buffer(vertices.tobytes())
        self._grid_vao = self.ctx.vertex_array(
            self.grid_shader.program,
            [(vbo, '3f', 'in_position')] # '3f' for 3 floats (x, y, z)
        )

    def _init_axes_vao(self):
        """
        Initializes the VAO for drawing XYZ axes (Red=X, Green=Y, Blue=Z).
        Each axis is a line segment from the origin to a unit length along its direction.
        Since the shared fragment shader uses a uniform color, the vertex data
        only needs to contain position.
        """
        # Vertices for X, Y, Z axes. No color data here.
        axes_vertices = np.array([
            # X-axis
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0,

            # Y-axis
            0.0, 0.0, 0.0,
            0.0, 1.0, 0.0,

            # Z-axis
            0.0, 0.0, 0.0,
            0.0, 0.0, 1.0,
        ], dtype='f4')
        vbo = self.ctx.buffer(axes_vertices.tobytes())
        self._axes_vao = self.ctx.vertex_array(
            self.axes_shader.program,
            [(vbo, '3f', 'in_position')] # Only 'in_position' attribute is needed
        )

    def _init_bbox_vao(self):
        """
        Initializes the VAO for drawing a unit wireframe cube, representing a bounding box.
        The cube is centered at the origin, with sides of length 1 (from -0.5 to 0.5).
        """
        # Vertices for the 12 edges of a unit cube wireframe.
        # Each pair of consecutive vertices forms a line segment.
        bbox_vertices = np.array([
            # Bottom face (Z=-0.5)
            -0.5, -0.5, -0.5,   0.5, -0.5, -0.5,
             0.5, -0.5, -0.5,   0.5,  0.5, -0.5,
             0.5,  0.5, -0.5,  -0.5,  0.5, -0.5,
            -0.5,  0.5, -0.5,  -0.5, -0.5, -0.5,

            # Top face (Z=0.5)
            -0.5, -0.5,  0.5,   0.5, -0.5,  0.5,
             0.5, -0.5,  0.5,   0.5,  0.5,  0.5,
             0.5,  0.5,  0.5,  -0.5,  0.5,  0.5,
            -0.5,  0.5,  0.5,  -0.5, -0.5,  0.5,

            # Connecting vertical edges (along Z)
            -0.5, -0.5, -0.5,  -0.5, -0.5,  0.5,
             0.5, -0.5, -0.5,   0.5, -0.5,  0.5,
             0.5,  0.5, -0.5,   0.5,  0.5,  0.5,
            -0.5,  0.5, -0.5,  -0.5,  0.5,  0.5,
        ], dtype='f4')
        vbo = self.ctx.buffer(bbox_vertices.tobytes())
        self._bbox_vao = self.ctx.vertex_array(
            self.bbox_shader.program,
            [(vbo, '3f', 'in_position')] # '3f' for 3 floats (x, y, z)
        )

    def on_render(self, renderer):
        """
        Called each frame to render the enabled debug visualizations.
        """
        # Get the active camera's projection and view matrices.
        # These are essential for correctly projecting 3D debug elements onto the 2D screen.
        cam_e = self.scene.active_camera
        if cam_e is None:
            # If no active camera is set, debug rendering cannot proceed.
            return

        cp_cam = self.scene.entity_manager.get_component(cam_e, CameraComponent)
        if cp_cam is None:
            # If the active camera entity lacks a CameraComponent, debug rendering cannot proceed.
            return

        proj = cp_cam.projection_matrix
        view = cp_cam.view_matrix

        # Render the grid if enabled.
        if self.enabled["grid"] and self._grid_vao is not None:
            self.draw_grid(proj, view)

        # Iterate over all entities that have a Transform component.
        # Axes and bounding boxes are drawn per entity.
        for eid in self.scene.entity_manager.get_entities_with(Transform):
            tr = self.scene.entity_manager.get_component(eid, Transform)

            # Render axes for the entity's transform if enabled.
            if self.enabled["axes"] and self._axes_vao is not None:
                self.draw_axes(tr, proj, view)

            # Render a bounding box for the entity's transform if enabled.
            if self.enabled["bounding_boxes"] and self._bbox_vao is not None:
                self.draw_bounding_box(tr, proj, view)

    def draw_grid(self, proj: np.ndarray, view: np.ndarray):
        """
        Draws the floor grid.
        """
        prog = self.grid_shader.program
        # Pass the view and projection matrices to the shader.
        # The grid itself is at the world origin, so its model matrix is identity.
        if 'view' in prog:       prog['view'].write(view.T.astype('f4').tobytes())
        if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())
        if 'model' in prog:      prog['model'].write(np.eye(4, dtype='f4').T.tobytes()) # Grid is at world origin
        if 'color' in prog:      prog['color'].value = (0.2, 0.2, 0.2) # Dark grey for grid
        self._grid_vao.render(moderngl.LINES)

    def draw_axes(self, tr: Transform, proj: np.ndarray, view: np.ndarray):
        """
        Draws RGB axes at the position and orientation of the given Transform component.
        Each axis is drawn separately, setting the uniform color before each draw call.
        """
        prog = self.axes_shader.program
        # Compute the model matrix for the axes based on the entity's transform.
        model = compute_model_matrix(tr)

        # Pass the model, view, and projection matrices to the shader.
        if 'model' in prog:      prog['model'].write(model.T.astype('f4').tobytes())
        if 'view' in prog:       prog['view'].write(view.T.astype('f4').tobytes())
        if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())

        # Draw X-axis (Red)
        if 'color' in prog: prog['color'].value = (1.0, 0.0, 0.0) # Red
        self._axes_vao.render(moderngl.LINES, vertices=2, first=0) # First 2 vertices are X-axis

        # Draw Y-axis (Green)
        if 'color' in prog: prog['color'].value = (0.0, 1.0, 0.0) # Green
        self._axes_vao.render(moderngl.LINES, vertices=2, first=2) # Next 2 vertices are Y-axis

        # Draw Z-axis (Blue)
        if 'color' in prog: prog['color'].value = (0.0, 0.0, 1.0) # Blue
        self._axes_vao.render(moderngl.LINES, vertices=2, first=4) # Next 2 vertices are Z-axis

    def draw_bounding_box(self, tr: Transform, proj: np.ndarray, view: np.ndarray):
        """
        Draws a wireframe bounding box around the given Transform component.
        The box will be scaled and positioned according to the transform.
        """
        prog = self.bbox_shader.program
        # Compute the model matrix for the bounding box based on the entity's transform.
        # This will scale, rotate, and translate the unit cube VAO.
        model = compute_model_matrix(tr)

        # Pass the model, view, and projection matrices to the shader.
        if 'model' in prog:      prog['model'].write(model.T.astype('f4').tobytes())
        if 'view' in prog:       prog['view'].write(view.T.astype('f4').tobytes())
        if 'projection' in prog: prog['projection'].write(proj.T.astype('f4').tobytes())
        if 'color' in prog:      prog['color'].value = (1.0, 1.0, 0.0) # Yellow for bounding box
        self._bbox_vao.render(moderngl.LINES)

    def set_enabled(self, name: str, state: bool = True):
        """
        Enables or disables a specific debug visualization feature.
        """
        if name in self.enabled:
            self.enabled[name] = state
        else:
            print(f"Warning: Debug feature '{name}' not recognized.")


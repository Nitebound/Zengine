import numpy as np

class Renderer:
    def __init__(self, ctx, shader):
        self.ctx = ctx
        self.shader = shader

        # Vertex buffer: (x, y, z)
        vertices = np.array([
            -0.5, -0.5, 0.0,  # Bottom left
             0.5, -0.5, 0.0,  # Bottom right
             0.5,  0.5, 0.0,  # Top right
            -0.5,  0.5, 0.0,  # Top left
        ], dtype='f4')

        # Index buffer: 2 triangles (0,1,2) and (2,3,0)
        indices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype='i4')

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo = self.ctx.buffer(indices.tobytes())

        # Now: only `in_position` (vec3)
        self.vao = self.ctx.vertex_array(
            self.shader.program,
            [(self.vbo, '3f', 'in_position')],  # 3 floats (vec3)
            self.ibo
        )

    def draw_quad(self, model_matrix, view_projection_matrix):
        self.shader.program['u_Model'].write(model_matrix.tobytes())
        self.shader.program['u_ViewProjection'].write(view_projection_matrix.tobytes())

        self.vao.render()

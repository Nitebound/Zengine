import numpy as np

class Renderer:
    def __init__(self, ctx, program):
        self.ctx = ctx
        self.prog = getattr(program, 'program',
                    getattr(program, 'prog', program))

        # Simple quad: only position
        verts = np.array([
            -0.5, -0.5, 0.0,
             0.5, -0.5, 0.0,
             0.5,  0.5, 0.0,
            -0.5,  0.5, 0.0,
        ], dtype='f4')

        idxs = np.array([0, 1, 2, 2, 3, 0], dtype='i4')

        self.vbo = ctx.buffer(verts.tobytes())
        self.ibo = ctx.buffer(idxs.tobytes())
        self.vao = ctx.vertex_array(
            self.prog,
            [(self.vbo, '3f', 'in_position')],  # ✅ Only bind what shader declares
            self.ibo
        )

    def draw_quad(self, model, vp):
        # You can add a dummy texture bind if needed, but here we just color
        self.prog['model'].write(model.T.tobytes())
        self.prog['view_projection'].write(vp.T.tobytes())
        self.vao.render()

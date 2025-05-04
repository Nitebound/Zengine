import numpy as np

class Renderer:
    def __init__(self, ctx, program):
        self.ctx  = ctx
        # unwrap moderngl.Program if wrapped
        self.prog = getattr(program, 'program',
                    getattr(program, 'prog', program))

        # a unit quad in XY plane at Z=0
        verts = np.array([
           -0.5, -0.5, 0.0,  0.0, 0.0,
            0.5, -0.5, 0.0,  1.0, 0.0,
            0.5,  0.5, 0.0,  1.0, 1.0,
           -0.5,  0.5, 0.0,  0.0, 1.0,
        ], dtype='f4')
        idxs = np.array([0,1,2, 2,3,0], dtype='i4')

        self.vbo = ctx.buffer(verts.tobytes())
        self.ibo = ctx.buffer(idxs.tobytes())
        self.vao = ctx.vertex_array(
            self.prog,
            [(self.vbo, '3f 2f', 'in_position','in_uv')],
            self.ibo
        )

    def draw_quad(self, model, vp, texture):
        texture.use(0)
        # **transpose** to column-major
        self.prog['model'].write(model.T.tobytes())
        self.prog['view_projection'].write(vp.T.tobytes())
        self.prog['tex'].value = 0
        self.vao.render()

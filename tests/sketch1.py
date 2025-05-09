# ortho_test.py
import pygame
import moderngl
import numpy as np
from PIL import Image

VERT_SHADER = '''
#version 330
in vec3 in_pos;
in vec2 in_uv;
uniform mat4 m_model;
uniform mat4 m_vp;
out vec2 v_uv;
void main() {
    v_uv = in_uv;
    gl_Position = m_vp * m_model * vec4(in_pos, 1.0);
}
'''

FRAG_SHADER = '''
#version 330
in vec2 v_uv;
out vec4 f_color;
uniform sampler2D tex;
void main() {
    f_color = texture(tex, v_uv);
}
'''

class App:
    def __init__(self, size=(1024,768)):
        pygame.init()
        pygame.display.set_mode(size, pygame.OPENGL|pygame.DOUBLEBUF)
        self.ctx = moderngl.create_context()
        self.running = True
        self.w, self.h = size

        # Compile shaders & program
        self.prog = self.ctx.program(
            vertex_shader  = VERT_SHADER,
            fragment_shader= FRAG_SHADER,
        )

        # Full‐screen ortho: world coords = pixels
        l, r = -self.w/2, self.w/2
        b, t = -self.h/2, self.h/2
        n, f = -1000.0, 1000.0
        self.proj = np.array([
            [2/(r-l),      0,         0,  -(r+l)/(r-l)],
            [0,         2/(t-b),      0,  -(t+b)/(t-b)],
            [0,            0,   -2/(f-n),-(f+n)/(f-n)],
            [0,            0,         0,           1   ],
        ], dtype='f4')

        # Initial camera at (0,0,10), pure translate view
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.cam_z = 10.0
        self.update_view()

        # Load texture
        img = Image.open("assets/images/mech1.png").transpose(Image.FLIP_TOP_BOTTOM)
        tex = self.ctx.texture(img.size, 4, img.convert("RGBA").tobytes())
        tex.filter = moderngl.NEAREST, moderngl.NEAREST
        self.texture = tex

        # Quad VBO/VAO
        verts = np.array([
            # x,    y,    z,   u,   v
            -0.5, -0.5,  0.0, 0.0, 0.0,
             0.5, -0.5,  0.0, 1.0, 0.0,
             0.5,  0.5,  0.0, 1.0, 1.0,
            -0.5,  0.5,  0.0, 0.0, 1.0,
        ], dtype='f4')
        idxs = np.array([0,1,2, 2,3,0], dtype='i4')
        self.vbo = self.ctx.buffer(verts.tobytes())
        self.ibo = self.ctx.buffer(idxs.tobytes())
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, '3f 2f', 'in_pos','in_uv')],
            self.ibo,
        )

        # Sprite scale = actual pixel size
        self.model = np.eye(4, dtype='f4')
        w_px, h_px = img.size
        self.model[0,0] = w_px
        self.model[1,1] = h_px

    def update_view(self):
        # pure-translation view matrix
        V = np.eye(4, dtype='f4')
        V[0,3] = -self.cam_x
        V[1,3] = -self.cam_y
        V[2,3] = -self.cam_z
        self.view = V
        self.vp   = self.proj @ self.view

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0

            for e in pygame.event.get():
                if e.type == pygame.QUIT or (
                   e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    self.running = False

            # Camera pan WASD
            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_d] - keys[pygame.K_a]
            dy = keys[pygame.K_w] - keys[pygame.K_s]
            if dx or dy:
                mag = (dx*dx + dy*dy)**0.5
                dx, dy = dx/mag, dy/mag
                self.cam_x += dx * 300 * dt  # 300 pixels/sec
                self.cam_y += dy * 300 * dt
                self.update_view()

            # Render
            self.ctx.clear(0.1,0.1,0.1)
            self.texture.use(0)
            # **transpose** before write
            self.prog['m_model'].write(self.model.T.tobytes())
            self.prog['m_vp'].   write(self.vp.T.tobytes())
            self.vao.render()

            pygame.display.flip()

if __name__ == '__main__':
    App((1024,768)).run()

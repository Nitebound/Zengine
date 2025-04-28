import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

def load_texture(path):
    tex = glGenTextures(1)
    surf = pg.image.load(path).convert_alpha()
    # no need to flip now that we handle UVs
    w, h = surf.get_size()
    data = pg.image.tostring(surf, 'RGBA', 1)

    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glBindTexture(GL_TEXTURE_2D, 0)

    return tex, w, h

class Mesh2D:
    def __init__(self, vertices, faces, tex_coords):
        self.vertices   = vertices
        self.faces      = faces
        self.tex_coords = tex_coords

    def draw_textured(self, texture):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture)
        glColor3f(1,1,1)
        for face in self.faces:
            glBegin(GL_QUADS)
            for idx in face:
                u, v = self.tex_coords[idx]
                x, y = self.vertices[idx]
                glTexCoord2f(u, 1 - v)  # flip V if needed
                glVertex2f(x, y)
            glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

def main():
    pg.init()
    W, H = 1024, 768
    ortho_scale = 1.0
    pg.display.set_mode((W, H), DOUBLEBUF | OPENGL)
    glViewport(0, 0, W, H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, W*ortho_scale, H*ortho_scale, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    texture, tex_w, tex_h = load_texture("assets/images/mech1.png")
    verts = [(0,0),(tex_w,0),(tex_w,tex_h),(0,tex_h)]
    uvs   = [(0,0),(1,0),(1,1),(0,1)]
    faces = [(0,1,2,3)]
    mesh  = Mesh2D(verts, faces, uvs)

    clock = pg.time.Clock()
    # state:
    position = [W/2 - tex_w/2, H/2 - tex_h/2]  # start centered
    angle = 0.0                               # facing right
    move_speed = 100.0   # px/sec when W/S
    turn_speed = 300.0   # deg/sec when A/D
    vel = 0.0

    while True:
        dt = clock.tick(60) / 1000.0  # seconds since last frame
        for e in pg.event.get():
            if e.type in (pg.QUIT, pg.KEYDOWN) and getattr(e, 'key', None)==pg.K_ESCAPE:
                pg.quit()
                return

        # input
        keys = pg.key.get_pressed()

        # rotation input
        if keys[pg.K_a]:
            angle -= turn_speed * dt
        if keys[pg.K_d]:
            angle += turn_speed * dt

        if keys[pg.K_q]:
            position[0] += math.cos(math.radians(angle-90)) * move_speed * 10 * dt
            position[1] += math.sin(math.radians(angle-90)) * move_speed * 10 * dt

        if keys[pg.K_e]:
            position[0] -= math.cos(math.radians(angle-90)) * move_speed * 10 * dt
            position[1] -= math.sin(math.radians(angle-90)) * move_speed * 10 * dt

        # forward/back input
        if keys[pg.K_w]:
            vel += move_speed
        if keys[pg.K_s]:
            vel += -move_speed

        if keys[pg.K_UP]:
            ortho_scale += 0.1
            glViewport(0, 0, W, H)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluOrtho2D(0, W * ortho_scale, H * ortho_scale, 0)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

        if keys[pg.K_DOWN]:
            ortho_scale -= 0.1
            glViewport(0, 0, W, H)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluOrtho2D(0, W * ortho_scale, H * ortho_scale, 0)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
        # update position in world‑space
        position[0] += math.cos(math.radians(angle)) * vel * dt
        position[1] += math.sin(math.radians(angle)) * vel * dt

        vel *= 0.99
        # draw
        glClearColor(0.2, 0.2, 0.2, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        glPushMatrix()
        # 1) move to object center in world
        glTranslatef(position[0] + tex_w/2, position[1] + tex_h/2, 0)
        # 2) rotate around its center
        glRotatef(angle, 0, 0, 1)
        # 3) shift back by half‐size so mesh draws at the right spot
        glTranslatef(-tex_w/2, -tex_h/2, 0)

        mesh.draw_textured(texture)
        glPopMatrix()

        pg.display.flip()

if __name__ == '__main__':
    main()

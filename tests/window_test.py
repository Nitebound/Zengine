import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

def main():
    pg.init()
    W, H = 1024, 768
    ortho_scale = 1.0

    pg.display.set_mode((W, H), DOUBLEBUF | OPENGL)

    glViewport(0, 0, W, H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, W*ortho_scale, H*ortho_scale, 0)
    #gluPerspective(45, W*ortho_scale/H*ortho_scale, .01, 10000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    clock = pg.time.Clock()

    while True:
        dt = clock.tick(60) / 1000.0  # seconds since last frame
        for e in pg.event.get():
            if e.type in (pg.QUIT, pg.KEYDOWN) and getattr(e, 'key', None)==pg.K_ESCAPE:
                pg.quit()
                return
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_SPACE:
                    pass
        # input
        keys = pg.key.get_pressed()

        # draw
        glClearColor(.8,.8,.8, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        pg.display.flip()

if __name__ == '__main__':
    main()

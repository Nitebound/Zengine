import numpy as np
import pygame
from zengine.ecs.systems.system import System
from zengine.ecs.components.camera_view import CameraView
from zengine.ecs.components.transform   import Transform

class CameraControllerSystem(System):
    def __init__(self, input_sys, speed: float = 5.0):
        self.input = input_sys
        self.speed = speed

    def on_update(self, dt, em):
        for eid in em.get_entities_with(CameraView, Transform):
            cam = em.get_component(eid, CameraView)
            if not cam.active:
                continue

            tr = em.get_component(eid, Transform)
            d = np.zeros(3, dtype='f4')
            if self.input.is_key_down(pygame.K_d): d[0] += 1
            if self.input.is_key_down(pygame.K_a): d[0] -= 1
            if self.input.is_key_down(pygame.K_w): d[1] += 1
            if self.input.is_key_down(pygame.K_s): d[1] -= 1
            if self.input.is_key_down(pygame.K_q): d[2] += 1
            if self.input.is_key_down(pygame.K_e): d[2] -= 1

            m = np.linalg.norm(d)
            if m > 0:
                delta = (d/m) * self.speed * dt
                tr.x += delta[0]
                tr.y += delta[1]
                tr.z += delta[2]
            break

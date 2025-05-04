import numpy as np
import pygame
from zengine.ecs.systems.system import System
from zengine.ecs.components.camera_view import CameraView
from zengine.ecs.components.transform import Transform

class CameraControllerSystem(System):
    def __init__(self, input_system, speed: float = 5.0):
        self.input = input_system
        self.speed = speed

    def on_update(self, dt, em):
        # Move the first active camera entity
        for eid in em.get_entities_with(CameraView, Transform):
            cam = em.get_component(eid, CameraView)
            if not cam.active:
                continue

            # tr = em.get_component(eid, Transform)
            # direction = np.zeros(3, dtype='f4')
            # keys = self.input
            # if keys.is_down(pygame.K_d): direction[0] += 1
            # if keys.is_down(pygame.K_a): direction[0] -= 1
            # if keys.is_down(pygame.K_w): direction[1] += 1
            # if keys.is_down(pygame.K_s): direction[1] -= 1
            # if keys.is_down(pygame.K_q): direction[2] += 1
            # if keys.is_down(pygame.K_e): direction[2] -= 1

            # norm = np.linalg.norm(direction)
            # if norm > 0:
            #     delta = direction / norm * self.speed * dt
            #     tr.x += delta[0]
            #     tr.y += delta[1]
            #     tr.z += delta[2]
            # break

# zengine/ecs/systems/camera_controller_system.py

import numpy as np
import pygame
from zengine.ecs.systems.system import System
from zengine.ecs.components.camera_view import CameraView
from zengine.ecs.components.transform import Transform

class CameraControllerSystem(System):
    def __init__(self, input_sys, speed: float = 5.0, lock_z: float = 10.0):
        self.input = input_sys
        self.speed = speed
        self.lock_z = lock_z

    def on_update(self, dt, em):
        # Move only X/Y; keep Z locked
        for eid in em.get_entities_with(CameraView, Transform):
            cam = em.get_component(eid, CameraView)
            if not cam.active:
                continue

            tr = em.get_component(eid, Transform)
            dx = self.input.is_key_down(pygame.K_d) - self.input.is_key_down(pygame.K_a)
            dy = self.input.is_key_down(pygame.K_w) - self.input.is_key_down(pygame.K_s)

            if dx or dy:
                # normalize diagonal
                mag = (dx*dx + dy*dy)**0.5
                dx, dy = dx/mag if mag else 0, dy/mag if mag else 0
                tr.x -= dx * self.speed * dt
                tr.y -= dy * self.speed * dt

            # enforce constant height
            tr.z = self.lock_z
            break

import pygame
import numpy as np

from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.system import System
from zengine.ecs.components import PlayerController, Transform
from zengine.util.quaternion import (
    quat_to_forward,
    quat_to_right,
    quat_to_up
)

class PlayerControllerSystem(System):
    def __init__(self, input_system):
        super().__init__()
        self.input = input_system
        self.mouse_sensitivity = 0.2
        self.last_mouse_pos = None
        self.mouse_dragging = False
        self.rotation_speed = 1000  # Degrees per second

    def on_added(self, scene):
        super().on_added(scene)
        self.input = scene.get_system(InputSystem)

    def on_event(self, event):
        pass

    def on_update(self, dt):
        for eid in self.em.get_entities_with(PlayerController, Transform):
            pc = self.em.get_component(eid, PlayerController)
            tr = self.em.get_component(eid, Transform)

            # Movement logic (independent of rotation)
            forward = quat_to_forward(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            right = quat_to_right(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            up = quat_to_up(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            velocity = np.zeros(3, dtype='f4')

            # Handle movement: Arrow keys for translation
            if self.input.is_key_down(pygame.K_w): velocity += up
            if self.input.is_key_down(pygame.K_s): velocity -= up
            if self.input.is_key_down(pygame.K_a): velocity -= right
            if self.input.is_key_down(pygame.K_d): velocity += right

            # Normalize and apply velocity
            if np.linalg.norm(velocity) > 0:
                velocity = velocity / np.linalg.norm(velocity)
                velocity *= pc.speed * dt
                tr.x += velocity[0]
                tr.y += velocity[1]
                tr.z += velocity[2]

                # Ensure no unintended drifting
                tr.x = round(tr.x, 6)
                tr.y = round(tr.y, 6)
                tr.z = round(tr.z, 6)
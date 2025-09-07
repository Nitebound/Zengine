import pygame
import numpy as np

from zengine.ecs.components.physics.rigid_body_2d import RigidBody2D
from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.system import System
from zengine.ecs.components import PlayerController, Transform, TopDownCarController
from zengine.util.quaternion import (
    quat_to_forward,
    quat_to_right,
    quat_to_up
)

class TopDownCarControllerSystem(System):
    def __init__(self, input_system):
        super().__init__()
        self.input = input_system
        self.mouse_sensitivity = 0.2
        self.last_mouse_pos = None
        self.mouse_dragging = False
        self.turn_rate = .1
        self.engine_power = 11

    def on_added(self, scene):
        super().on_added(scene)
        self.input = scene.get_system(InputSystem)

    def on_event(self, event):
        pass

    def on_update(self, dt):
        for eid in self.em.get_entities_with(TopDownCarController, Transform):
            pc = self.em.get_component(eid, TopDownCarController)
            tr = self.em.get_component(eid, Transform)
            rb = self.em.get_component(eid, RigidBody2D)

            # Movement logic (independent of rotation)
            forward = quat_to_forward(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            right = quat_to_right(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            up = quat_to_up(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)

            # Handle movement: Arrow keys for translation
            if self.input.is_key_down(pygame.K_w):
                dx = self.engine_power * up[0] * dt
                dy = self.engine_power * up[1] * dt
                rb.velocity[0] += dx
                rb.velocity[1] += dy

            if self.input.is_key_down(pygame.K_s):
                dx = self.engine_power * up[0] * dt
                dy = self.engine_power * up[1] * dt
                rb.velocity[0] -= dx
                rb.velocity[1] -= dy

            if self.input.is_key_down(pygame.K_a):
                rb.angular_velocity[0] += self.turn_rate

            if self.input.is_key_down(pygame.K_d):
                rb.angular_velocity[0] -= self.turn_rate

            tr.update_quaternion_from_euler()

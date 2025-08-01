import pygame
import numpy as np

from zengine.ecs.components.free_roam_camera_controller import FreeRoamCameraController
from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.system import System
from zengine.ecs.components import PlayerController, Transform
from zengine.util.quaternion import (
    quat_to_forward,
    quat_to_right,
    quat_to_up
)

class FreeRoamCameraControllerSystem(System):
    def __init__(self, input_system):
        super().__init__()
        self.input = input_system
        self.mouse_sensitivity = 0.2
        self.last_mouse_pos = None
        self.mouse_dragging = False

    def on_added(self, scene):
        super().on_added(scene)
        self.input = scene.get_system(InputSystem)
        print("Added FreeRoamCameraController")

    def on_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.mouse_dragging = True
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            self.last_mouse_pos = pygame.mouse.get_pos()
            print("Mouse Dragging")

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            self.mouse_dragging = False
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            self.last_mouse_pos = None
            print("Mouse Released")

    def on_update(self, dt):
        for eid in self.em.get_entities_with(FreeRoamCameraController, Transform):
            pc = self.em.get_component(eid, FreeRoamCameraController)
            tr = self.em.get_component(eid, Transform)

            # Mouse look: Z = yaw, X = pitch
            if self.mouse_dragging:
                mouse_pos = pygame.mouse.get_pos()
                if self.last_mouse_pos is not None:
                    dx = mouse_pos[0] - self.last_mouse_pos[0]
                    dy = mouse_pos[1] - self.last_mouse_pos[1]

                    tr.euler_z -= dx * self.mouse_sensitivity  # Yaw (around Z)
                    tr.euler_x -= dy * self.mouse_sensitivity  # Pitch (around X)
                    tr.euler_x = max(0, min(100, tr.euler_x))  # Clamp

                pygame.mouse.set_pos(self.last_mouse_pos)
                pygame.event.pump()

            tr.update_quaternion_from_euler()

            # Movement based on orientation
            forward = quat_to_forward(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            right   = quat_to_right(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            up      = quat_to_up(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)

            velocity = np.zeros(3, dtype='f4')

            # Forward/back (along Y)
            if self.input.is_key_down(pygame.K_w): velocity += forward
            if self.input.is_key_down(pygame.K_s): velocity -= forward

            # Left/right (along X)
            if self.input.is_key_down(pygame.K_a): velocity -= right
            if self.input.is_key_down(pygame.K_d): velocity += right

            # Depth up/down (along Z)
            if self.input.is_key_down(pygame.K_z): velocity -= up  # toward origin
            if self.input.is_key_down(pygame.K_SPACE):     velocity += up  # away from origin

            # Apply movement
            if np.linalg.norm(velocity) > 0:
                velocity = velocity / np.linalg.norm(velocity)
                velocity *= pc.speed * dt
                tr.x += velocity[0]
                tr.y += velocity[1]
                tr.z += velocity[2]

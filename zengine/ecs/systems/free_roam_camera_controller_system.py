import pygame
import numpy as np

from zengine.ecs.components.camera import ProjectionType
from zengine.ecs.components.free_roam_camera_controller import FreeRoamCameraController
from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.system import System
from zengine.ecs.components import PlayerController, Transform, CameraComponent
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

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                for eid in self.em.get_entities_with(CameraComponent, Transform):
                    pc = self.em.get_component(eid, CameraComponent)
                    tr = self.em.get_component(eid, Transform)

                    if pc.projection is ProjectionType.PERSPECTIVE:
                        pc.projection = ProjectionType.ORTHOGRAPHIC
                        print("Projection changed to Orthographic")
                    else:
                        pc.projection = ProjectionType.PERSPECTIVE
                        print("Projection changed to Perspective")

    def on_update(self, dt):
        for eid in self.em.get_entities_with(FreeRoamCameraController, Transform):
            pc = self.em.get_component(eid, FreeRoamCameraController)
            tr = self.em.get_component(eid, Transform)

            # # Mouse look: Z = yaw, X = pitch
            # if self.mouse_dragging:
            #     mouse_pos = pygame.mouse.get_pos()
            #     if self.last_mouse_pos is not None:
            #         dx = mouse_pos[0] - self.last_mouse_pos[0]
            #         dy = mouse_pos[1] - self.last_mouse_pos[1]
            #
            #         tr.euler_z -= dx * self.mouse_sensitivity  # Yaw
            #         tr.euler_x -= dy * self.mouse_sensitivity  # Pitch
            #         tr.euler_x = max(-89.9, min(89.9, tr.euler_x))  # Clamp pitch
            #
            #     pygame.mouse.set_pos(self.last_mouse_pos)
            #     pygame.event.pump()

            # Update only camera's quaternion
            tr.update_quaternion_from_euler()

            # Handle camera translation independently
            velocity = np.zeros(3, dtype='f4')
            forward = quat_to_forward(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            right = quat_to_right(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)
            up = quat_to_up(tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w)

            if self.input.is_key_down(pygame.K_KP1): velocity += forward
            if self.input.is_key_down(pygame.K_KP3): velocity -= forward
            if self.input.is_key_down(pygame.K_KP4): velocity -= right
            if self.input.is_key_down(pygame.K_KP6): velocity += right
            if self.input.is_key_down(pygame.K_KP5): velocity -= up
            if self.input.is_key_down(pygame.K_KP8): velocity += up

            # Normalize camera velocity and apply it
            if np.linalg.norm(velocity) > 0:
                velocity = velocity / np.linalg.norm(velocity)
                velocity *= pc.speed * dt
                tr.x += velocity[0]
                tr.y += velocity[1]
                tr.z += velocity[2]
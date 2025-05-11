# zengine/ecs/systems/player_controller_system.py

import pygame
from zengine.ecs.systems.system import System
from zengine.ecs.components import PlayerController, Transform

class PlayerControllerSystem(System):
    def __init__(self, input_system):
        super().__init__()
        self.input = input_system

    def on_event(self, event):
        for eid in self.em.get_entities_with(PlayerController):
            pc = self.em.get_component(eid, PlayerController)
            if not pc.active:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    tr = self.em.get_component(eid, Transform)
                    tr.rotation += 10

    def on_update(self, dt):
        for eid in self.em.get_entities_with(PlayerController, Transform):
            pc = self.em.get_component(eid, PlayerController)
            tr = self.em.get_component(eid, Transform)

            # move in X/Y
            vx = (self.input.is_key_down(pygame.K_d) -
                  self.input.is_key_down(pygame.K_a))
            vy = (self.input.is_key_down(pygame.K_s) -
                  self.input.is_key_down(pygame.K_w))

            # move in Z (depth) with Q/E
            vz = (self.input.is_key_down(pygame.K_e) -
                  self.input.is_key_down(pygame.K_q))

            # normalize
            mag = (vx*vx + vy*vy + vz*vz)**0.5
            if mag:
                vx, vy, vz = vx/mag, vy/mag, vz/mag

            tr.x += vx * pc.speed * dt
            tr.y += vy * pc.speed * dt
            tr.z += vz * pc.speed * dt

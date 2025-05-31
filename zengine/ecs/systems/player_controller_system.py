# zengine/ecs/systems/player_controller_system.py

import pygame

from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.system import System
from zengine.ecs.components import PlayerController, Transform


class PlayerControllerSystem(System):
    def __init__(self, input_system):
        super().__init__()
        self.input = input_system

    def on_added(self, scene):
        super().on_added(scene)
        self.input = scene.get_system(InputSystem)

    def on_event(self, event):
        for eid in self.em.get_entities_with(PlayerController):
            pc = self.em.get_component(eid, PlayerController)
            if not pc.active:
                continue

    def on_update(self, dt):
        for eid in self.em.get_entities_with(PlayerController, Transform):
            pc = self.em.get_component(eid, PlayerController)
            tr = self.em.get_component(eid, Transform)

            vx = self.input.get_axis("horizontal")
            vy = self.input.get_axis("vertical")
            vz = self.input.get_axis("depth")
            vr = self.input.get_axis("rotation")
            vr2 = self.input.get_axis("rotation2")

            # normalize
            mag = (vx*vx + vy*vy + vz*vz)**0.5
            if mag:
                vx, vy, vz = vx/mag, vy/mag, vz/mag

            tr.x += vx * pc.speed * dt
            tr.y -= vy * pc.speed * dt
            tr.z += vz * pc.speed * dt
            tr.rotation_x += vr2 * pc.rotation_speed * dt
            tr.rotation_z += vr * pc.rotation_speed * dt
            tr.rotation_y += vx * pc.rotation_speed * dt
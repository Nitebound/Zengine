# zengine/ecs/systems/player_controller_system.py

import pygame
import numpy as np

from zengine.ecs.systems.input_system import InputSystem
from zengine.ecs.systems.system import System
from zengine.ecs.components import PlayerController, Transform
from zengine.util.quaternion import quat_from_euler, quat_mul, normalize_quat


class PlayerControllerSystem(System):
    def __init__(self, input_system):
        super().__init__()
        self.input = input_system

    def on_added(self, scene):
        super().on_added(scene)
        self.input = scene.get_system(InputSystem)

    def on_event(self, event):
        pass  # input handled per-frame

    def on_update(self, dt):
        for eid in self.em.get_entities_with(PlayerController, Transform):
            pc = self.em.get_component(eid, PlayerController)
            tr = self.em.get_component(eid, Transform)

            vx = self.input.get_axis("horizontal")
            vy = self.input.get_axis("vertical")
            vz = self.input.get_axis("depth")
            vr = self.input.get_axis("rotation")
            vr2 = self.input.get_axis("rotation2")

            # Normalize movement vector
            mag = (vx*vx + vy*vy + vz*vz) ** 0.5
            if mag > 0:
                vx, vy, vz = vx/mag, vy/mag, vz/mag

            # 🚀 Apply Translation (World Space)
            tr.x += vx * pc.speed * dt
            tr.y -= vy * pc.speed * dt
            tr.z += vz * pc.speed * dt

            if tr.x < -1:
                tr.x=-1
            # 🚀 Apply Rotation (Local Space - via Quaternion)
            if vr != 0 or vr2 != 0:
                delta_q = quat_from_euler(
                    yaw=vr  * pc.rotation_speed * dt,
                    pitch=0,
                    roll=vr2 * pc.rotation_speed * dt
                )
                current_q = np.array([
                    tr.rotation_x,
                    tr.rotation_y,
                    tr.rotation_z,
                    tr.rotation_w,
                ])
                result_q = quat_mul(current_q, delta_q)
                result_q = normalize_quat(result_q)

                tr.rotation_x, tr.rotation_y, tr.rotation_z, tr.rotation_w = result_q

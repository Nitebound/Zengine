# zengine/ecs/systems/input_system.py

import pygame
from zengine.ecs.systems.system import System

class InputSystem(System):
    def __init__(self):
        super().__init__()
        # persistent state
        self.keys_down     = set()
        self.mouse_down    = set()
        self.mouse_pos     = (0, 0)

        # one‐frame events
        self.keys_pressed  = set()
        self.keys_released = set()
        self.mouse_pressed = set()
        self.mouse_released= set()
        self.mouse_rel     = (0, 0)

        # dragging
        self.dragging      = False
        self.drag_start    = None
        self.drag_current  = None

        self.axes = {
            "horizontal": (pygame.K_d, pygame.K_a),
            "vertical":   (pygame.K_s, pygame.K_w),
            "rotation":      (pygame.K_q, pygame.K_e),
            "depth": (pygame.K_f, pygame.K_g),
            "horizontal2": (pygame.K_RIGHT, pygame.K_LEFT),
            "vertical2":   (pygame.K_DOWN, pygame.K_UP),
            "depth2":      (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET),
            "rotation2":   (pygame.K_z, pygame.K_x),
        }

    def get_axis(self, name):
        if name not in self.axes:
            raise ValueError(f"Unknown axis: {name}")
        pos, neg = self.axes[name]
        return self.is_key_down(pos) - self.is_key_down(neg)

    def on_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.keys_down.add(event.key)
            self.keys_pressed.add(event.key)

        elif event.type == pygame.KEYUP:
            self.keys_down.discard(event.key)
            self.keys_released.add(event.key)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_down.add(event.button)
            self.mouse_pressed.add(event.button)
            self.mouse_pos = event.pos
            self.dragging   = True
            self.drag_start = event.pos
            self.drag_current = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_down.discard(event.button)
            self.mouse_released.add(event.button)
            self.mouse_pos = event.pos
            self.dragging   = False
            self.drag_current = event.pos

        elif event.type == pygame.MOUSEMOTION:
            self.mouse_rel = event.rel
            self.mouse_pos = event.pos

            if self.dragging:
                self.drag_current = event.pos

    def on_update(self, dt):
        # clear one‐frame events
        self.keys_pressed.clear()
        self.keys_released.clear()
        self.mouse_pressed.clear()
        self.mouse_released.clear()
        self.mouse_rel = (0, 0)

    # query methods for other systems:
    def is_key_down(self, key):     return key in self.keys_down
    def is_key_pressed(self, key):  return key in self.keys_pressed
    def is_key_released(self, key): return key in self.keys_released

    def is_mouse_down(self, btn):     return btn in self.mouse_down
    def is_mouse_pressed(self, btn):  return btn in self.mouse_pressed
    def is_mouse_released(self, btn): return btn in self.mouse_released

    def get_mouse_pos(self): return self.mouse_pos
    def get_mouse_rel(self): return self.mouse_rel

    def get_drag_delta(self):
        if self.drag_start and self.drag_current:
            dx = self.drag_current[0] - self.drag_start[0]
            dy = self.drag_current[1] - self.drag_start[1]
            return dx, dy
        return 0, 0

from dataclasses import dataclass

@dataclass
class PlayerController:
    speed: float = 900.0
    rotation_speed: float = 1.0
    active: bool = True
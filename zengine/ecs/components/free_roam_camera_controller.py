from dataclasses import dataclass

@dataclass
class FreeRoamCameraController:
    speed: float = 11.0
    rotation_speed: float = 1.0
    active: bool = True
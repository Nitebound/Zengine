from dataclasses import dataclass

@dataclass
class RigidBody2D:
    mass: float
    velocity: tuple[float, float, float]
    angular_velocity: tuple[float, float, float]

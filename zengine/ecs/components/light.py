# zengine/ecs/components/light.py

from dataclasses import dataclass
from enum import Enum


class LightType(Enum):
    DIRECTIONAL = 0
    POINT       = 1


@dataclass
class LightComponent:
    type: LightType = LightType.DIRECTIONAL
    color: tuple = (1.0, 1.0, 1.0)
    intensity: float = 1.0
    range: float = 10.0  # for point lights
    casts_shadows: bool = False  # for future extension

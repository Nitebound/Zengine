# zengine/ecs/components/light.py

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

class LightType(Enum):
    POINT       = 0
    DIRECTIONAL = 1

@dataclass
class LightComponent:
    type: LightType = LightType.POINT

    # Common light properties
    color:     Tuple[float, float, float] = (1.0, 1.0, 1.0)
    intensity: float                       = 1.0

    # Only used for directional lights
    direction: Tuple[float, float, float] = (0.0, -1.0, 0.0)

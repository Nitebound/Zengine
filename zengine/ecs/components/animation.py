# zengine/ecs/components/animation.py

from dataclasses import dataclass
import numpy as np

@dataclass
class Animation:
    name:    str
    # keyframes, samplers, etc.
    # store as you need for update system

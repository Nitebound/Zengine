# zengine/ecs/components/skeleton.py

from dataclasses import dataclass

@dataclass
class Skeleton:
    root_node: int
    joints:    list[int]

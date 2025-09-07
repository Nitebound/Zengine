# zengine/ecs/components/camera.py

from dataclasses import dataclass
from enum import Enum
import numpy as np


class ProjectionType(Enum):
    ORTHOGRAPHIC       = 1
    PERSPECTIVE = 2


@dataclass
class CameraComponent:
    projection: ProjectionType = ProjectionType.PERSPECTIVE

    # ZERO means “auto”
    left:   float = 0.0
    right:  float = 0.0
    bottom: float = 0.0
    top:    float = 0.0

    near: float = 0.01
    far:  float = 9000.0

    # perspective-only
    fov_deg: float = 60.0
    aspect:  float = 1.0        # you should set this to window.width/window.height in setup
    p_near:  float = 0.01
    p_far:   float = 5000.0

    active: bool             = True
    view_matrix:       np.ndarray = None
    projection_matrix: np.ndarray = None
    vp_matrix:         np.ndarray = None

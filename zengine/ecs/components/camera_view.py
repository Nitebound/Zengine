# zengine/ecs/components/camera_view.py

from dataclasses import dataclass
from enum import Enum

class ProjectionType(Enum):
    ORTHO       = 1
    PERSPECTIVE = 2

@dataclass
class CameraView:
    projection_type: ProjectionType
    # only one of these is non-None:
    # Orthographic params
    left:   float = 0.0
    right:  float = 0.0
    bottom: float = 0.0
    top:    float = 0.0
    near:   float = -1000.0
    far:    float =  1000.0

    # Perspective params
    fov_deg:  float = 60.0
    aspect:   float = 1.0
    p_near:   float = 0.1
    p_far:    float = 1000.0

    active: bool = False

    # these will be filled in by the system
    view_matrix:       any = None
    projection_matrix: any = None
    vp_matrix:         any = None

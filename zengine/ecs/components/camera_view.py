from dataclasses import dataclass
from enum import Enum

class ProjectionType(Enum):
    ORTHO       = 1
    PERSPECTIVE = 2

@dataclass
class CameraView:
    projection_type: ProjectionType
    left:   float = 0.0
    right:  float = 0.0
    bottom: float = 0.0
    top:    float = 0.0
    near:   float = -1000.0
    far:    float =  1000.0

    # perspective params (unused in ORTHO mode)
    fov_deg: float = 60.0
    aspect:  float = 1.0
    p_near:  float = 0.1
    p_far:   float = 1000.0

    active: bool = False

    # filled in at runtime by CameraSystem
    view_matrix:       any = None
    projection_matrix: any = None
    vp_matrix:         any = None

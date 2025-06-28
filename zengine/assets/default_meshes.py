# zengine/assets/default_meshes.py

from zengine.util.mesh_factory import MeshFactory
from zengine.assets.mesh_registry import MeshRegistry

# Register built-in primitives with complete vertex, normal, index, and UV data
MeshRegistry.register(MeshFactory.cube     ("cube",      1.0))
MeshRegistry.register(MeshFactory.sphere   ("sphere",    1.0, 16))
MeshRegistry.register(MeshFactory.plane("plane", 1.0, 1.0))

import numpy as np
from numpy.linalg import inv
from zengine.ecs.systems.system         import System
from zengine.ecs.components.transform   import Transform
from zengine.ecs.components.skinned_mesh import SkinnedMesh
from zengine.ecs.components.skin         import Skin
from zengine.ecs.components.skeleton     import Skeleton
from zengine.ecs.components.camera       import CameraComponent
from zengine.assets.mesh_registry        import MeshRegistry
from zengine.ecs.systems.render_system   import compute_model_matrix

class SkinningSystem(System):
    """
    Computes `Skin.joint_matrices` per-frame so that they
    are *relative* to the mesh node’s local space.
    """
    def on_update(self, dt):
        node_map    = getattr(self.scene, "node_map", {})
        parent_map  = getattr(self.scene, "node_parent", {})

        def compute_world_matrix(node_idx):
            """Climb up the parent chain and compose all local transforms."""
            M = np.eye(4, dtype="f4")
            cur = node_idx
            while cur is not None:
                eid = node_map[cur]
                tr  = self.em.get_component(eid, Transform)
                M_local = compute_model_matrix(tr)
                M = M_local @ M
                cur = parent_map.get(cur, None)
            return M

        # For each skinned‐mesh instance
        for eid in self.em.get_entities_with(Transform, SkinnedMesh, Skin, Skeleton):
            sm   = self.em.get_component(eid, SkinnedMesh)
            skin = self.em.get_component(eid, Skin)
            skel = self.em.get_component(eid, Skeleton)

            # 1) get the mesh‐node’s local transform → M_mesh
            mesh_node_idx = sm.node_index
            mesh_eid      = node_map[mesh_node_idx]
            mesh_tr       = self.em.get_component(mesh_eid, Transform)
            M_mesh        = compute_model_matrix(mesh_tr)

            # 2) invert it so we can bring joint world → mesh-local
            M_inv_mesh    = inv(M_mesh)

            # 3) build jointMatrices array
            joint_mats = []
            for j_idx, ibm in zip(skin.joint_nodes, skin.inverse_bind_matrices):
                # world‐space joint transform
                W = compute_world_matrix(j_idx)
                # bring into mesh local: invMesh * W * invBind
                JM = (M_inv_mesh @ W @ ibm).astype("f4")
                joint_mats.append(JM)

            skin.joint_matrices = np.stack(joint_mats, axis=0)

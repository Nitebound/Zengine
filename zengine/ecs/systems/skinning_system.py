import numpy as np
from numpy.linalg import inv
from zengine.ecs.systems.system       import System
from zengine.ecs.components.transform import Transform
from zengine.ecs.components.skinned_mesh import SkinnedMesh
from zengine.ecs.components.skin         import Skin
from zengine.ecs.components.skeleton     import Skeleton
from zengine.ecs.systems.render_system   import compute_model_matrix

class SkinningSystem(System):
    """
    Compute per-frame joint_matrices for each skinned mesh.
    """
    def on_update(self, dt):
        node_map    = getattr(self.scene, "node_map", {})
        parent_map  = getattr(self.scene, "node_parent", {})

        def world_matrix(node_idx):
            """Compose all local transforms up the parent chain."""
            M = np.eye(4, dtype='f4')
            cur = node_idx
            while cur is not None:
                eid = node_map[cur]
                tr  = self.em.get_component(eid, Transform)
                M = compute_model_matrix(tr) @ M
                cur = parent_map.get(cur, None)
            return M

        for eid in self.em.get_entities_with(Transform, SkinnedMesh, Skin, Skeleton):
            sm   = self.em.get_component(eid, SkinnedMesh)
            skin = self.em.get_component(eid, Skin)

            # mesh-node local
            mesh_idx = sm.node_index
            mesh_eid = node_map[mesh_idx]
            mesh_tr  = self.em.get_component(mesh_eid, Transform)
            M_mesh   = compute_model_matrix(mesh_tr)
            M_inv    = inv(M_mesh)

            # build jointMatrices
            joint_mats = []
            for j_idx, ibm in zip(skin.joint_nodes, skin.inverse_bind_matrices):
                W = world_matrix(j_idx)
                JM = (M_inv @ W @ ibm).astype('f4')
                joint_mats.append(JM)

            skin.joint_matrices = np.stack(joint_mats, axis=0)

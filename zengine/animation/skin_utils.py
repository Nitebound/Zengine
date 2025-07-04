import numpy as np
from scipy.spatial.transform import Rotation as R

def compute_joint_matrices(gltf, skin_asset, pose_overrides=None):
    """
    Computes final skinning transforms for each joint.
    pose_overrides: dict[node_index] = 4x4 matrix to override a joint pose
    """
    # Step 1: Build local transforms
    node_transforms = []
    for i, node in enumerate(gltf.nodes):
        if pose_overrides and i in pose_overrides:
            # Full override of local transform
            local_mat = pose_overrides[i]
        else:
            T = np.eye(4, dtype=np.float32)
            Rm = np.eye(4, dtype=np.float32)
            S = np.eye(4, dtype=np.float32)

            if node.translation:
                T[:3, 3] = node.translation
            if node.rotation:
                r = R.from_quat(node.rotation)
                Rm[:3, :3] = r.as_matrix()
            if node.scale:
                scale = np.diag(node.scale + [1.0])
                S = scale

            local_mat = T @ Rm @ S

        node_transforms.append(local_mat)

    # Step 2: Compute global transforms via hierarchy traversal
    global_transforms = [None] * len(gltf.nodes)

    def traverse(node_idx, parent_matrix):
        local = node_transforms[node_idx]
        global_transforms[node_idx] = parent_matrix @ local

        children = gltf.nodes[node_idx].children or []
        for child in children:
            traverse(child, global_transforms[node_idx])

    # Step 3: Find root nodes (those not referenced as children)
    all_children = set(c for n in gltf.nodes if n.children for c in n.children)
    root_nodes = [i for i in range(len(gltf.nodes)) if i not in all_children]

    for root in root_nodes:
        traverse(root, np.eye(4, dtype=np.float32))

    # # 🛠️ Step 4: Recalculate inverse bind matrices to match pose
    # skin_asset.inverse_bind_matrices = [
    #     np.linalg.inv(global_transforms[joint])
    #     for joint in skin_asset.joint_nodes
    # ]

    # Step 5: Compute final skinning matrices
    final_matrices = []
    for i, (joint_idx, ibm) in enumerate(zip(skin_asset.joint_nodes, skin_asset.inverse_bind_matrices)):
        joint_global = global_transforms[joint_idx]
        joint_matrix = joint_global @ ibm
        final_matrices.append(joint_matrix)

        # # Optional Debug
        # print(f"\n🦴 Joint {i}: Node {joint_idx}")
        # print(f"   → Global:\n{joint_global}")
        # print(f"   → Inverse Bind:\n{ibm}")
        # print(f"   → Final Matrix:\n{joint_matrix}")
        # print(f"   → Determinant: {np.linalg.det(joint_matrix)}")

    return np.array(final_matrices, dtype=np.float32)

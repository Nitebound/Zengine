#version 330 core

in vec3 in_position;
in vec3 in_normal;
in vec3 in_tangent;
in vec2 in_uv;
in vec4 in_joints;
in vec4 in_weights;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 joint_matrices[64];

out vec3 frag_pos;
out vec3 frag_normal;
out vec3 frag_tangent;
out vec2 frag_uv;

mat4 get_skin_matrix() {
    mat4 skin = mat4(0.0);
    for (int i = 0; i < 4; ++i) {
        int joint = int(in_joints[i]);
        if (joint >= 0 && joint < 64)
            skin += joint_matrices[joint] * in_weights[i];
    }
    return skin;
}

void main() {
    // If all weights are zero, skip skinning
    bool apply_skinning = dot(in_weights, vec4(1.0)) > 0.001;
    mat4 skin_mat = apply_skinning ? get_skin_matrix() : mat4(1.0);

    vec4 skinned_pos = skin_mat * vec4(in_position, 1.0);
    vec3 skinned_normal = mat3(skin_mat) * in_normal;
    vec3 skinned_tangent = mat3(skin_mat) * in_tangent;

    vec4 world_pos = model * skinned_pos;

    frag_pos = world_pos.xyz;
    frag_normal = normalize(mat3(model) * skinned_normal);
    frag_tangent = normalize(mat3(model) * skinned_tangent);
    frag_uv = in_uv;

    gl_Position = projection * view * world_pos;
}

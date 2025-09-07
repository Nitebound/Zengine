#version 330 core
// attributes
in vec3 in_position;
in vec3 in_normal;
in vec3 in_tangent;
in vec2 in_uv;
in vec4 in_joints;
in vec4 in_weights;

// matrices / skinning
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 joint_matrices[64];

// varyings
out vec3 frag_pos;
out vec3 frag_normal;
out vec3 frag_tangent;
out vec2 frag_uv;

void main() {
    // ----- Safe 0..4 bone skinning -----
    float wsum = in_weights.x + in_weights.y + in_weights.z + in_weights.w;
    mat4 skin = (wsum > 0.0) ? mat4(0.0) : mat4(1.0);
    if (wsum > 0.0) {
        for (int i = 0; i < 4; ++i) {
            int ji = int(in_joints[i]);
            if (ji >= 0 && ji < 64) {
                skin += joint_matrices[ji] * in_weights[i];
            }
        }
    }

    vec4 skinned_pos     = skin * vec4(in_position, 1.0);
    vec3 skinned_normal  = mat3(skin) * in_normal;
    vec3 skinned_tangent = mat3(skin) * in_tangent;

    vec4 world = model * skinned_pos;

    frag_pos     = world.xyz;
    frag_normal  = normalize(mat3(model) * skinned_normal);
    frag_tangent = normalize(mat3(model) * skinned_tangent);
    frag_uv      = in_uv;

    gl_Position = projection * view * world;
}

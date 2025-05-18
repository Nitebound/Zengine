// assets/shaders/skinning_phong.vert
#version 330 core
#define MAX_JOINTS 64

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;
layout(location = 3) in ivec4 in_joints;
layout(location = 4) in vec4 in_weights;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 jointMatrices[MAX_JOINTS];

out vec3 v_world_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    // 1) Blend the joint transforms
    mat4 skinMat =
          in_weights.x * jointMatrices[in_joints.x] +
          in_weights.y * jointMatrices[in_joints.y] +
          in_weights.z * jointMatrices[in_joints.z] +
          in_weights.w * jointMatrices[in_joints.w];

    // 2) Skin position + normal
    vec4 skinnedPos    = skinMat * vec4(in_position, 1.0);
    vec3 skinnedNormal = mat3(skinMat) * in_normal;

    // 3) To world‐space
    vec4 worldPos = model * skinnedPos;
    v_world_pos   = worldPos.xyz;

    // 4) Proper normal transform
    v_normal = normalize(mat3(transpose(inverse(model))) * skinnedNormal);

    // 5) Pass UV
    v_uv = in_uv;

    // 6) Final clip‐space
    gl_Position = projection * view * worldPos;
}

#version 330 core

in vec3 in_position;
in vec3 in_normal;
in vec3 in_tangent;
in vec2 in_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 frag_pos;
out vec3 frag_normal;
out vec3 frag_tangent;
out vec2 frag_uv;

void main() {
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_pos = world_pos.xyz;

    mat3 normal_mat = transpose(inverse(mat3(model)));
    frag_normal = normalize(normal_mat * in_normal);
    frag_tangent = normalize(mat3(model) * in_tangent);
    frag_uv = in_uv;
    gl_Position = projection * view * world_pos;
}

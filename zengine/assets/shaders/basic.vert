#version 330 core

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 frag_pos;
out vec3 frag_normal;
out vec2 frag_uv;

void main() {
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_pos = world_pos.xyz;

    // Transform normals to world space using full inverse transpose
    frag_normal = normalize(mat3(transpose(inverse(model))) * in_normal);

    frag_uv = in_uv;
    gl_Position = projection * view * world_pos;
}

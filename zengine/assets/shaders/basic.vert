#version 330

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 frag_normal;
out vec2 frag_uv;
out vec3 frag_world;

void main() {
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_world = world_pos.xyz;

    frag_normal = mat3(transpose(inverse(model))) * in_normal;
    frag_uv = in_uv;

    gl_Position = projection * view * world_pos;
}

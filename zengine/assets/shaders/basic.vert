#version 330 core

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 frag_normal;
out vec3 frag_world_pos;
out vec2 frag_uv;

void main() {
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_world_pos = (view * world_pos).xyz;
    frag_normal = mat3(transpose(inverse(view * model))) * in_normal;
    frag_uv = in_uv;
    gl_Position = projection * view * world_pos;
}

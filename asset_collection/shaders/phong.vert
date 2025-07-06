#version 330 core
layout(location=0) in vec3 in_position;
layout(location=1) in vec3 in_normal;
layout(location=2) in vec2 in_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 v_world_pos;
out vec3 v_normal;
out vec2 v_uv;

void main() {
    vec4 world_pos = model * vec4(in_position,1.0);
    v_world_pos    = world_pos.xyz;
    v_normal       = mat3(transpose(inverse(model))) * in_normal;
    v_uv           = in_uv;
    gl_Position    = projection * view * world_pos;
}

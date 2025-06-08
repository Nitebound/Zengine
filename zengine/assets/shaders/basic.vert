#version 330 core

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

//out vec3 FragPos;
//out vec2 TexCoord;

out vec2 frag_uv;
out vec3 frag_normal;
out vec3 frag_world_pos;


void main() {
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_world_pos = world_pos.xyz;
    frag_normal = mat3(transpose(inverse(model))) * in_normal;
    frag_uv = in_uv;
    gl_Position = projection * view * world_pos;
}
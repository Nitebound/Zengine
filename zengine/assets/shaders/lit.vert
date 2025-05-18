#version 330 core
in vec3 in_position;
in vec3 in_normal;

uniform mat4 model;
uniform mat4 view_projection;

out vec3 frag_normal;
out vec3 frag_pos;

void main() {
    vec4 world_pos = model * vec4(in_position,1.0);
    frag_pos    = world_pos.xyz;
    frag_normal = mat3(model) * in_normal; // no non-uniform scale ideally
    gl_Position = view_projection * world_pos;
}

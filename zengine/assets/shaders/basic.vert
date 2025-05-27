#version 330 core
// assets/shaders/universal.vert

// — generic attribute names —
in vec3 in_position;
in vec3 in_normal;   // optional, only used if you light
in vec2 in_uv;

// — standard transforms —
uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

// pass UV (and normal) to frag
out vec2 v_uv;
out vec3 v_normal;

void main() {
    v_uv     = in_uv;
    v_normal = mat3(transpose(inverse(model))) * in_normal;
    gl_Position = projection * view * model * vec4(in_position, 1.0);
}

#version 330

in vec3 in_position;

uniform mat4 model;
uniform mat4 view_projection;

void main() {
    gl_Position = view_projection * model * vec4(in_position, 1.0);
}

#version 330

in vec3 in_position;
in vec3 in_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 frag_normal;

void main() {
    mat4 mv = view * model;
    gl_Position = projection * mv * vec4(in_position, 1.0);
    frag_normal = mat3(transpose(inverse(model))) * in_normal;
}

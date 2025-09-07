#version 330

#if defined(VERTEX_SHADER)
uniform mat4 m_proj;
uniform mat4 m_model;
uniform mat4 m_camera;

in vec3 in_position;

void main() {
    gl_Position = m_proj * m_camera * m_model * vec4(in_position, 1.0);
}
#endif

#if defined(FRAGMENT_SHADER)
uniform vec4 color;

out vec4 f_color;

void main() {
    f_color = color;
}
#endif
#version 330

in vec3 in_position;

uniform mat4 u_Model;
uniform mat4 u_ViewProjection;

void main()
{
    gl_Position = u_ViewProjection * u_Model * vec4(in_position, 1.0);
}

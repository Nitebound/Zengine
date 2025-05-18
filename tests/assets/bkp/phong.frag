// assets/shaders_x/phong.frag
#version 330 core
in vec3 v_world_pos;
in vec3 v_normal;

uniform vec3 light_pos;        // world‐space point light
uniform vec3 view_pos;         // camera world‐space pos
uniform vec3 light_color;      // e.g. vec3(1.0)
uniform vec4 object_color;     // RGBA

uniform float ambient_strength;   // e.g. 0.1
uniform float specular_strength;  // e.g. 0.5
uniform float shininess;          // e.g. 32.0

out vec4 fragColor;

void main() {
    // Ambient
    vec3 ambient = ambient_strength * light_color;

    // Diffuse
    vec3 N = normalize(v_normal);
    vec3 L = normalize(light_pos - v_world_pos);
    float diff = max(dot(N, L), 0.0);
    vec3 diffuse = diff * light_color;

    // Specular
    vec3 V = normalize(view_pos - v_world_pos);
    vec3 R = reflect(-L, N);
    float spec = pow(max(dot(V, R), 0.0), shininess);
    vec3 specular = specular_strength * spec * light_color;

    vec3 lit = ambient + diffuse + specular;
    fragColor = vec4(lit * object_color.rgb, object_color.a);
}

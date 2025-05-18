// assets/shaders/skinning_phong.frag
#version 330 core

in vec3  v_world_pos;
in vec3  v_normal;
in vec2  v_uv;

uniform vec3   light_pos;        // point‐light world position
uniform vec3   view_pos;         // camera world position
uniform vec3   light_color;      // e.g. vec3(1.0)

uniform sampler2D albedo_map;    // your 2D texture
uniform vec4      object_color;  // fallback RGBA

uniform float ambient_strength;
uniform float specular_strength;
uniform float shininess;

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

    vec3 lighting = ambient + diffuse + specular;

    // Texture lookup (will return object_color.rgb if you bind a 1×1 white)
    vec3 base_color = texture(albedo_map, v_uv).rgb * object_color.rgb;

    fragColor = vec4(lighting * base_color, object_color.a);
}

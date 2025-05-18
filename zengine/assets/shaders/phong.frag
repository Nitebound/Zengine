#version 330 core

in  vec3 v_world_pos;
in  vec3 v_normal;
in  vec2 v_uv;

uniform vec3   view_pos;          // camera world position
uniform vec4   object_color;      // fallback albedo
uniform sampler2D albedo_map;     // must always be bound

uniform float  ambient_strength;
uniform float  specular_strength;
uniform float  shininess;

// lights
uniform int    numLights;
uniform int    light_types[8];
uniform vec3   light_positions[8];
uniform vec3   light_directions[8];
uniform vec3   light_colors[8];
uniform float  light_intensities[8];

out vec4 fragColor;

void main() {
    vec3 N = normalize(v_normal);
    vec3 V = normalize(view_pos - v_world_pos);

    // 1) ambient = sum over lights
    vec3 ambient = vec3(0.0);
    for(int i = 0; i < numLights; i++) {
        ambient += ambient_strength * light_colors[i] * light_intensities[i];
    }

    // 2) accumulate diffuse + specular
    vec3 diff_acc = vec3(0.0);
    vec3 spec_acc = vec3(0.0);

    for(int i = 0; i < numLights; i++) {
        vec3 L;
        if(light_types[i] == 0) {
            // POINT
            L = normalize(light_positions[i] - v_world_pos);
        } else {
            // DIRECTIONAL
            L = normalize(-light_directions[i]);
        }

        float diff = max(dot(N, L), 0.0);
        diff_acc += diff * light_colors[i] * light_intensities[i];

        vec3 R = reflect(-L, N);
        float spec = pow(max(dot(V, R), 0.0), shininess);
        spec_acc += specular_strength * spec * light_colors[i] * light_intensities[i];
    }

    vec3 lighting = ambient + diff_acc + spec_acc;

    // 3) sample texture for base color
    vec3 base_color = texture(albedo_map, v_uv).rgb;

    fragColor = vec4(lighting * base_color, object_color.a);
}

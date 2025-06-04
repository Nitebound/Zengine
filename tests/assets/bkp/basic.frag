#version 330

// Light types
#define LIGHT_DIRECTIONAL 0
#define LIGHT_POINT       1

in vec3 frag_position;
in vec3 frag_normal;
in vec2 frag_uv;

out vec4 fragColor;

// MATERIAL UNIFORMS
uniform vec4 albedo;
uniform float metallic;
uniform float smoothness;
uniform float emission_intensity;
uniform vec4 emission_color;

uniform bool useTexture;
uniform bool useLighting;

// TEXTURES
uniform sampler2D main_texture;

// LIGHT DATA
uniform int   light_count;
uniform vec3  light_position[16];
uniform vec3  light_color[16];
uniform float light_intensity[16];
uniform int   light_type[16]; // 0 = directional, 1 = point

void main() {
    vec3 base_color = albedo.rgb;
    if (useTexture) {
        base_color *= texture(main_texture, frag_uv).rgb;
    }

    vec3 normal = normalize(frag_normal);
    vec3 final_color = vec3(0.0);

    if (useLighting) {
        for (int i = 0; i < light_count; ++i) {
            vec3 light_dir;
            if (light_type[i] == LIGHT_DIRECTIONAL) {
                light_dir = normalize(-light_position[i]); // Directional light
            } else {
                light_dir = normalize(light_position[i] - frag_position); // Point light
            }

            float diff = max(dot(normal, light_dir), 0.0);
            final_color += diff * light_color[i] * light_intensity[i];
        }

        // Add ambient term
        final_color += vec3(0.1); // constant ambient
        fragColor = vec4(base_color * final_color, albedo.a);
    } else {
        fragColor = vec4(base_color, albedo.a);
    }

    // Emission is always added on top
    fragColor.rgb += emission_color.rgb * emission_intensity;
}

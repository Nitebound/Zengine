#version 330 core

in vec3 frag_pos;
in vec3 frag_normal;
in vec3 frag_tangent;
in vec2 frag_uv;

out vec4 frag_color;

uniform sampler2D albedo_texture;
uniform sampler2D normal_map;

uniform bool u_has_albedo_map;
uniform bool u_has_normal_map;

uniform vec4 albedo;
uniform vec3 u_ambient_color;

uniform int   light_count;
uniform vec3  light_position[8];
uniform vec3  light_color[8];
uniform float light_intensity[8];
uniform float light_range[8];

void main() {
    // Flip UV Y (GLTF vs OpenGL convention)
    vec2 uv = vec2(frag_uv.x, 1.0 - frag_uv.y);

    // Base color
    vec4 base_color = u_has_albedo_map ? texture(albedo_texture, uv) : albedo;

    // Compute normal
    vec3 normal = normalize(frag_normal);

    if (u_has_normal_map && length(frag_tangent) > 0.0) {
        vec3 T = normalize(frag_tangent);
        vec3 N = normalize(frag_normal);
        vec3 B = normalize(cross(N, T));
        mat3 TBN = mat3(T, B, N);

        vec3 n = texture(normal_map, uv).rgb;
        n = normalize(n * 2.0 - 1.0); // unpack
        normal = normalize(TBN * n);
    }

    // Basic Lambert lighting with attenuation
    vec3 lighting = u_ambient_color;

    for (int i = 0; i < light_count; ++i) {
        vec3 to_light = light_position[i] - frag_pos;
        float dist = length(to_light);
        vec3 L = to_light / dist;

        float diff = max(dot(normal, L), 0.0);

        float attenuation = 1.0 / (1.0 + 0.22 * dist + 0.20 * dist * dist);
        attenuation *= clamp(1.0 - (dist / light_range[i]), 0.0, 1.0);

        vec3 contrib = light_color[i] * light_intensity[i] * diff * attenuation;
        lighting += contrib;
    }

    vec3 final_rgb = base_color.rgb * lighting;
    frag_color = vec4(final_rgb, base_color.a);
}

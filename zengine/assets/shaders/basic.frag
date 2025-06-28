#version 330 core

in vec3 frag_pos;
in vec3 frag_normal;
in vec3 frag_tangent;
in vec2 frag_uv;

uniform sampler2D albedo_texture;
uniform sampler2D normal_map;

uniform vec3 u_ambient_color;

uniform int   light_count;
uniform vec3  light_position[8];
uniform vec3  light_color[8];
uniform float light_intensity[8];
uniform float light_range[8];
out vec4 frag_color;

uniform vec4 albedo;
uniform bool u_has_albedo_map;
uniform bool u_has_normal_map;

vec4 get_albedo(vec2 uv) {
    return u_has_albedo_map ? texture(albedo_texture, uv) : albedo;
}


void main() {
    // Base shading normal
    vec3 N = normalize(frag_normal);
    vec3 T = normalize(frag_tangent);
    vec3 B = normalize(cross(N, T));
    mat3 TBN = mat3(T, B, N);

    vec3 normal = N;

    if (u_has_normal_map) {
        vec3 n_map = texture(normal_map, frag_uv).rgb;
        n_map = normalize(n_map * 2.0 - 1.0);
        normal = normalize(TBN * n_map);
    }

    vec4 base_color = get_albedo(frag_uv);
    vec3 lighting = u_ambient_color;

    for (int i = 0; i < light_count; ++i) {
        vec3 to_light = light_position[i] - frag_pos;
        float dist = length(to_light);
        vec3 light_dir = to_light / dist;

        float diff = max(dot(normal, light_dir), 0.0); // <- must use that `normal`
        float attenuation = 1.0 / (1.0 + 0.22 * dist + 0.20 * dist * dist);
        attenuation *= clamp(1.0 - (dist / light_range[i]), 0.0, 1.0);
        vec3 contribution = light_color[i] * light_intensity[i] * diff * attenuation;
        lighting += contribution;
    }

    vec3 final_color = base_color.rgb * lighting;
    frag_color = vec4(final_color, base_color.a);
}

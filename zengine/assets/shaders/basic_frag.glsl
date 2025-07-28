#version 330 core

in vec3 frag_pos;
in vec3 frag_normal;
in vec3 frag_tangent; // Still included, though not used in this basic lighting
in vec2 frag_uv;      // Still included, though not used in this basic lighting

out vec4 frag_color;

uniform sampler2D albedo_texture; // Still included, for future texture use
uniform sampler2D normal_map;     // Still included, for future normal map use

uniform bool u_has_albedo_map;    // Still included
uniform bool u_has_normal_map;    // Still included

uniform vec4 albedo;
uniform vec3 u_ambient_color; // Global ambient light color

uniform int   light_count;
uniform vec3  light_position[8];
uniform vec3  light_color[8];
uniform float light_intensity[8];
uniform float light_range[8];

uniform float smoothness; // For specular shininess (from Material)
uniform float metallic;   // Not used in this basic Phong, but kept as per Material

uniform vec3 camera_position; // Crucial for specular highlights

void main() {
    // Note: UV flipping and normal mapping logic are kept from your original
    // basic_frag.glsl, but for a simple cube with no textures, they won't have
    // a visible effect.
    vec2 uv = vec2(frag_uv.x, 1.0 - frag_uv.y);
    vec4 base_color = u_has_albedo_map ? texture(albedo_texture, uv) : albedo;

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

    // Start with global ambient light
    vec3 lighting_accum = u_ambient_color;

    for (int i = 0; i < light_count; ++i) {
        vec3 to_light = light_position[i] - frag_pos;
        float dist = length(to_light);
        vec3 L = to_light / dist; // Normalized light direction

        // Attenuation (your original quadratic attenuation + range falloff)
        float attenuation = 1.0 / (1.0 + 0.22 * dist + 0.20 * dist * dist);
        attenuation *= clamp(1.0 - (dist / light_range[i]), 0.0, 1.0);

        // Diffuse component (Lambertian)
        float diff = max(dot(normal, L), 0.0);
        vec3 diffuse_contrib = light_color[i] * light_intensity[i] * diff * attenuation;

        // Specular component (Phong-like)
        vec3 view_dir = normalize(camera_position - frag_pos); // Direction from fragment to camera
        vec3 reflect_dir = reflect(-L, normal); // Reflected light direction
        float spec = pow(max(dot(view_dir, reflect_dir), 0.0), smoothness * 128.0); // Shininess controlled by smoothness
        vec3 specular_contrib = light_color[i] * light_intensity[i] * spec * attenuation;

        lighting_accum += diffuse_contrib + specular_contrib;
    }

    vec3 final_rgb = base_color.rgb * lighting_accum;
    frag_color = vec4(final_rgb, base_color.a);
}

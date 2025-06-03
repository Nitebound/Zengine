#version 330 core

in vec3 frag_pos;
in vec3 frag_normal;
in vec2 frag_uv;

out vec4 out_color;

uniform vec4 albedo;
uniform bool useTexture;
uniform bool useLighting;
uniform sampler2D main_texture;

uniform vec4 emission_color;
uniform float emission_intensity;

void main() {
    vec4 base_color = albedo;

    if (useTexture) {
        base_color *= texture(main_texture, frag_uv);
    }

    vec3 normal = normalize(frag_normal);
    vec3 light_dir = normalize(vec3(0.4, 1.0, 0.5));
    float diff = max(dot(normal, light_dir), 0.0);

    vec3 final_rgb = base_color.rgb;

    if (useLighting) {
        final_rgb *= diff;
    }

    // Apply emissive glow
    final_rgb += emission_color.rgb * emission_intensity;

    out_color = vec4(final_rgb, base_color.a);
}

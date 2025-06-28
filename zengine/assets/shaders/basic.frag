#version 330 core

in vec3 frag_pos;
in vec3 frag_normal;
in vec2 frag_uv;

uniform sampler2D main_texture;
uniform vec3 u_ambient_color;

uniform int   light_count;
uniform vec3  light_position[8];
uniform vec3  light_color[8];
uniform float light_intensity[8];

out vec4 frag_color;

void main() {
    // Hard-reference uniform arrays to ensure GLSL compiler retains them
vec3 _keep0 = light_position[0] + light_color[0] * light_intensity[0];
vec3 _keep1 = light_position[1] + light_color[1] * light_intensity[1];

    vec3 normal = normalize(frag_normal);
    vec3 base_color = texture(main_texture, frag_uv).rgb;

    // Force use of uniforms by making them directly influence final output
    vec3 debug_light = light_position[0] * 0.0001 + light_color[0] * 0.0001 + light_intensity[0] * 0.0001;
    base_color += debug_light;  // Has minimal visual effect but ensures GPU keeps the uniforms

    vec3 lighting = u_ambient_color;

    for (int i = 0; i < light_count; ++i) {
        vec3 to_light = light_position[i] - frag_pos;
        float dist = length(to_light);
        vec3 light_dir = to_light / dist;

        float diff = max(dot(normal, light_dir), 0.0);
        float attenuation = 1.0 / (1.0 + 0.22 * dist + 0.20 * dist * dist);

        vec3 contribution = light_color[i] * light_intensity[i] * diff * attenuation;
        lighting += contribution;
    }

    vec3 final_color = base_color * lighting;
    frag_color = vec4(final_color, 1.0);
}

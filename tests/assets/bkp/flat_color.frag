#version 330

uniform vec4 color;
out vec4 fragColor;

void main() {
    vec3 normal = normalize(frag_normal);
    vec3 base_color = albedo.rgb;
    vec3 final_color = vec3(0.0);

    if (useLighting) {
        for (int i = 0; i < light_count; ++i) {
            vec3 light_dir = normalize(light_position[i] - frag_position);
            float diff = max(dot(normal, light_dir), 0.0);
            final_color += diff * light_color[i] * light_intensity[i];
        }
        // Add ambient
        final_color += vec3(0.1);
        fragColor = vec4(base_color * final_color, albedo.a);
    } else {
        fragColor = vec4(base_color, albedo.a);
    }
}

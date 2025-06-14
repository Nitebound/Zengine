#version 330 core

uniform vec3 camera_position;

uniform int light_count;
uniform int light_type[8];
uniform vec3 light_position[8];
uniform vec3 light_color[8];
uniform float light_intensity[8];

uniform vec4 albedo;
uniform float emission_intensity;
uniform vec4 emission_color;
uniform sampler2D main_texture;
uniform bool useTexture;
uniform bool useLighting;
uniform vec3 u_ambient_color;

in vec2 frag_uv;
in vec3 frag_normal;
in vec3 frag_world_pos;

out vec4 frag_color;

void main() {
    vec4 tex_color = useTexture ? texture(main_texture, frag_uv) : vec4(1.0);
    vec3 base_color = tex_color.rgb * albedo.rgb;

    vec3 normal = normalize(frag_normal);
    vec3 color = vec3(0.0);

    if (useLighting) {
        color += base_color * u_ambient_color;

        for (int i = 0; i < light_count; ++i) {
            vec3 light_dir;
            float attenuation = 1.0;

            if (light_type[i] == 1) {
                vec3 to_light = light_position[i] - frag_world_pos;
                float dist = length(to_light);
                light_dir = normalize(to_light);
                attenuation = 1.0 / (dist * dist + 0.01);
            } else {
                light_dir = normalize(-light_position[i]);
            }

            float diff = max(dot(normal, light_dir), 0.0);
            vec3 diffuse = diff * light_color[i] * light_intensity[i] * attenuation;
            color += base_color * diffuse;
        }
    } else {
        color = base_color;
    }

    color += emission_color.rgb * emission_intensity;
    frag_color = vec4(color, albedo.a);
}

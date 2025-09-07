#version 330 core
in vec3 frag_pos;
in vec3 frag_normal;
in vec3 frag_tangent;
in vec2 frag_uv;

out vec4 frag_color;

// textures
uniform sampler2D albedo_texture;
uniform sampler2D normal_map;

// flags
uniform bool u_has_albedo_map;
uniform bool u_has_normal_map;

// material
uniform vec4  albedo;
uniform float smoothness;          // 0..1

// ambient + camera
uniform vec3 u_ambient_color;
uniform vec3 camera_position;

// lights (keep names you already use)
#define MAX_LIGHTS 16
uniform int   light_count;
uniform vec3  light_position[MAX_LIGHTS];
uniform vec3  light_color[MAX_LIGHTS];
uniform float light_intensity[MAX_LIGHTS];
uniform float light_range[MAX_LIGHTS];

vec3 apply_normal_map(vec3 N, vec3 T) {
    vec3 n = normalize(N);
    vec3 t = normalize(T - n * dot(T, n));
    vec3 b = normalize(cross(n, t));
    vec3 nn = texture(normal_map, frag_uv).xyz * 2.0 - 1.0;
    return normalize(mat3(t, b, n) * nn);
}

void main() {
    // base color (preserve alpha)
    vec4 base = u_has_albedo_map ? texture(albedo_texture, frag_uv) : albedo;

    // DO NOT write depth for invisible pixels
    if (base.a <= 0.001) discard;

    // normal selection
    vec3 N = normalize(frag_normal);
    if (u_has_normal_map) {
        N = apply_normal_map(N, frag_tangent);
    }

    // simple Blinn-Phong + soft distance attenuation
    vec3 V = normalize(camera_position - frag_pos);
    float shininess = mix(8.0, 128.0, clamp(smoothness, 0.0, 1.0));

    vec3 lighting = u_ambient_color;

    int count = min(light_count, MAX_LIGHTS);
    for (int i = 0; i < count; ++i) {
        vec3  Ldir = light_position[i] - frag_pos;
        float dist = length(Ldir);
        vec3  L    = (dist > 0.0) ? Ldir / dist : vec3(0.0, 0.0, 1.0);

        float r = max(light_range[i], 0.0001);
        float att = clamp(1.0 - (dist / r), 0.0, 1.0);
        att *= att;

        float ndl = max(dot(N, L), 0.0);
        vec3  diffuse  = light_color[i] * light_intensity[i] * ndl;

        vec3  H = normalize(L + V);
        float ndh = max(dot(N, H), 0.0);
        float spec = pow(ndh, shininess);
        vec3  specular = light_color[i] * light_intensity[i] * spec;

        lighting += (diffuse + specular) * att;
    }

    frag_color = vec4(base.rgb * lighting, base.a);
}

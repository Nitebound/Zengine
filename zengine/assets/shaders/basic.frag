// assets/shaders/universal.frag
#version 330 core

in vec2 v_uv;
in vec3 v_normal;

// your single texture sampler
uniform sampler2D albedo;

// simple toggles
uniform bool  useTexture;   // if false, we’ll just tint by baseColor
uniform bool  useLighting;  // if false, we skip the diffuse lighting

// material fields
uniform vec4 baseColor;        // fallback color when no texture
uniform vec3 lightDirection;   // world-space dir TO the light
uniform vec4 ambientColor;     // rgb×alpha for ambient term

out vec4 frag_color;

void main() {
    // 1) fetch your color
    vec3 color = useTexture
        ? texture(albedo, v_uv).rgb
        : baseColor.rgb;

    // 2) apply one‐bounce diffuse (Lambert)
    if (useLighting) {
        vec3 N = normalize(v_normal);
        vec3 L = normalize(-lightDirection);
        float d = max(dot(N, L), 0.0);
        vec3 diff = d * color;
        vec3 amb  = ambientColor.rgb * ambientColor.a;
        color = amb + diff;
    }

    frag_color = vec4(color, useTexture ? texture(albedo, v_uv).a : baseColor.a);
}

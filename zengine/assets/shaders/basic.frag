#version 330

in vec3 frag_normal;
in vec2 frag_uv;
in vec3 frag_world;

uniform sampler2D albedoMap;
uniform vec4 baseColor;
uniform bool useTexture;
uniform bool useLighting;

out vec4 fragColor;

void main() {
    vec4 color = baseColor;

    if (useTexture)
        color *= texture(albedoMap, frag_uv);

    // Optional simple lighting
    if (useLighting) {
        vec3 lightDir = normalize(vec3(1.3, 1.0, 0.2));
        float diff = max(dot(normalize(frag_normal), lightDir), 0.0);
        color.rgb *= diff;
    }

    fragColor = color;
}

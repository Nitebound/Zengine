#version 330

in vec3 frag_normal;

uniform bool useTexture;
uniform bool useLighting;
uniform vec4 baseColor;

out vec4 fragColor;

void main() {
    vec3 light_dir = normalize(vec3(1.0, 1.0, 1.0));
    float diff = useLighting ? max(dot(normalize(frag_normal), light_dir), 0.0) : 1.0;
    fragColor = baseColor * diff;
}

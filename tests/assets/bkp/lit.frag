#version 330 core
in vec3 frag_normal;
in vec3 frag_pos;

uniform vec3 light_dir;
uniform vec4 base_color;

out vec4 fColor;

void main(){
    // simple Lambert
    vec3 N = normalize(frag_normal);
    vec3 L = normalize(light_dir);
    float diff = max(dot(N, L), 0.0);
    vec3 col  = base_color.rgb * diff + base_color.rgb * .001;
    fColor = vec4(col, base_color.a);
}

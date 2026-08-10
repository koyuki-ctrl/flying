#version 330

in vec2 fragTexCoord;
in vec4 fragColor;
in vec3 fragPosition;
in vec3 fragNormal;

uniform float time;

out vec4 finalColor;

vec3 water_color(float level) {
    if (level < 0.20) return vec3(0.02, 0.08, 0.25);
    if (level < 0.40) return vec3(0.05, 0.20, 0.45);
    if (level < 0.60) return vec3(0.10, 0.35, 0.60);
    if (level < 0.80) return vec3(0.25, 0.55, 0.80);
    return vec3(0.50, 0.80, 0.95);
}

void main() {
    float h = fragPosition.y;

    float micro = sin(fragPosition.x * 8.0 + time * 3.0) * 0.02
                + sin(fragPosition.z * 6.0 + time * 2.5) * 0.02;
    h += micro;

    float t = clamp((h + 0.4) / 0.8, 0.0, 1.0);

    float bands = 5.0;
    float cel = floor(t * bands) / bands;

    vec3 color = water_color(cel);

    float crest = smoothstep(0.35, 0.42, h);
    color = mix(color, vec3(0.8, 0.95, 1.0), crest * 0.7);

    float reflect = sin(fragPosition.x * 3.0 + time)
                  * sin(fragPosition.z * 2.0 - time * 0.5);
    if (reflect > 0.85 && h > 0.05) {
        color = mix(color, vec3(0.9, 0.98, 1.0), 0.4);
    }

    float edge = step(0.92, fract(t * bands));
    color = mix(color, color * 0.6, edge * 0.4);

    finalColor = vec4(color, 1.0);
}

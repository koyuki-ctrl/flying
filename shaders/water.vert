#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;
in vec4 vertexColor;

uniform mat4 mvp;
uniform float time;

out vec2 fragTexCoord;
out vec4 fragColor;
out vec3 fragPosition;
out vec3 fragNormal;

void main() {
    vec3 pos = vertexPosition;

    // Vagues douces et amples, plus "lisses" que réaliste (look stylisé)
    float wave1 = sin(pos.x * 0.35 + time * 0.8) * 0.10;
    float wave2 = sin(pos.z * 0.30 + time * 0.55) * 0.10;
    float wave3 = sin((pos.x + pos.z) * 0.5 + time * 0.9) * 0.03;
    pos.y += wave1 + wave2 + wave3;

    // Normale approximée pour l'éclairage / fresnel du fragment shader
    float dx = cos(pos.x * 0.35 + time * 0.8) * 0.035;
    float dz = cos(pos.z * 0.30 + time * 0.55) * 0.03;
    vec3 newNormal = normalize(vec3(-dx, 1.0, -dz));

    fragTexCoord = vertexTexCoord;
    fragColor    = vertexColor;
    fragPosition = pos;
    fragNormal   = newNormal;

    gl_Position = mvp * vec4(pos, 1.0);
}

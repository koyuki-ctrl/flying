#version 330

in vec2 fragTexCoord;
in vec4 fragColor;
in vec3 fragNormal;
in vec3 fragPosition;

uniform sampler2D texture0;
uniform vec4 colDiffuse;

uniform vec3 lightDir;
uniform vec3 lightColor;
uniform vec3 ambientColor;
uniform float levels;

uniform vec3 groundColor;
uniform float groundHeight;

uniform vec3 detailColor;
uniform float noiseScale;
uniform float noiseStrength;

out vec4 finalColor;

float hash2(vec2 p)
{
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main()
{
    vec4 texelColor = texture(texture0, fragTexCoord);
    vec3 normal = normalize(fragNormal);
    float facingUp = dot(normal, vec3(0.0, 1.0, 0.0));

    // Sol = Y bas ET face vers le haut (plateau uniquement)
    float isGround = 0.0;
    if (fragPosition.y < groundHeight && facingUp > 0.95) {
        isGround = 1.0;
    }

    vec3 baseColor;
    if (isGround > 0.5) {
        // Sol : couleur perso + bruit
        baseColor = groundColor;
        vec2 cell = floor(fragPosition.xz * noiseScale);
        float n = hash2(cell);
        float blend = n * noiseStrength;
        baseColor = mix(baseColor, detailColor, blend);
    } else {
        // Objets : couleur normale
        baseColor = texelColor.rgb * colDiffuse.rgb * fragColor.rgb;
    }

    // Cel-shading
    vec3 toLight = normalize(-lightDir);
    float diff = max(dot(normal, toLight), 0.0);
    float quantized = floor(diff * levels) / max(levels - 1.0, 1.0);
    quantized = clamp(quantized, 0.0, 1.0);
    vec3 litColor = mix(ambientColor, lightColor, quantized);

    vec3 result = baseColor * litColor;
    finalColor = vec4(result, texelColor.a * colDiffuse.a * fragColor.a);
}
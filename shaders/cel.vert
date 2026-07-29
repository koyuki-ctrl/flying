#version 330

// Attributs d'entrée (fournis automatiquement par raylib)
in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;
in vec4 vertexColor;

// Uniforms fournis automatiquement par raylib
uniform mat4 mvp;
uniform mat4 matModel;
uniform mat4 matNormal;

// Sorties vers le fragment shader
out vec2 fragTexCoord;
out vec4 fragColor;
out vec3 fragNormal;
out vec3 fragPosition;

void main()
{
    fragTexCoord = vertexTexCoord;
    fragColor = vertexColor;

    // Normale et position en espace monde (pour l'éclairage)
    fragNormal = normalize(vec3(matNormal * vec4(vertexNormal, 1.0)));
    fragPosition = vec3(matModel * vec4(vertexPosition, 1.0));

    gl_Position = mvp * vec4(vertexPosition, 1.0);
}

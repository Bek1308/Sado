#version 460 core

// Sado's living sphere: a ray-marched ball whose surface ripples with the
// voice it hears or speaks, lit like glass with a soft glow around it.

#include <flutter/runtime_effect.glsl>

uniform vec2 uSize;
uniform float uTime;
// How loud the voice is right now, 0 to 1.
uniform float uLevel;
// 0 while listening (Sado's blue), 1 while speaking (violet).
uniform float uMood;
// 0 to 1 while Sado is thinking: the colour bands start to swirl.
uniform float uThink;

out vec4 fragColor;

float hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x),
            mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
        mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x),
            mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y),
        f.z);
}

float surface(vec3 p) {
    float t = uTime;
    // Nearly round at rest; the voice raises soft waves, never sharp lumps.
    float ripple = 0.025 + 0.2 * uLevel;
    float n = noise(p * 1.6 + vec3(0.0, t * 0.6, t * 0.35)) * 2.0 - 1.0;
    n += (noise(p * 3.2 - vec3(t * 0.8)) * 2.0 - 1.0) * 0.35;
    return length(p) - 1.0 - ripple * n;
}

vec3 normalAt(vec3 p) {
    vec2 e = vec2(0.003, 0.0);
    return normalize(vec3(
        surface(p + e.xyy) - surface(p - e.xyy),
        surface(p + e.yxy) - surface(p - e.yxy),
        surface(p + e.yyx) - surface(p - e.yyx)));
}

void main() {
    vec2 uv = (FlutterFragCoord().xy - 0.5 * uSize) / min(uSize.x, uSize.y) * 2.0;
    uv.y = -uv.y;

    vec3 origin = vec3(0.0, 0.0, 3.4);
    // The ball fills about two thirds of the square, leaving room for its glow.
    vec3 ray = normalize(vec3(uv, -2.1));
    float angle = uTime * 0.3;
    mat2 turn = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));

    float travelled = 0.0;
    bool hit = false;
    vec3 p = origin;
    for (int i = 0; i < 48; i++) {
        p = origin + ray * travelled;
        p.xz = turn * p.xz;
        float d = surface(p);
        if (d < 0.002) {
            hit = true;
            break;
        }
        travelled += d * 0.8;
        if (travelled > 6.0) {
            break;
        }
    }

    vec3 blue = vec3(0.0, 0.51, 0.98);
    vec3 deep = vec3(0.0, 0.25, 0.70);
    vec3 violet = vec3(0.48, 0.25, 0.95);
    vec3 cyan = vec3(0.25, 0.85, 1.0);
    vec3 tone = mix(blue, violet, uMood);

    vec3 colour = vec3(0.0);
    float alpha = 0.0;
    if (hit) {
        vec3 n = normalAt(p);
        vec3 light = normalize(vec3(-0.5, 0.8, 0.6));
        float diffuse = max(dot(n, light), 0.0);
        float rim = pow(1.0 - max(dot(n, -ray), 0.0), 3.0);
        float bands = 0.5 + 0.5 * sin(dot(p, vec3(3.0, 2.0, 1.5)) * 2.0
            + uTime * (1.5 + 4.0 * uThink));
        // Sado's blue at the top fading to violet below, like its logo.
        vec3 body = mix(violet, tone, smoothstep(-0.8, 0.9, n.y));
        colour = mix(deep, body, 0.35 + 0.65 * diffuse)
            + mix(tone, violet, bands) * 0.18 * bands
            + rim * mix(cyan, violet, 0.35) * 0.6
            + pow(max(dot(reflect(-light, n), -ray), 0.0), 40.0) * 0.45;
        alpha = 1.0;
    }

    // A round halo that hugs the ball and is gone well before the square's
    // edges, so no frame ever shows around it.
    float edge = length(uv);
    float glow = exp(-max(edge - 0.6, 0.0) * 7.0) * (0.35 + 0.65 * uLevel)
        * (1.0 - smoothstep(0.75, 0.98, edge));
    colour += tone * glow * (1.0 - alpha);
    alpha = max(alpha, clamp(glow, 0.0, 1.0));
    fragColor = vec4(colour * alpha, alpha);
}

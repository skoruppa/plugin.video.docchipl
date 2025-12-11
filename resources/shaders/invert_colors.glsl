#version 130

uniform sampler2D m_samp0;
varying vec2 m_cord0;

void main()
{
    vec4 rgb = texture2D(m_samp0, m_cord0);
    rgb.rgb = vec3(1.0) - rgb.rgb;
    gl_FragColor = rgb;
}
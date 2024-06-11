Shader "Custom/OverlayTexturesPBR"
{
    Properties
    {
        _BaseTex("Base Texture", 2D) = "white" {}
        _OverlayTex("Overlay Texture", 2D) = "white" {}
        _NormalMap("Normal Map", 2D) = "bump" {}
        _Metallic("Metallic", Range(0.0, 1.0)) = 0.0
        _Smoothness("Smoothness", Range(0.0, 1.0)) = 0.5
        _Brightness("Brightness", Range(0.0, 2.0)) = 1.0
    }
        SubShader
        {
            Tags { "RenderType" = "Opaque" }
            LOD 200

            CGPROGRAM
            #pragma surface surf Standard fullforwardshadows

            sampler2D _BaseTex;
            sampler2D _OverlayTex;
            sampler2D _NormalMap;
            float _Metallic;
            float _Smoothness;
            float _Brightness;

            struct Input
            {
                float2 uv_BaseTex;
                float2 uv_OverlayTex;
                float2 uv_NormalMap;
            };

            void surf(Input IN, inout SurfaceOutputStandard o)
            {
                fixed4 baseTex = tex2D(_BaseTex, IN.uv_BaseTex);
                fixed4 overlayTex = tex2D(_OverlayTex, IN.uv_OverlayTex);

                fixed4 combinedTex = lerp(baseTex, overlayTex, overlayTex.a);
                combinedTex.rgb *= _Brightness;

                o.Albedo = combinedTex.rgb;
                o.Alpha = combinedTex.a;

                // Normal mapping
                fixed4 normalTex = tex2D(_NormalMap, IN.uv_NormalMap);
                o.Normal = UnpackNormal(normalTex);

                // Metallic and smoothness
                o.Metallic = _Metallic;
                o.Smoothness = _Smoothness;
            }
            ENDCG
        }
            FallBack "Diffuse"
}

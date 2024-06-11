Shader "Custom/OverlayTextures"
{
    Properties
    {
        _BaseTex("Base Texture", 2D) = "white" {}
        _OverlayTex("Overlay Texture", 2D) = "white" {}
    }
        SubShader
    {
        Tags { "RenderType" = "Opaque" }
        LOD 200

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            sampler2D _BaseTex;
            sampler2D _OverlayTex;

            struct appdata_t
            {
                float4 vertex : POSITION;
                float2 texcoord : TEXCOORD0;
            };

            struct v2f
            {
                float2 texcoord : TEXCOORD0;
                float4 vertex : SV_POSITION;
            };

            v2f vert(appdata_t v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.texcoord = v.texcoord;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 baseTex = tex2D(_BaseTex, i.texcoord);
                fixed4 overlayTex = tex2D(_OverlayTex, i.texcoord);
                fixed4 result = lerp(baseTex, overlayTex, overlayTex.a);
                return result;
            }
            ENDCG
        }
    }
        FallBack "Diffuse"
}

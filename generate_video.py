import os, requests, sys, base64, json

CF_ACCOUNT = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

# Modelo text-to-video disponible en Cloudflare gratuito
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/@cf/wan-ai/wan2.1-t2v-14b"

PROMPT = "A plumber in blue uniform working on pipes, professional setting, vertical 9:16 format, high quality, realistic animation"

headers = {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"}

payload = {
    "prompt": PROMPT,
    "num_frames": 81,
    "fps": 24,
    "guidance_scale": 5.0
}

print("🎬 Generando video con Cloudflare Text-to-Video...")
print(f"📡 Endpoint: {API_URL}")

try:
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    print(f"📊 Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ Error: {resp.text[:500]}")
        sys.exit(1)
    
    data = resp.json()
    print(f"✅ Respuesta recibida")
    
    if data.get("success") and "result" in data:
        result = data["result"]
        if "video" in result:
            b64 = result["video"]
            if b64.startswith("data:"): b64 = b64.split(",", 1)[1]
            with open("video_daniel_plomero.mp4", "wb") as f:
                f.write(base64.b64decode(b64))
            print("✅ Video guardado: video_daniel_plomero.mp4")
        else:
            print(f"❌ Formato: {list(result.keys())}")
            sys.exit(1)
    else:
        print(f"❌ Fallo: {data}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

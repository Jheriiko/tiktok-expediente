import os, requests, sys, base64, json

CF_ACCOUNT = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")

# Endpoint verificado de Cloudflare para Image-to-Video
API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/@cf/wan-ai/wan2.1-i2v-14b"

PROMPT = "Animate this image naturally. The plumber blinks slowly and smiles warmly. Camera stays fixed, vertical 9:16 format."

headers = {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"}

# Payload con formato correcto para Cloudflare I2V
payload = {
    "prompt": PROMPT,
    "image": IMAGE_URL,
    "num_frames": 81,
    "fps": 24,
    "guidance_scale": 5.0
}

print("🎬 Generando con Cloudflare AI (Gratis)...")
print(f"📡 Endpoint: {API_URL}")
print(f"🖼️  Image URL: {IMAGE_URL[:50]}...")

try:
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    print(f"📊 Status Code: {resp.status_code}")
    print(f"📄 Response: {resp.text[:500]}")
    
    if resp.status_code == 404:
        print("❌ Modelo no encontrado. Probando endpoint alternativo...")
        # Fallback a otro modelo
        API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        payload = {"prompt": PROMPT}
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        print(f"📊 Status Code (fallback): {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ Error completo: {resp.text}")
        sys.exit(1)
    
    data = resp.json()
    print(f"✅ Respuesta: {json.dumps(data, indent=2)[:300]}")
    
    if data.get("success") and "result" in data:
        result = data["result"]
        if "video" in result:
            b64 = result["video"]
            if b64.startswith("data:"): b64 = b64.split(",", 1)[1]
            with open("video_daniel_plomero.mp4", "wb") as f:
                f.write(base64.b64decode(b64))
            print("✅ Video guardado: video_daniel_plomero.mp4")
        elif "image" in result:
            # Si es imagen en lugar de video
            img_b64 = result["image"]
            if img_b64.startswith("data:"): img_b64 = img_b64.split(",", 1)[1]
            with open("video_daniel_plomero.png", "wb") as f:
                f.write(base64.b64decode(img_b64))
            print("✅ Imagen guardada (modelo no soporta video)")
        else:
            print(f"❌ Formato inesperado: {list(result.keys())}")
            sys.exit(1)
    else:
        print(f"❌ Fallo: {data}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

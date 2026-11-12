import os, requests, sys, base64

CF_ACCOUNT = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")

API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/@cf/wan-ai/wan2.1-i2v-14b"
PROMPT = "Animate this image naturally. The plumber blinks slowly and smiles warmly. Camera stays fixed, vertical 9:16 format."

headers = {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"}
payload = {"prompt": PROMPT, "image": IMAGE_URL, "num_frames": 81, "fps": 24}

print("🎬 Generando con Cloudflare AI (Gratis)...")
resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
if resp.status_code != 200:
    print(f"❌ Error {resp.status_code}: {resp.text}"); sys.exit(1)

data = resp.json()
if data.get("success") and "result" in data and "video" in data["result"]:
    b64 = data["result"]["video"]
    if b64.startswith("data:"): b64 = b64.split(",", 1)[1]
    with open("video_daniel_plomero.mp4", "wb") as f:
        f.write(base64.b64decode(b64))
    print("✅ Video guardado")
else:
    print(f"❌ Fallo: {data}"); sys.exit(1)

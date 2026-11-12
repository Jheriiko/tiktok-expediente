import os, time, requests, sys

API_KEY = os.getenv("REPLICATE_API_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")

PROMPT = "Anima esta imagen vertical 9:16 manteniendo intactos los textos. El plomero parpadea y sonríe."

# Modelo más estable con fallback
MODEL_URL = "https://api.replicate.com/v1/models/minimax/video-01-live/predictions"

def generate_video():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "wait=60"
    }
    
    payload = {
        "input": {
            "prompt": PROMPT,
            "first_frame_image": IMAGE_URL,
            "prompt_optimizer": True
        }
    }
    
    print("🎬 Iniciando generación con MiniMax Video-01-Live...")
    
    try:
        resp = requests.post(MODEL_URL, headers=headers, json=payload, timeout=120)
        
        if resp.status_code not in [200, 201, 202]:
            print(f"❌ Error: {resp.status_code} - {resp.text}")
            sys.exit(1)
        
        task_data = resp.json()
        prediction_url = task_data.get("urls", {}).get("get")
        
        if not prediction_url:
            print("❌ No se recibió URL de monitoreo.")
            sys.exit(1)
        
        print(f"✅ Predicción creada. Monitoreando estado...")
        
        max_retries = 60
        for i in range(max_retries):
            time.sleep(10)
            try:
                status_resp = requests.get(prediction_url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=30)
                status_data = status_resp.json()
                status = status_data.get("status")
                print(f"   Estado: {status} (intento {i+1}/{max_retries})")
                
                if status in ["succeeded", "failed", "canceled"]:
                    break
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Error de conexión en polling: {e}")
                time.sleep(5)
        
        if status == "succeeded":
            output = status_data.get("output")
            video_url = output[0] if isinstance(output, list) else output
            
            if video_url:
                print("📥 Descargando video...")
                video_content = requests.get(video_url, timeout=120).content
                with open("video_daniel_plomero.mp4", "wb") as f:
                    f.write(video_content)
                print("✅ Video guardado: video_daniel_plomero.mp4")
            else:
                print("❌ Sin URL de video.")
                sys.exit(1)
        else:
            err_msg = status_data.get("error", "Desconocido")
            print(f"❌ Falló la generación: {err_msg}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_video()

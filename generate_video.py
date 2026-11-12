import os
import time
import requests
import sys

API_KEY = os.getenv("AGNES_API_KEY")
IMAGE_URL = os.getenv("IMAGE_URL")
PROMPT = "Anima esta imagen vertical 9:16 manteniendo intactos los textos. El plomero parpadea y sonríe."

# Endpoint y payload según la documentación oficial de Agnes Video v2.0
API_URL = "https://apihub.agnes-ai.com/v1/videos"

def generate_video():
    print("🚀 Iniciando fábrica de videos Daniel Plomero (Agnes AI)...")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # Payload con los parámetros exactos que espera Agnes AI[reference:5]
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": PROMPT,
        "image": IMAGE_URL,
        "size": "720P",          # Requerido por Agnes
        "aspect_ratio": "9:16",  # Vertical para redes sociales
        "num_frames": 121,       # 5 segundos a 24fps (debe ser 8n+1)
        "frame_rate": 24
    }

    resp = requests.post(API_URL, headers=headers, json=payload)
    
    if resp.status_code != 200:
        print(f"❌ Error en la solicitud: {resp.status_code} - {resp.text}")
        sys.exit(1) # Fuerza el error en GitHub Actions

    # La respuesta de Agnes usa 'video_id' para la consulta de estado[reference:6]
    task_data = resp.json()
    video_id = task_data.get("video_id") or task_data.get("id")
    if not video_id:
        print("❌ No se recibió video_id en la respuesta.")
        sys.exit(1)

    print(f"✅ Tarea creada con video_id: {video_id}. Esperando renderizado...")
    
    # Bucle de polling usando el endpoint correcto de Agnes
    while True:
        # Endpoint de consulta: /agnesapi?video_id=...&model_name=...
        status_url = f"https://apihub.agnes-ai.com/agnesapi?video_id={video_id}&model_name=agnes-video-v2.0"
        status_resp = requests.get(status_url, headers=headers)
        status_data = status_resp.json()
        status = status_data.get("status")

        if status == "completed":
            video_url = status_data.get("metadata", {}).get("url") or status_data.get("video_url")
            if video_url:
                print("🎉 ¡Video generado! Descargando...")
                with open("video_daniel_plomero.mp4", "wb") as f:
                    f.write(requests.get(video_url).content)
                print("✅ Archivo guardado exitosamente.")
            else:
                print("❌ Completado pero sin URL de video.")
                sys.exit(1)
            break
        elif status == "failed":
            print(f"❌ Falló la generación: {status_data}")
            sys.exit(1)
        else:
            print(f"⏳ Estado: {status}. Esperando 15s...")
            time.sleep(15)

if __name__ == "__main__":
    generate_video()

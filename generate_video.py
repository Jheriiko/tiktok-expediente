import os
import time
import requests
import sys # <-- Importante para forzar el error

API_KEY = os.getenv("AGNES_API_KEY")
IMAGE_URL = os.getenv("IMAGE_URL")
PROMPT = "Anima esta imagen vertical 9:16 manteniendo intactos los textos. El plomero parpadea y sonríe."
API_URL = "https://apihub.agnes-ai.com/v1/videos"

def generate_video():
    print("🚀 Iniciando fábrica de videos Daniel Plomero...")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-video-v2.0", "prompt": PROMPT, "image": IMAGE_URL, "width": 720, "height": 1280, "num_frames": 240}

    resp = requests.post(API_URL, headers=headers, json=payload)
    
    if resp.status_code != 200:
        print(f"❌ Error en la solicitud: {resp.status_code} - {resp.text}")
        sys.exit(1) # 🚨 OBLIGA A GITHUB A MARCAR EL PROCESO EN ROJO

    task_id = resp.json().get("id")
    if not task_id:
        print("❌ No hay ID de tarea en la respuesta.")
        sys.exit(1)

    print(f"✅ Tarea creada con ID: {task_id}. Esperando...")
    
    while True:
        status_resp = requests.get(f"{API_URL}/{task_id}", headers=headers)
        status_data = status_resp.json()
        status = status_data.get("status")

        if status == "completed":
            video_url = status_data.get("metadata", {}).get("url") or status_data.get("video_url")
            if video_url:
                print(f"🎉 ¡Video generado! Descargando...")
                with open("video_daniel_plomero.mp4", "wb") as f:
                    f.write(requests.get(video_url).content)
                print("✅ Archivo guardado.")
            else:
                print("❌ Completado pero sin URL de video.")
                sys.exit(1)
            break
        elif status == "failed":
            print(f"❌ Falló la generación: {status_data}")
            sys.exit(1) # 🚨 FORZAMOS EL ERROR
        else:
            print(f"⏳ Estado: {status}. Esperando 15s...")
            time.sleep(15)

if __name__ == "__main__":
    generate_video()

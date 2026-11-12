import os
import time
import requests
import sys

API_KEY = os.getenv("REPLICATE_API_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL")
PROMPT = "Anima esta imagen vertical 9:16 manteniendo intactos los textos. El plomero parpadea y sonríe."
API_URL = "https://api.replicate.com/v1/models/minimax/video-01/predictions"

def generate_video():
    print("🚀 Iniciando fábrica de videos con Replicate...")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "input": {
            "prompt": PROMPT, 
            "first_frame_image": IMAGE_URL, 
            "prompt_optimizer": True
        }
    }

    resp = requests.post(API_URL, headers=headers, json=payload)
    if resp.status_code not in [200, 201]:
        print(f"❌ Error en la solicitud: {resp.status_code} - {resp.text}")
        sys.exit(1)

    task_data = resp.json()
    prediction_url = task_data.get("urls", {}).get("get")
    if not prediction_url:
        print("❌ No se recibió URL de monitoreo.")
        sys.exit(1)

    print("✅ Predicción creada en Replicate. Monitoreando estado...")
    status = "starting"
    status_data = {}
    
    while status not in ["succeeded", "failed", "canceled"]:
        time.sleep(10)
        status_resp = requests.get(prediction_url, headers={"Authorization": f"Bearer {API_KEY}"})
        status_data = status_resp.json()
        status = status_data.get("status")
        print(f"⏳ Estado: {status}...")

    if status == "succeeded":
        output = status_data.get("output")
        video_url = output[0] if isinstance(output, list) else output
        if video_url:
            print("🎉 ¡Video generado! Descargando...")
            with open("video_daniel_plomero.mp4", "wb") as f:
                f.write(requests.get(video_url).content)
            print("✅ Archivo guardado con éxito.")
        else:
            print("❌ Sin URL de video en la respuesta.")
            sys.exit(1)
    else:
        err_msg = status_data.get("error", "Desconocido")
        print(f"❌ Falló la generación: {err_msg}")
        sys.exit(1)

if __name__ == "__main__":
    generate_video()

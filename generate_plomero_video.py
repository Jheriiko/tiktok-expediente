import os
import time
import requests
import subprocess
import asyncio
import edge_tts

# --- CONFIGURACIÓN ---
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
IMAGE_URL = os.getenv("IMAGE_URL") 

# Elegimos el guion (Puedes cambiar el texto aquí)
GUION_VOZ = "¿Fuga de agua o tubería rota? ¡No arruines tu casa! Soy Daniel Plomero. Reparaciones rápidas, limpias y 100% garantizadas. ¡Marca ya y soluciona eso hoy!"
TELEFONO = "302 121 1347"

def generar_voz():
    print("🎙️ Generando voz en off con IA...")
    # Voz en español de Colombia (muy natural)
    voice = "es-CO-GonzaloNeural" 
    async def _generar():
        tts = edge_tts.Communicate(GUION_VOZ, voice)
        await tts.save("voz_plomero.mp3")
    asyncio.run(_generar())
    print("✅ Voz generada: voz_plomero.mp3")

def generar_video_ia():
    print("🎬 Solicitando video a Replicate (Wan 2.1)...")
    headers = {"Authorization": f"Bearer {REPLICATE_API_TOKEN}", "Content-Type": "application/json"}
    
    # Usamos Wan 2.1 (económico y rápido)
    payload = {
        "version": "wan-video/wan-2.1-i2v",
        "input": {
            "image": IMAGE_URL,
            "prompt": "El plomero parpadea, sonríe sutilmente y mueve las manos trabajando. Tuberías de fondo con luz suave. Estilo cinematográfico.",
            "num_frames": 81 # Aproximadamente 5 segundos de animación (depende del modelo)
        }
    }
    
    resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
    if resp.status_code != 201:
        print(f"❌ Error en Replicate: {resp.text}")
        return False
        
    prediction = resp.json()
    prediction_id = prediction["id"]
    print(f"⏳ Generando video (ID: {prediction_id})...")
    
    while True:
        status_resp = requests.get(f"https://api.replicate.com/v1/predictions/{prediction_id}", headers=headers)
        status_data = status_resp.json()
        
        if status_data["status"] == "succeeded":
            video_url = status_data["output"]
            print(f"🎉 ¡Video listo! Descargando...")
            video_data = requests.get(video_url).content
            with open("video_base.mp4", "wb") as f:
                f.write(video_data)
            return True
        elif status_data["status"] == "failed":
            print(f"❌ Falló la generación: {status_data}")
            return False
        
        time.sleep(10)

def montar_video_final():
    print("🎛️ Montando video final con FFmpeg (Texto + Botón + Audio)...")
    
    # Comando de FFmpeg para superponer el texto y el botón sobre el video de la IA
    # Nota: Ajustamos los tiempos para que el video dure lo que dura el audio.
    cmd = [
        "ffmpeg", "-y",
        "-i", "video_base.mp4",          # El video de la IA
        "-i", "voz_plomero.mp3",         # La voz generada
        "-filter_complex", 
        # 1. Ajustamos la duración del video al audio
        # 2. Agregamos el texto de urgencia arriba
        # 3. Agregamos un "botón" fucsia simulado con el teléfono
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "drawtext=text='¡FUGA DE AGUA?':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=100:box=1:boxcolor=black@0.5:boxborderw=20:enable='between(t,0,2)',"
        "drawtext=text='RÁPIDOS Y GARANTIZADOS':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=200:box=1:boxcolor=black@0.5:boxborderw=20:enable='between(t,2,7)',"
        "drawbox=x=100:y=1500:w=880:h=200:color=magenta@0.8:t=fill:enable='between(t,7,10)',"
        "drawtext=text='LLAMA YA: 302 121 1347':fontcolor=white:fontsize=65:x=(w-text_w)/2:y=1560:enable='between(t,7,10)'[v]",
        "-map", "[v]", "-map", "1:a", 
        "-c:v", "libx264", "-c:a", "aac", "-shortest", 
        "video_daniel_plomero_final.mp4"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ ¡Video final ensamblado con éxito!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en FFmpeg: {e}")

if __name__ == "__main__":
    if not REPLICATE_API_TOKEN or not IMAGE_URL:
        print("❌ Faltan las credenciales (REPLICATE_API_TOKEN o IMAGE_URL).")
    else:
        generar_voz()
        exito = generar_video_ia()
        if exito:
            montar_video_final()
        else:
            print("❌ No se pudo generar el video final porque la IA falló.")

import os
import json
import requests
import subprocess

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "richardyoung/qwen3-4b-instruct-2507-abliterated:Q4_K_M" 

def leer_archivo(nombre, defecto=""):
    if os.path.exists(nombre):
        with open(nombre, "r", encoding="utf-8") as f: return f.read()
    return defecto

CEREBRO = leer_archivo("cerebro.md", "Eres Jarvis.")

SYSTEM_PROMPT = f"""
{CEREBRO}

HERRAMIENTAS (Responde ÚNICAMENTE con este JSON):
1. {{"thought": "...", "action": "run", "command": "..."}}
2. {{"thought": "...", "action": "final", "response": "..."}}
"""

def llamar_ia(mensajes):
    payload = {
        "model": MODELO,
        "messages": mensajes,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_ctx": 2048
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        return json.dumps({"thought": "Error", "action": "final", "response": f"Error de red o falta de RAM: {e}"})

def ejecutar_comando(comando):
    palabras_prohibidas = ["muestra", "instala", "busca", "fast fetch", "hola"]
    primer_palabra = comando.strip().split()[0].lower() if comando.strip() else ""
    
    if primer_palabra in palabras_prohibidas:
        return "ERROR CRÍTICO: Comando en español detectado. Usa comandos reales de Linux."
    
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=120)
        return (resultado.stdout if resultado.stdout else resultado.stderr)[-1000:]
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print("🧠 JARVIS (4B - MODO LIGERO) INICIADO.")
    print("👉 Pídele tareas. El modelo no debería colapsar tu teléfono.\n")
    
    historial = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    while True:
        try:
            tarea = input("\n👤 Tú: ")
            if tarea.lower() == "salir": break
            
            historial = [{"role": "system", "content": SYSTEM_PROMPT}]
            historial.append({"role": "user", "content": tarea})
            
            pasos = 0
            MAX_PASOS = 5
            
            while True:
                if pasos >= MAX_PASOS:
                    print(f"\n👑 IA: Límite de pasos alcanzado.")
                    break
                
                pasos += 1
                print("🧠 Pensando...")
                respuesta_json_str = llamar_ia(historial)
                
                try:
                    inicio = respuesta_json_str.find('{')
                    fin = respuesta_json_str.rfind('}') + 1
                    accion_data = json.loads(respuesta_json_str[inicio:fin])
                    accion = accion_data.get("action")
                    pensamiento = accion_data.get("thought", "Sin pensamiento.")
                    
                    print(f"\n🧠 [PASO {pasos}/{MAX_PASOS}] [ANÁLISIS]: {pensamiento}")
                    
                    if accion == "run":
                        comando = accion_data.get("command")
                        print(f"⚙️ [EJECUTANDO]: {comando}")
                        salida = ejecutar_comando(comando)
                        print(f"📤 [SALIDA]: {salida[:200]}...")
                        historial.append({"role": "assistant", "content": respuesta_json_str})
                        historial.append({"role": "user", "content": f"Resultado: {salida}"})
                        
                    elif accion == "final":
                        print(f"\n👑 IA: {accion_data.get('response')}")
                        break
                except Exception as e:
                    print(f"❌ Error JSON: {e}")
                    break
        except KeyboardInterrupt:
            break

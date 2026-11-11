import getpass
import json
import os
import shlex
import subprocess
from pathlib import Path

import requests
from bs4 import BeautifulSoup

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent"
)
PROJECT_DIR = Path(__file__).resolve().parent
MAX_STEPS = 5

ALLOWED_COMMANDS = {
    "pwd", "ls", "cat", "grep", "find", "mkdir", "touch",
    "cp", "mv", "git", "python", "python3", "pip", "pip3",
    "termux-open",
}

SYSTEM_PROMPT = """
Eres Jarvis, un asistente para ayudar con proyectos en Termux.
Responde siempre con un único objeto JSON, sin texto adicional:
{"action":"run","command":"...","summary":"motivo breve"}
{"action":"search","query":"...","summary":"motivo breve"}
{"action":"final","response":"..."}

Reglas:
- Ejecuta automáticamente los comandos permitidos; no pidas aprobación.
- No uses tuberías, redirecciones, punto y coma ni encadenamiento de comandos.
- No intentes borrar archivos ni cambiar permisos.
- Si falta información o una acción no está permitida, explícalo con action=final.
- No afirmes que ejecutaste algo si no recibiste el resultado.
"""

def buscar_web(query):
    response = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    resultados = []

    for item in soup.select(".result")[:4]:
        titulo = item.select_one(".result__a")
        resumen = item.select_one(".result__snippet")
        if titulo:
            texto = resumen.get_text(" ", strip=True) if resumen else ""
            resultados.append(
                f"- {titulo.get_text(' ', strip=True)}: {texto}"
            )

    return "\n".join(resultados) or "No encontré resultados."

def llamar_gemini(api_key, historial):
    contents = [
        {
            "role": "user" if mensaje["role"] == "user" else "model",
            "parts": [{"text": mensaje["content"]}],
        }
        for mensaje in historial
    ]

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    response = requests.post(
        API_URL,
        headers={"x-goog-api-key": api_key},
        json=payload,
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"Gemini respondió {response.status_code}: {response.text[:1000]}"
        )

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

def ejecutar_comando(comando):
    prohibidos = (";", "|", "&", ">", "<", "`", "$", "\n")
    if any(caracter in comando for caracter in prohibidos):
        return "Comando rechazado: no se permite sintaxis de shell."

    try:
        argumentos = shlex.split(comando)
    except ValueError as error:
        return f"Comando inválido: {error}"

    if not argumentos:
        return "No se recibió ningún comando."

    if argumentos[0] not in ALLOWED_COMMANDS:
        return f"Comando rechazado: '{argumentos[0]}' no está permitido."

    try:
        resultado = subprocess.run(
            argumentos,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        salida = ((resultado.stdout or "") + (resultado.stderr or "")).strip()
        return salida[-4000:] or (
            f"Terminó con código {resultado.returncode}, sin salida."
        )
    except subprocess.TimeoutExpired:
        return "El comando superó el límite de 120 segundos."
    except Exception as error:
        return f"Error al ejecutar el comando: {error}"

def recortar_historial(historial):
    if len(historial) > 12:
        del historial[:-12]

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = getpass.getpass("Clave de Gemini (no se mostrará): ")

    if not api_key.strip():
        print("No recibí una clave de API.")
        return

    historial = []
    print("JARVIS iniciado. Escribe 'salir' para terminar.")

    while True:
        try:
            tarea = input("\nTú: ").strip()
            if tarea.lower() in {"salir", "exit", "quit"}:
                print("Cerrando Jarvis.")
                break
            if not tarea:
                continue

            historial.append({"role": "user", "content": tarea})
            recortar_historial(historial)

            for paso in range(1, MAX_STEPS + 1):
                print(f"\nConsultando a Gemini ({paso}/{MAX_STEPS})...")
                try:
                    respuesta = llamar_gemini(api_key, historial)
                    accion_data = json.loads(respuesta)
                except Exception as error:
                    print(f"No pude consultar a Gemini: {error}")
                    break

                accion = accion_data.get("action")

                if accion == "final":
                    print(f"\nJarvis: {accion_data.get('response', 'Listo.')}")
                    historial.append({"role": "assistant", "content": respuesta})
                    break

                if accion == "search":
                    query = accion_data.get("query", "").strip()
                    try:
                        salida = buscar_web(query) if query else "Búsqueda vacía."
                    except Exception as error:
                        salida = f"Falló la búsqueda: {error}"
                    print(salida)
                    historial.extend([
                        {"role": "assistant", "content": respuesta},
                        {"role": "user", "content": f"Resultados:\n{salida}"},
                    ])
                    continue

                if accion == "run":
                    comando = accion_data.get("command", "").strip()
                    print(f"Ejecutando automáticamente: {comando}")
                    salida = ejecutar_comando(comando)
                    print(f"Resultado:\n{salida}")
                    historial.extend([
                        {"role": "assistant", "content": respuesta},
                        {"role": "user", "content": f"Resultado:\n{salida}"},
                    ])
                    continue

                print("Jarvis devolvió una acción que no reconozco.")
                break
            else:
                print("Llegué al límite de pasos para esta tarea.")

            recortar_historial(historial)

        except KeyboardInterrupt:
            print("\nCerrando Jarvis.")
            break

if __name__ == "__main__":
    main()

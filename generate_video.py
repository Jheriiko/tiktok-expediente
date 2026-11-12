import os
import time
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

API_KEY = os.getenv("AGNES_API_KEY")
IMAGE_URL = os.getenv("IMAGE_URL")
PROMPT = "Anima esta imagen vertical 9:16 manteniendo intactos los textos. El plomero parpadea y sonríe."

API_URL = "https://apihub.agnes-ai.com/v1/videos"

def generate_video():
    console.print("[bold cyan]🚀 Iniciando fábrica de videos Daniel Plomero[/bold cyan]")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "agnes-video-v2.0",
        "prompt": PROMPT,
        "image": IMAGE_URL,
        "width": 720,
        "height": 1280,
        "num_frames": 240
    }

    with console.status("[bold yellow]Enviando solicitud a Agnes AI...[/bold yellow]", spinner="dots"):
        resp = requests.post(API_URL, headers=headers, json=payload)
    
    if resp.status_code != 200:
        console.print(f"[bold red]❌ Error en la solicitud: {resp.status_code} - {resp.text}[/bold red]")
        return

    result = resp.json()
    task_id = result.get("id")
    if not task_id:
        console.print(f"[bold red]❌ No hay ID de tarea: {result}[/bold red]")
        return

    console.print(f"[bold green]✅ Tarea creada con ID: {task_id}[/bold green]")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        task = progress.add_task("[cyan]Esperando renderizado de Agnes AI...", total=None)
        
        while True:
            status_resp = requests.get(f"{API_URL}/{task_id}", headers=headers)
            status_data = status_resp.json()
            status = status_data.get("status")

            if status == "completed":
                video_url = status_data.get("metadata", {}).get("url") or status_data.get("video_url")
                if video_url:
                    console.print(f"[bold green]🎉 ¡Video generado! Descargando...[/bold green]")
                    with open("video_daniel_plomero.mp4", "wb") as f:
                        f.write(requests.get(video_url).content)
                    console.print("[bold green]✅ Archivo guardado exitosamente.[/bold green]")
                break
            elif status == "failed":
                console.print(f"[bold red]❌ Falló la generación: {status_data}[/bold red]")
                break
            else:
                progress.update(task, description=f"[cyan]Estado: {status}. Esperando 15s...[/cyan]")
                time.sleep(15)

if __name__ == "__main__":
    generate_video()

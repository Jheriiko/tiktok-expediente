import os, json, subprocess, textwrap, time, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "guion.json").read_text(encoding="utf-8"))
W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = Path("out"); OUT.mkdir(exist_ok=True)
FINAL = OUT / f"{CFG['titulo']}.mp4"
API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

def run(cmd, **kw):
    print(">>", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, **kw)

def dur(p):
    out = subprocess.check_output(["ffprobe","-v","error","-show_entries", "format=duration","-of","json",str(p)])
    return float(json.loads(out)["format"]["duration"])

def tts(texto, salida):
    for intento in range(3):
        try:
            run(["edge-tts","--voice","es-ES-AlvaroNeural", "--text", texto, "--write-media", str(salida)])
            return
        except subprocess.CalledProcessError:
            time.sleep(3)
    from gtts import gTTS
    gTTS(texto, lang="es").save(str(salida))

def get_image(prompt, salida):
    # Codificar el prompt para que funcione en la URL
    p_encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{p_encoded}?width=1080&height=1920&nologo=true"
    if API_KEY:
        url += f"&token={API_KEY}"
    run(["curl", "-L", "-s", "-o", str(salida), url])

def clip(texto, dur_s, img_path, salida, idx):
    tf = OUT / f"txt_{idx}.txt"
    tf.write_text("\n".join(textwrap.wrap(texto, width=22)), encoding="utf-8")
    # Filtro: Escalar imagen, oscurecerla un poco para leer el texto, y poner el texto
    filtro = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"eq=brightness=-0.2:contrast=1.1," # Oscurece la imagen de fondo
        f"drawtext=fontfile={FONT}:textfile={tf}:"
        "fontcolor=white:fontsize=68:line_spacing=18:"
        "box=1:boxcolor=black@0.6:boxborderw=20:"
        "x=(w-text_w)/2:y=(h-text_h)/2"
    )
    # Bucle de imagen (-loop 1) para que dure lo que dura el audio
    run(["ffmpeg","-y","-loop","1","-i",str(img_path), "-vf", filtro, 
         "-c:v","libx264","-pix_fmt","yuv420p", "-t", str(dur_s), str(salida)])

def main():
    clips, audios = [], []
    for i, seg in enumerate(CFG["segmentos"]):
        print(f"--- Generando escena {i+1} ---")
        a = OUT / f"audio_{i}.mp3"
        tts(seg["voz"], a)
        d = dur(a) + 0.4
        
        img = OUT / f"img_{i}.jpg"
        print(f"Descargando imagen para: {seg['imagen']}")
        get_image(seg["imagen"], img)
        
        v = OUT / f"clip_{i}.mp4"
        clip(seg["pantalla"], d, img, v, i)
        clips.append(v); audios.append(a)

    # Unir videos
    lv = OUT / "lv.txt"; lv.write_text("\n".join(f"file '{c.name}'" for c in clips))
    v_sin_audio = OUT / "v_sin_audio.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",lv,"-c","copy",v_sin_audio])

    # Unir audios
    la = OUT / "la.txt"; la.write_text("\n".join(f"file '{a.name}'" for a in audios))
    a_full = OUT / "audio_full.mp3"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",la,"-c","copy",a_full])

    # Unir video y audio final
    run(["ffmpeg","-y","-i",v_sin_audio,"-i",a_full, "-c:v","copy","-c:a","aac","-shortest",FINAL])

    adv = CFG.get("advertencia")
    if adv:
        tf = OUT / "adv.txt"; tf.write_text(adv, encoding="utf-8")
        con_adv = OUT / f"{CFG['titulo']}_adv.mp4"
        run(["ffmpeg","-y","-i",FINAL, "-vf", f"drawtext=fontfile={FONT}:textfile={tf}:fontcolor=yellow:fontsize=52:" "box=1:boxcolor=black@0.7:boxborderw=14:x=(w-text_w)/2:y=80:enable='lt(t,2)'", "-c:a","copy",con_adv])
        con_adv.replace(FINAL)

    print(f"OK: {FINAL} ({FINAL.stat().st_size/1e6:.1f} MB)")

if __name__ == "__main__":
    main()

import os, json, subprocess, textwrap, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "guion.json").read_text(encoding="utf-8"))
W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = Path("out"); OUT.mkdir(exist_ok=True)
FINAL = OUT / f"{CFG['titulo']}.mp4"

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

def clip(texto, dur_s, salida, idx):
    tf = OUT / f"txt_{idx}.txt"
    tf.write_text("\n".join(textwrap.wrap(texto, width=22)), encoding="utf-8")
    filtro = (f"drawtext=fontfile={FONT}:textfile={tf}:" "fontcolor=white:fontsize=68:line_spacing=18:" "box=1:boxcolor=black@0.68:boxborderw=20:" "x=(w-text_w)/2:y=(h-text_h)/2")
    run(["ffmpeg","-y","-f","lavfi","-i", f"color=c=0x0a0a0a:s={W}x{H}:d={dur_s}", "-vf", filtro, "-c:v","libx264","-pix_fmt","yuv420p", "-t", str(dur_s), str(salida)])

def main():
    clips, audios = [], []
    for i, seg in enumerate(CFG["segmentos"]):
        a = OUT / f"audio_{i}.mp3"
        tts(seg["voz"], a)
        d = dur(a) + 0.4
        v = OUT / f"clip_{i}.mp4"
        clip(seg["pantalla"], d, v, i)
        clips.append(v); audios.append(a)

    lv = OUT / "lv.txt"; lv.write_text("\n".join(f"file '{c}'" for c in clips))
    v_sin_audio = OUT / "v_sin_audio.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",lv,"-c","copy",v_sin_audio])

    la = OUT / "la.txt"; la.write_text("\n".join(f"file '{a}'" for a in audios))
    a_full = OUT / "audio_full.mp3"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",la,"-c","copy",a_full])

    run(["ffmpeg","-y","-i",v_sin_audio,"-i",a_full, "-c:v","copy","-c:a","aac","-shortest",FINAL])

    if CFG.get("musica_url"):
        mus = OUT / "musica.mp3"
        run(["curl","-L","-o",mus, CFG["musica_url"]])
        con_mus = OUT / f"{CFG['titulo']}_mus.mp4"
        run(["ffmpeg","-y","-i",FINAL,"-stream_loop","-1","-i",mus, "-filter_complex", "[0:a]volume=1.0[a1];[1:a]volume=0.12[a2];[a1][a2]amix=inputs=2:duration=first[aout]", "-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-shortest",con_mus])
        con_mus.replace(FINAL)

    adv = CFG.get("advertencia")
    if adv:
        tf = OUT / "adv.txt"; tf.write_text(adv, encoding="utf-8")
        con_adv = OUT / f"{CFG['titulo']}_adv.mp4"
        run(["ffmpeg","-y","-i",FINAL, "-vf", f"drawtext=fontfile={FONT}:textfile={tf}:fontcolor=yellow:fontsize=52:" "box=1:boxcolor=black@0.7:boxborderw=14:x=(w-text_w)/2:y=80:enable='lt(t,2)'", "-c:a","copy",con_adv])
        con_adv.replace(FINAL)

    print(f"OK: {FINAL} ({FINAL.stat().st_size/1e6:.1f} MB)")

if __name__ == "__main__":
    main()

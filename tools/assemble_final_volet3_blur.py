#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemblage Volet 3 : visage animé net + FOND FLOU (portrait) + logo Hermes
+ lien dépôt (10 dernières s) + voix off.

Entrées : portrait animé (LivePortrait 512, carré) + voix off v4 (~5 min)
Sortie  : youtube_volet3_hermes_skills_v4.mp4
Fond    : version étirée+floutée du portrait (pas de miroir).
"""
import os
import subprocess
import sys

D = r"C:\Users\searc\AppData\Local\hermes\data\video_youtube"
os.chdir(D)


def run(cmd, label=""):
    print(f"[{label}] ...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR:", r.stderr[-1200:])
        sys.exit(1)
    print("  -> OK", flush=True)


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


FACE = sys.argv[1] if len(sys.argv) > 1 else "face_liveportrait_volet3.mp4"
VOIX = "volet3_hermes_skills_v4.wav"
LOGO = "hermes_logo_icon.png"
OUT = "youtube_volet3_hermes_skills_v7.mp4"

# 1. FOND FLOU : le visage est étiré en fond 1920x1080 + flou gaussien ;
#    le visage NET (1080x1080) est centré par-dessus.
run([
    "ffmpeg", "-y", "-i", FACE,
    "-filter_complex",
    "[0:v]split=2[bg][fg];"
    "[bg]scale=1920:1080:flags=lanczos,gblur=sigma=30[bgblur];"
    "[fg]scale=1080:1080:flags=lanczos[fgsharp];"
    "[bgblur][fgsharp]overlay=(W-w)/2:(H-h)/2[composite]",
    "-map", "[composite]", "-an",
    "-c:v", "h264_nvenc", "-r", "30", "-preset", "p7", "-cq", "20", "-b:v", "0",
    "-pix_fmt", "yuv420p",
    "fond_flou_volet3.mp4",
], "fond flou")

# 2. Logo Hermes en coin + voix off
run([
    "ffmpeg", "-y",
    "-i", "fond_flou_volet3.mp4",
    "-i", LOGO,
    "-i", VOIX,
    "-filter_complex",
    "[1:v]scale=320:-1[lg];"
    "[0:v][lg]overlay=W-w-40:40[branded]",
    "-map", "[branded]", "-map", "2:a",
    "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "18", "-b:v", "0",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart",
    "volet3_branded.mp4",
], "logo + voix off")

# 3. Lien du dépôt en bas d'écran pendant les 10 dernières secondes
branded_d = dur("volet3_branded.mp4")
link_start = max(0.0, branded_d - 10.0)
print(f"branded={branded_d:.1f}s  lien à partir de {link_start:.1f}s", flush=True)

run([
    "ffmpeg", "-y",
    "-i", "volet3_branded.mp4",
    "-vf",
    f"drawbox=x=0:y=ih-120:w=iw:h=120:color=black@0.5:t=fill:enable='gte(t,{link_start:.3f})',"
    f"drawtext=text='github.com/Antoine-Thomas/hermes-skills':"
    f"fontfile=Montserrat.ttf:fontsize=44:fontcolor=white:"
    f"x=(w-text_w)/2:y=h-85:enable='gte(t,{link_start:.3f})'",
    "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "18", "-b:v", "0",
    "-c:a", "copy",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    OUT,
], "lien dépôt (10 dernières secondes)")

# Nettoyage
for tmp in ("fond_flou_volet3.mp4", "volet3_branded.mp4"):
    if os.path.exists(tmp):
        os.remove(tmp)

print(f"=== TERMINÉ : {OUT} ({dur(OUT):.1f}s) ===", flush=True)

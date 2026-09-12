#!/usr/bin/env python3
"""SadTalker Volet 3 avec GFPGAN (pipeline V7) — corrige bouche fermée / dents invisibles.

Le rendu SadTalker précédent (crop, sans enhancer) donnait une bouche floue :
les dents n'étaient pas visibles -> impression de bouche fermée.
La V7 validée utilisait --preprocess full --still --enhancer gfpgan (dents nettes).
"""
import subprocess
from pathlib import Path

BASE = Path(r"C:\Users\searc\AppData\Local\hermes\data\video_youtube")
REPO = BASE / "sadtalker" / "repo"
PY = BASE / "sadtalker" / "venv" / "Scripts" / "python.exe"

cmd = [
    str(PY), "inference.py",
    "--driven_audio", str(BASE / "volet3_hermes_skills_v4.wav"),
    "--source_image", str(BASE / "portrait_512.png"),
    "--result_dir", str(BASE / "volet3_sadtalker_gfpgan"),
    "--preprocess", "full",
    "--size", "512",
    "--still",
    "--enhancer", "gfpgan",
]
print("SadTalker volet3 (gfpgan) →", " ".join(cmd), flush=True)
subprocess.run(cmd, cwd=str(REPO), check=True)
print("SadTalker gfpgan render complete.", flush=True)

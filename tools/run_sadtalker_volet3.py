#!/usr/bin/env python3
"""SadTalker render for Volet 3 — driving video synced to the NEW voiceover."""
import subprocess
import sys
from pathlib import Path

BASE = Path(r"C:\Users\searc\AppData\Local\hermes\data\video_youtube")
SADTALKER_REPO = BASE / "sadtalker" / "repo"
VENV_PY = BASE / "sadtalker" / "venv" / "Scripts" / "python.exe"

AUDIO = str(BASE / "volet3_hermes_skills_v4.wav")
SOURCE = str(BASE / "portrait_512.png")
RESULT_DIR = str(BASE / "volet3_sadtalker")

cmd = [
    str(VENV_PY),
    "inference.py",
    "--driven_audio", AUDIO,
    "--source_image", SOURCE,
    "--result_dir", RESULT_DIR,
    "--preprocess", "crop",
    "--size", "512",
    # no --still: user wants head/eye/neck movement
    # no --enhancer: gfpgan import is broken in this repo; LivePortrait handles teeth
]

print("SadTalker volet 3 →", " ".join(cmd), flush=True)
subprocess.run(cmd, cwd=str(SADTALKER_REPO), check=True)
print("SadTalker render complete.", flush=True)
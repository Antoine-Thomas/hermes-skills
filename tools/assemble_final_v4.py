# -*- coding: utf-8 -*-
"""Assemblage final v4 : sortie LivePortrait sur FOND ANIMÉ Hermes + logo, 1080p.

Usage:
    python assemble_final_v4.py --video-input <talking_head.mp4> [--audio voix.wav]
"""
import argparse
import os
import subprocess
import sys

D = r"C:\Users\searc\AppData\Local\hermes\data\video_youtube"
os.chdir(D)


def run(cmd, label=""):
    print(f"[{label}] ...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR:", r.stderr[-900:])
        sys.exit(1)
    print("  -> OK", flush=True)


def build_animated_bg(duration_s):
    """Génère le fond animé (boucle) si absent, puis l'étend à la durée cible."""
    if not os.path.exists("bg_loop.mp4"):
        if not os.path.isdir("bg_anim_frames") or not os.listdir("bg_anim_frames"):
            # régénérer les frames via gen_fond_anime.py
            run([sys.executable, "gen_fond_anime.py"], "génération frames fond animé")
        run(["ffmpeg", "-y", "-framerate", "25", "-i", "bg_anim_frames/%05d.png",
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "bg_loop.mp4"],
            "fond animé (boucle)")
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", "bg_loop.mp4", "-t", str(duration_s),
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "animated_bg.mp4"],
        f"fond animé {duration_s}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-input", required=True, help="vidéo tête parlante (sortie LivePortrait)")
    ap.add_argument("--audio", default="voix_v3.wav", help="audio de la voix (si l'entrée est muette)")
    ap.add_argument("--output", default="resultat_final_v4.mp4")
    ap.add_argument("--title", default="titre_intro_video.mp4", help="carton de titre (optionnel)")
    ap.add_argument("--no-title", action="store_true", help="ne pas ajouter de carton de titre")
    args = ap.parse_args()

    if not os.path.exists(args.video_input):
        sys.exit(f"Vidéo d'entrée introuvable : {args.video_input}")

    # durée de la vidéo d'entrée
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", args.video_input],
                       capture_output=True, text=True)
    dur = float(p.stdout.strip())
    print(f"Durée entrée : {dur:.1f}s")

    # 1. fond animé étendu à la durée
    build_animated_bg(dur)

    # 2. logo Hermes en grand (filigrane semi-transparent) + visage centré sur le fond animé
    run(["ffmpeg", "-y", "-i", args.video_input, "-i", "animated_bg.mp4", "-i", "hermes_logo_icon.png",
         "-filter_complex",
         "[1:v]scale=1920:1080[bg];"
         "[2:v]scale=1400:-1,format=rgba,colorchannelmixer=aa=0.35[lg];"
         "[bg][lg]overlay=(W-w)/2:(H-h)/2[bg2];"
         "[0:v]scale=1080:1080:flags=lanczos[fg];"
         "[bg2][fg]overlay=(W-w)/2:(H-h)/2",
         "-map", "0:a?", "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "20", "-b:v", "0",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-pix_fmt", "yuv420p", "-shortest",
         "face_1080_v4.mp4"], "logo filigrane + visage sur fond animé")

    # 3. audio de la voix si l'entrée est muette
    if not args.no_title and os.path.exists(args.title):
        # titre -> 1080p
        run(["ffmpeg", "-y", "-i", args.title,
             "-vf", "scale=1920:1080:flags=lanczos",
             "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "20", "-b:v", "0",
             "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-pix_fmt", "yuv420p",
             "titre_1080.mp4"], "titre 1080p")
        # concat titre + visage
        run(["ffmpeg", "-y", "-i", "titre_1080.mp4", "-i", "face_1080_v4.mp4",
             "-filter_complex",
             "[0:v]fps=25,format=yuv420p[v0];[1:v]fps=25,format=yuv420p[v1];"
             "[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0];"
             "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a1];"
             "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
             "-map", "[v]", "-map", "[a]", "-c:v", "h264_nvenc", "-preset", "p5",
             "-cq", "20", "-b:v", "0", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", "concat_1080_v4.mp4"], "concat titre + visage")
        base = "concat_1080_v4.mp4"
    else:
        base = "face_1080_v4.mp4"

    # 4. logo watermark (superposé)
    run(["ffmpeg", "-y", "-i", base, "-loop", "1", "-i", "watermark_logo.png",
         "-filter_complex", "[1:v]scale=1920:1080[lg];[0:v][lg]overlay=0:0",
         "-map", "0:a", "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "20", "-b:v", "0",
         "-c:a", "copy", "-shortest", "-movflags", "+faststart",
         args.output], "logo")

    print(f"=== TERMINÉ : {args.output} ===", flush=True)


if __name__ == "__main__":
    main()

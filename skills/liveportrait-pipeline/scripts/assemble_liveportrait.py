#!/usr/bin/env python3
"""
Assemble LivePortrait chunks into a final video with background, logo, and audio.

Usage:
    python assemble_liveportrait.py \
        --chunks_dir output/ \
        --driving_video sadtalker_512_v3.mp4 \
        --bg_video fond_bois.mp4 \
        --logo logo_hermes.png \
        --audio narration.wav \
        --output final_video.mp4
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def assemble_chunks(chunks_dir: str, output_path: str):
    """Concatenate chunk videos using ffmpeg concat demuxer."""
    chunks = sorted(Path(chunks_dir).glob("tr_*.mp4"))
    if not chunks:
        print(f"Error: No chunks found in {chunks_dir}")
        sys.exit(1)

    # Create concat list
    concat_file = Path(chunks_dir) / "concat_list.txt"
    with open(concat_file, "w") as f:
        for chunk in chunks:
            f.write(f"file '{chunk.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Chunks assembled: {output_path}")


def add_background(input_video: str, bg_video: str, output_path: str):
    """Overlay the animated face onto the background video."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", bg_video,
        "-filter_complex",
        "[1:v]scale=1920:1080[bg];[bg][0:v]overlay=(W-w)/2:(H-h)/2",
        "-c:v", "libx264", "-crf", "18",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Background added: {output_path}")


def add_logo(input_video: str, logo_path: str, output_path: str,
             position: str = "top-right", margin: int = 20):
    """Add logo overlay to video."""
    if position == "top-right":
        overlay = f"W-w-{margin}:{margin}"
    elif position == "bottom-right":
        overlay = f"W-w-{margin}:H-h-{margin}"
    else:
        overlay = f"{margin}:{margin}"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", logo_path,
        "-filter_complex", f"[1:v]overlay={overlay}",
        "-c:v", "libx264", "-crf", "18",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Logo added: {output_path}")


def add_audio(input_video: str, audio_path: str, output_path: str):
    """Add audio track to video."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Audio added: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Assemble LivePortrait final video")
    parser.add_argument("--chunks_dir", required=True, help="Directory with tr_*.mp4 chunks")
    parser.add_argument("--driving_video", help="Driving video (for reference)")
    parser.add_argument("--bg_video", help="Background video (e.g. fond_bois.mp4)")
    parser.add_argument("--logo", help="Logo overlay image (e.g. logo_hermes.png)")
    parser.add_argument("--audio", help="Audio track (e.g. narration.wav)")
    parser.add_argument("--output", default="final_video.mp4", help="Output file")
    args = parser.parse_args()

    tmp_dir = Path(args.chunks_dir) / "_assembly_tmp"
    tmp_dir.mkdir(exist_ok=True)

    # Step 1: Concatenate chunks
    concat_path = str(tmp_dir / "01_concat.mp4")
    assemble_chunks(args.chunks_dir, concat_path)

    current = concat_path

    # Step 2: Add background
    if args.bg_video:
        bg_path = str(tmp_dir / "02_background.mp4")
        add_background(current, args.bg_video, bg_path)
        current = bg_path

    # Step 3: Add logo
    if args.logo:
        logo_path = str(tmp_dir / "03_logo.mp4")
        add_logo(current, args.logo, logo_path)
        current = logo_path

    # Step 4: Add audio
    if args.audio:
        audio_path = str(tmp_dir / "04_audio.mp4")
        add_audio(current, args.audio, audio_path)
        current = audio_path

    # Move to final output
    import shutil
    shutil.move(current, args.output)
    print(f"\nFinal video: {args.output}")

    # Cleanup temp
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

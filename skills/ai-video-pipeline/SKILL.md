---
name: ai-video-pipeline
description: Use when managing AI video inference and assembly.
---

# AI Video Pipeline: Best Practices

This skill covers the end-to-end management of AI video generation workflows (like LivePortrait, Wav2Lip), focusing on pre-processing, inference stability, and final assembly.

## Pipeline Steps

1. **Pre-processing (Crucial)**
   - **Stabilization/Denoising:** Video input (driving video) must be smooth. Jitter in the source causes artifacts in the output. Apply Gaussian blur or specialized denoising if necessary.
   - **FPS Alignment:** Ensure the driving video's FPS matches the target output FPS and the inference script's expected FPS. Mismatches cause stuttering/saccades.
   - **Portrait adaptation for 16:9 (YouTube):** Convert square portrait (1024×1024) to 1920×1080 with centered face, blurred neutral background, NO mirror/reflection:
     ```bash
     ffmpeg -y -i portrait_1024_square.png \
       -filter_complex \
       "[0:v]scale=1920:1920,boxblur=40:5,crop=1920:1080[bg]; \
        [0:v]scale=900:900:flags=lanczos[fg]; \
        [bg][fg]overlay=(W-w)/2:(H-h)/2[out]" \
       -map "[out]" portrait_16_9.png
     ```
   - **Square source for LivePortrait**: Also generate 1024×1024 square version from the same source (LivePortrait expects square input for stability):
     ```bash
     ffmpeg -y -i source_image.jpg -vf "crop=min(iw\,ih):min(iw\,ih),scale=1024:1024" portrait_1024_square.png
     ```

2. **Inference (LivePortrait, EchoMimicV2, etc.)**
   - **VRAM Monitoring:** Use `nvidia-smi` to monitor usage. If approaching limits, reduce resolution or close other heavy applications.
   - **Model Selection:** Choose based on need (lips-only vs. full-head) and hardware constraints (see `talking-head-video` skill for model comparison).
   - **LivePortrait V7 settings (best quality for this hardware):**
     ```bash
     --flag_stitching --flag_do_crop --flag_relative_motion --source_max_dim 512
     ```
     Note: `--batch-size` is not a valid flag for LivePortrait's `inference.py`; omit it.
     Use `--output_dir` (not `--output`) to specify output directory.
     **Path resolution**: Copy source image and driving video into the LivePortrait repo directory before running `inference.py` — it validates input paths relative to CWD.
   - **SadTalker checkpoint typo workaround**: The config references `auido2pose` (missing 'd') instead of `audio2pose`. Use `--old_version` flag and copy source/audio into repo directory to avoid path issues.
   - **EchoMimicV2** — best free audio-driven talking head (Ant Group): natural half-body motion + hand gestures, markedly LESS RIGID than SadTalker; 2026 reviews place it above Hallo2. Needs a **driving pose sequence** on top of image+audio (~12 GB models, ~6 GB VRAM fp16 on 8 GB). See `## EchoMimicV2` section below.

3. **Final Assembly (FFmpeg)**
   - **Background loop for image input**: When background is a static image, use `loop=loop=-1:size=N` where N = driving video frame count (from `ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=noprint_wrappers=1:nokey=1 driving.mp4`).
   - **Face overlay**: Scale animated face to full height, center on background.
   - **Logo overlay**: Scale logo (e.g., 120px wide), position bottom-right with opacity.
   - **Audio mapping**: Map voice audio, use `-shortest` to trim to audio duration.
   - **Encoding**: H.264 CRF 18, preset slow, yuv420p; AAC 192k.
     ```bash
     ffmpeg -y \
       -i background_16_9.png \
       -i animated_face.mp4 \
       -i logo.png \
       -i voice.wav \
       -filter_complex \
       "[0:v]scale=1920:1080,format=yuv420p,loop=loop=-1:size=3262[bg]; \
        [1:v]scale=-1:1080,format=yuva420p[face]; \
        [bg][face]overlay=(W-w)/2:(H-h)/2[bgface]; \
        [2:v]scale=120:-1,format=yuva420p,colorchannelmixer=aa=0.85[logo]; \
        [bgface][logo]overlay=W-w-30:H-h-30[v]" \
       -map "[v]" -map 3:a \
       -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
       -c:a aac -b:a 192k -shortest \
       output.mp4
     ```

2. **Inference (LivePortrait, EchoMimicV2, etc.)**
   - **VRAM Monitoring:** Use `nvidia-smi` to monitor usage. If approaching limits, reduce resolution or close other heavy applications.
   - **Model Selection:** Choose based on need (lips-only vs. full-head) and hardware constraints (see `talking-head-video` skill for model comparison).
   - **LivePortrait V7 settings (best quality for this hardware):**
     ```bash
     --flag_stitching --flag_do_crop --flag_relative_motion --source_max_dim 512
     ```
     Note: `--batch-size` is not a valid flag for LivePortrait's `inference.py`; omit it.
     Use `--output_dir` (not `--output`) to specify output directory.
     **Path resolution**: Copy source image and driving video into the LivePortrait repo directory before running `inference.py` — it validates input paths relative to CWD.
   - **SadTalker driving video:** Use safetensors checkpoints (SadTalker_V0.0.2_512.safetensors) — they load without missing pth files. Output appears in `repo/results/<timestamp>/`.

3. **Assembly (FFmpeg)**
   - **Consistent Encoding:** Force frame rate (`-r 30`) at the OUTPUT only. NEVER `-r 30` as an INPUT option on a 25 fps source — it re-timestamps frames and TRUNCATES the video (376 s → 313 s).
   - **Bitrate:** Use high bitrates for complex detail (e.g., `-b:v 15M` for 1080p).
   - **Codec:** Prefer H.264 or H.265 with high constant quality settings.
   - **Final YouTube assembly (1920×1080, H.264 CRF 18):**
     ```bash
     ffmpeg -y \
       -loop 1 -i portrait_16_9.png \
       -stream_loop -1 -i liveportrait_output.mp4 \
       -loop 1 -i hermes_logo_icon.png \
       -i voice.wav \
       -filter_complex "\
       [0:v]scale=1920:1080,format=yuv420p[bg]; \
       [1:v]scale=-1:900,format=yuva420p[face]; \
       [bg][face]overlay=(W-w)/2:(H-h)/2[bgface]; \
       [2:v]scale=120:-1,format=yuva420p,colorchannelmixer=aa=0.85[logo]; \
       [bgface][logo]overlay=W-w-30:H-h-30[v]" \
       -map "[v]" -map 3:a \
       -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
       -c:a aac -b:a 192k -shortest \
       youtube_final.mp4
     ```
     - Background loops, face loops (stream_loop), logo loops, `-shortest` stops at audio end.
     - Face scaled to height 900, centered; logo scaled to 120px width, top-right with 30px margin.
     - Use `colorchannelmixer=aa=0.85` for logo opacity if PNG has alpha; else add alpha via `format=yuva420p`.

## FFmpeg Opacity Alternance 1s/1s (sans xfade, sans ecran noir)

Pattern 2s boucle via transparence alpha + overlay — deux sources avancent en parallele, V1 au-dessus de V2 :
- Pitfall : `colorchannelmixer=aa='if(eq(mod(floor(t),2),0),1,0)'` est rejete par libavfilter 11.14 sur cette build (erreur filter) — utiliser `geq` avec `alpha(X,Y)` : `geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(eq(mod(floor(T),2),0),alpha(X,Y),0)'` (noter `T` majuscule pour le temps dans geq).

```
[1:v]setpts=PTS-STARTPTS[base];
[0:v]setpts=PTS-STARTPTS,format=yuva420p,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(eq(mod(floor(T),2),0),alpha(X,Y),0)'[fg];
[base][fg]overlay=0:0:format=auto,eq=...[out]
```

- `colorchannelmixer=aa='if(eq(mod(floor(t),2),0),1,0)'` refuse sur libavfilter 11.14 (ce build) — utiliser `geq` avec `alpha(X,Y)` et `T` (pas `t`). Verifier avec test 10s + extraction frames 0.5s=V1, 1.5s=V2 avant encodage complet.
- Etalonnage chain apres overlay : `eq=contrast=1.05:saturation=1.12:brightness=0.005,curves=all='0/0 0.25/0.22 0.75/0.78 1/1'`.
- Encodage complet : `scale/pad/setsar/fps=60` sur chaque branche, `-c:v libx264 -preset veryfast -crf 20 -r 60 -pix_fmt yuv420p -an -movflags +faststart`.

## FFmpeg Single-Pass xfade Montage (5500+ segments, alternance 1s)

Quand alternance A/B mécanique avec transitions sans Premiere/MCP : construire un seul `filter_complex` chaîné via fichier (`-filter_complex_script` obligatoire au-delà de la limite shell) — jamais `-y` sans vérifier `ls -lh` que la sortie n'existe pas et que le fichier protégé (`montage_alternance_5s.mp4`) reste intact. Voir `references/ffmpeg-xfade-montage.md`.

## FFmpeg Opacity Montage 1s/1s (alternance par transparence, sans xfade)

Quand flash-cut 1s V1 / 1s V2 par alpha sans écran noir : V1 au-dessus avec `geq` alpha `if(eq(mod(floor(T),2),0),alpha(X,Y),0)` overlay sur V2, grading après overlay. Voir `references/ffmpeg-opacity-montage.md` — contient le filter validé (FFmpeg 8.1), le piège `colorchannelmixer` qui échoue, et la procédure de test 10s.
- Découper en `trim`+`setpts` par segment (`n` pair A `[(n//2),(n//2)+1]` sinon B, borné à durée `ffprobe`), appliquer `eq` différencié (A 1.05/1.10/0.01, B 1.03/1.08/0.00) + `scale=1920:1080:force_original_aspect_ratio=decrease:eval=frame,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=60`, puis chaîner `[s0][s1]xfade=transition=...:duration=...:offset=...[xf0]` séquentiellement et finir par `curves`+`vignette` global. Valider parse seul `ffmpeg -filter_complex_script ... -map "[xflast_g]" -f null - -t 2` doit retourner 0 avant l'encodage long (`-c:v libx264 -preset medium -crf 20 -r 60 -pix_fmt yuv420p -an -movflags +faststart`, 1-3h, log dans `%TEMP%`). Durée sortie = sum(segments) - sum(transitions).
- Virages : Farneback 320x180 toutes les 2s, `|mean_flow_x|>2.0` => gauche/droit, `1.0-2.0` => incertain, mapping jonction `[t-1,t+1]` : gauche->`wipeleft:0.5`, droit->`wiperight:0.5`, incertain->alterner, aucun->`fade:0.3`. Timeout analyse 900s => fallback fade partout.
Voir `references/ffmpeg-xfade-montage.md` pour le détail complet (calculs offset/durée, comptage transitions).

## Pitfalls

- **Jitter Sensitivity:** AI models like LivePortrait amplify source jitter. If the output looks unstable, stabilize the source FIRST — smooth the driving video with FFmpeg (`smooth_driving_video.py`: `hqdn3d`/`gblur`) into `*_smoothed.mp4` and point `run_liveportrait_volet3.py` `DRIVING` to it (keep `sys.argv[1]` override).
- **FPS Drift:** Any mismatch in FPS throughout the chain leads to stuttering and out-of-sync audio. Set `-r 30` on the OUTPUT only (frame duplication) — the input stays at its native 25 fps (an input `-r 30` truncates duration). In `assemble_final_volet3_blur.py`, put `-r 30` in the encode options, NOT before `-i`.
- **VRAM Saturation:** High-resolution inference will fail or run extremely slowly if VRAM is near capacity. Monitor continuously with `nvidia-smi` BEFORE launching — require ~7+ Go free on 8 Go card; `7.7/8.1 Go + 100% GPU` during LivePortrait starves the Hermes gateway and triggers `shutdown_watchdog` exit 75. For unattended jobs use `deliver=local` on cron, never `deliver=telegram` (blocks event loop).

See `references/ffmpeg-settings.md` for specific encoding settings and `references/jitter-smoothing.md` for pre-processing unstable driving videos. encoding templates.

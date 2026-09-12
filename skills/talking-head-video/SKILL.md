---
name: talking-head-video
description: Lip-sync a portrait to audio into a talking-head video.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wav2lip, lip-sync, talking-head, video, youtube, torch, ffmpeg, tts]
---

# Talking-Head / Lip-Sync Video (Wav2Lip)

## When to Use

- Turn a single portrait/selfie + a narration audio into a video where the lips
  move with the speech (YouTube "faceless" avatar, explainer, promo).
- Pair with a cloned TTS voice (see `tts-voice-cloning`) for a fully AI-narrated video.
- NOT for photorealistic deepfakes — both tools produce clearly-AI output. Set
  that expectation up front: neither is true 4K (Wav2Lip ~720p, SadTalker 512×512;
  a 4K full-screen result is an upscale that goes soft).

## Choosing the tool

- **Wav2Lip** — lips-only: STATIC face, moving lips (96×96 mouth). Lighter/faster.
- **SadTalker** — full talking head: head pose + eyes/blink + neck + lips from a
  single image. Heavier (~2.5 GB models, ~8 GB VRAM, slow). Use when the user asks
  for "eyes, neck, head" movement, not just lips. Known to look a bit **rigid**.
  - **Checkpoint format:** Use `.safetensors` (SadTalker_V0.0.2_512.safetensors) — loads without missing `.pth` files.
  - **Output location:** Results appear in `repo/results/<timestamp>/` subdirectory.
  - **Old version flag:** Use `--old_version` when loading older checkpoint formats.
- **EchoMimicV2** — best free audio-driven talking head (Ant Group): natural
  half-body motion + hand gestures, markedly LESS RIGID than SadTalker; 2026
  reviews place it above Hallo2. Needs a **driving pose sequence** on top of
  image+audio (~12 GB models, ~6 GB VRAM fp16 on 8 GB). See `## EchoMimicV2` +
  `references/echomimic-v2-setup.md`.
- **LivePortrait** — best quality for re-enactment (driving video + source image):
  - **V7 settings (validated on RTX 3070 Ti 8 GB VRAM):**
    `--flag-stitching --flag-do-crop --flag-relative-motion --source-max-dim 512`
  - `--batch-size` is NOT a valid flag for `app.py`/`inference.py`/`run_liveportrait.py` — omit.
  - Source image should be square (512×512 or 1024×1024); driving video from SadTalker works well.
  - Output: `face_liveportrait.mp4` in `--output_dir`.
  - Patches for insightface CPU fallback already in place (CUDA 13.3 incompatible with onnxruntime-gpu 1.18).
- **MiniMax H3 (cloud API)** — image + text → talking portrait with no local
  GPU. Async: `POST https://api.minimax.io/v2/video_generation` (model
  `MiniMax-H3`) → poll `/v2/query/video_generation` for the URL. Requires a
  valid `eyJ...`-style MiniMax key (a `Sk-api-` key is rejected 1004 on every
  host). Full recipe in the `omniroute-gateway` skill's
  `references/minimax-provider.md`.

## LivePortrait (Recommended for Realism)

- **Best for Motion Control:** VIDEO-DRIVEN (not audio-driven). Uses a driving
  video (e.g. a SadTalker output) to transfer natural expressions + head movement
  onto a 1024×1024 source portrait.
- **Workflow:** 1. Generate driving video (SadTalker/EchoMimic) with audio -> 2. Transfer to 1024 portrait with LivePortrait.
- **Paramètres optimisés :**
  - `--flag_stitching` et `--flag_do_crop` : pour un meilleur alignement.
  - `--flag_relative_motion` : booléen, **défaut = True**. Le mouvement relatif normalise l'amplitude → bouche fermée (« dents serrées ») + jitter frame-à-frame (« l'image saute »). Pour une bouche ouverte et stable : `--no-flag_relative_motion` (mouvement absolu) + `--driving_multiplier 1.2` (amplification de la bouche). Retirer le flag NE suffit PAS — le défaut est déjà True.
  - `--flag_pasteback` : **CRITIQUE** pour éliminer les effets de miroir/clignotement sur les bords en réintégrant le visage dans le cadre original.
  - `--source_max_dim 512` : privilégier 512 pour la fluidité sur 8GB VRAM.
  - **Stabilisation (Denoising) :** LivePortrait est extrêmement sensible au jitter de la vidéo de conduite. Appliquez toujours un filtre de débruitage temporel (ex: `FFmpeg -vf hqdn3d=1.5:1.5:6:6`) sur la vidéo de conduite *avant* l'inférence.

## Lessons and Pitfalls

- **Driving Video Mismatch:** NEVER reuse an old driving video (from a previous script) for a new audio track. Lip-sync is tied to the driving video's timing; using an old one will result in \"mismatched mouth\" syndrome. Always re-run the audio-driven stage (SadTalker) before the video-driven stage (LivePortrait) when audio changes.
- **Verify LivePortrait flags against `argument_config.py` before running.** AI-generated commands carry non-existent flags (`--flag_use_cuda`, `--flag_absolute_motion`, `--mouth_ratio`, `--lip_sync_strength`, `--frame_smooth_window`, `--output_fps`). The real list is the `ArgumentConfig` dataclass (`src/config/argument_config.py`); CUDA is the default (the inverse is `--flag_force_cpu`). An unknown flag makes tyro fail immediately.
- **ONNX/CUDA Conflict (Windows):** Windows systems with CUDA 13.3+ and `onnxruntime-gpu` < 1.19 will crash if `insightface` or `HumanLandmark` try to use `CUDAExecutionProvider`.
  - **Fix:** Patch `model_zoo.py` (insightface) and `cropper.py` (LivePortrait) to force `providers=['CPUExecutionProvider']`. See `references/liveportrait-troubleshooting.md`.
- **Dents invisibles / bouche « fermée » :** SadTalker SANS `--enhancer gfpgan` rend les dents floues → impression de bouche fermée. Toujours `--enhancer gfpgan --preprocess full --size 512 --still` pour des dents nettes. La bouche ne s'ouvre qu'aux voyelles (moments de parole) — vérifier plusieurs frames. Source 1024×1024 nette (une source 512 floue donne un visage flou après upscale).
- **Sorties SadTalker (`--preprocess full`) :** deux mp4 sont produits — `...mp4` (crop 512×512, visage seul) et `..._full.mp4` (1024×1024, visage + fond). Pour l'assemblage fond flou, utiliser le `_full.mp4` : visage plus net (moins d'upscale) + fond propre à flouter.
- **Cadrage YouTube (photo source) :** recadrer/adapter la photo au format de la fenêtre YouTube (16:9 / vignette) AVANT l'animation — un simple crop centré ne suffit pas. Vérifier le cadrage final à l'écran YouTube.
- **Diction Issues:** Words like "Hermes Agent" may be cut. Use phonetic spelling (e.g., "Hermès ... Agent") in the TTS script.
- **VRAM Exhaustion (SadTalker/LivePortrait):** Sur 8GB VRAM, une saturation entraîne des échecs d'écriture du fichier final (`moov` atom absent). Vérifiez `nvidia-smi` avant tout rendu long.
- **Fluidité de lecture (Assembly):** PAS de `-r 30` en ENTRÉE — sur une source 25 fps, `-r 30 -i FACE` force 30 fps et TRONQUE la durée (376 s → 313 s, ratio 1.2). Laisser l'entrée à son fps natif ; `-r 30` uniquement en SORTIE (duplication de frames).
- **Fond d'assemblage : flou, pas miroir.** Le reflet vertical (vflip + vstack + scale) étire le visage en largeur et paraît déformé. L'utilisateur préfère un fond classique flou : visage net centré (1080×1080) sur un arrière-plan `gblur=sigma=30` de la même image étirée en 1920×1080.
- **Persist pipeline state to memory before launching a long render.** The chain (TTS → SadTalker → LivePortrait → assemble) runs ~1h and sessions get interrupted; un-persisted state forces the next session to re-derive commands and re-hit already-known errors. Before launching, save the current stage + exact commands + known issues to memory — this is a standing user requirement.

## Reference Files
- `references/echomimic-v2-setup.md`
- `references/models-and-deps.md`
- `references/liveportrait-troubleshooting.md` (ONNX/CUDA patches)
- `scripts/gfpgan_upscale.py`

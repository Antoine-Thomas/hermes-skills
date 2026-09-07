---
name: liveportrait-pipeline
description: "Animation faciale avec LivePortrait : optimisation GPU, assemblage fond/logo, CHUNK stitching."
version: 1.0.0
author: searching-murphy
license: MIT
metadata:
  hermes:
    tags: [liveportrait, face-animation, gpu, youtube, video, ffmpeg, portrait]
    related_skills: [talking-head-video, tts-voice-cloning, video-youtube-assembly]
---

# LivePortrait Pipeline

Animation faciale réaliste à partir d'une photo source + vidéo d'animation (driving video).

## Quand utiliser

- Transformer un portrait/statique en vidéo parlante avec mouvements naturels (tête, yeux, expressions).
- Produire un avatar YouTube avec un rendu plus réaliste que SadTalker (plus de fluidité, moins de raideur).
- Assemblage final avec fond animé (bois), logo Hermes, et CTA en fin de vidéo.

## Prérequis

- **GPU**: RTX 3070 Ti ou mieux (≥ 8 GB VRAM)
- **Python 3.11** dans un venv dédié (`liveportrait/repo/venv`)
- **FFmpeg** installé et accessible
- **PyTorch 2.5.1+cu124** (CUDA)
- **Modèle**: télécharger les poids depuis le repo GitHub officiel

## Installation

```bash
# Cloner le repo LivePortrait
cd data/video_youtube
git clone https://github.com/KwaiVGI/LivePortrait.git liveportrait/repo
cd liveportrait/repo
python -m venv venv
source venv/Scripts/activate  # Windows
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
pip install insightface onnxruntime-gpu
```

## Utilisation

### 1. Animation simple

```bash
python run_liveportrait.py \
  --source_image photo_1024.png \
  --driving_video sadtalker_512_v3.mp4 \
  --output_dir output/
```

### 2. Assemblage CHUNK (recommandé)

Si la driving video est longue, diviser en chunks de 3-5 secondes :

```bash
python assemble_liveportrait_final.py \
  --chunks_dir output/ \
  --driving_video sadtalker_512_v3.mp4 \
  --bg_video fond_bois.mp4 \
  --logo logo_hermes.png \
  --output final_video.mp4
```

## Configuration

### Paramètres clés (dans `head_animation_config.yaml`)

| Paramètre | Valeur recommandée | Description |
|-----------|-------------------|-------------|
| `source_image` | 1024×1024 | Photo source (carrée, haute résolution) |
| `driving_video` | 512×512 | Vidéo d'animation (animation de tête) |
| `flag_do_crop` | true | Recadrage automatique du visage |
| `flag_stitching` | true | Suture des bords (réduit les artefacts) |
| `flag_pasteback` | true | Collage du visage animé sur le fond |
| `device` | cuda | GPU (ou cpu si pas de GPU) |

### Fonds et overlays

- **Fond bois**: `fond_bois.mp4` — animation subtile, PAS de fond blanc
- **Logo Hermes**: `logo_hermes.png` — positionné en coin (top-right ou bottom-right)
- **CTA fin**: like/abonnement en fin de vidéo, sans sous-titres

## Optimisation GPU

- **Batch mode**: traiter plusieurs frames en parallèle (augmente le VRAM utilisé)
- **FP16**: réduit la VRAM de moitié (`--dtype fp16`)
- **MAX_CHUNK_SIZE**: limiter la taille des chunks si VRAM limitée

## Assemblage final

L'assemblage combine :
1. **Chunks LivePortrait** (vidéo animée du visage)
2. **Fond animé** (bois, arrière-plan)
3. **Logo Hermes** (overlay en coin)
4. **Audio** (depuis XTTS ou autre TTS)
5. **CTA** (call-to-action en fin)

FFmpeg assemble le tout :
```bash
ffmpeg -i fond_bois.mp4 -i audio.wav -i logo.png \
  -filter_complex "[0:v][2:v]overlay=W-w-20:20[v]" \
  -map "[v]" -map 1:a -c:v libx264 -c:a aac final.mp4
```

## Problèmes connus

- **VRAM insuffisante**: réduire la résolution du driving video ou utiliser `--dtype fp16`
- **Artefacts de bord**: activer `flag_stitching=true`
- **Visage rigide**: augmenter l'amplitude des mouvements dans la config
- **Chunks désynchronisés**: vérifier les timestamps entre chunks

## Voir aussi

- `talking-head-video` : pipeline complet (SadTalker + LivePortrait + assemblage)
- `tts-voice-cloning` : clonage vocal XTTS-v2 pour la narration
- `video-youtube-assembly` : assemblage final avec fond/logo/audio

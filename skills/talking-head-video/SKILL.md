---
name: talking-head-video
description: Lip-sync a portrait to audio into a talking-head video.
version: 1.0.0
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
- Pair with a cloned TTS voice (see `vibevoice-tts`) for a fully AI-narrated video.
- NOT for photorealistic deepfakes — both tools produce clearly-AI output. Set
  that expectation up front: neither is true 4K (Wav2Lip ~720p, SadTalker 512×512;
  a 4K full-screen result is an upscale that goes soft).

## Choosing the tool

- **Wav2Lip** — lips-only: STATIC face, moving lips (96×96 mouth). Lighter/faster.
- **SadTalker** — full talking head: head pose + eyes/blink + neck + lips from a
  single image. Heavier (~2.5 GB models, ~8 GB VRAM, slow). Use when the user asks
  for "eyes, neck, head" movement, not just lips. Known to look a bit **rigid**.
- **EchoMimicV2** — best free audio-driven talking head (Ant Group): natural
  half-body motion + hand gestures, markedly LESS RIGID than SadTalker; 2026
  reviews place it above Hallo2. Needs a **driving pose sequence** on top of
  image+audio (~12 GB models, ~6 GB VRAM fp16 on 8 GB). See `## EchoMimicV2` +
  `references/echomimic-v2-setup.md`.

## LivePortrait (Recommended for Realism)

- **Best for Motion Control:** VIDEO-DRIVEN (not audio-driven). Uses a driving
  video (e.g. a SadTalker output) to transfer natural expressions + head movement
  onto a 1024×1024 source portrait. Superior realism to SadTalker/Wav2Lip.
- **Workflow:** source image (1024×1024) + driving video (e.g. `sadtalker_512_v3.mp4`)
  → `inference.py` → 1024×1024 animated portrait (audio copied from the driving
  video via `--audio_priority driving`).
- **DRIVING VIDEO MUST BE 512×512, not 256.** A 256×256 driving face is too
  small for LivePortrait's landmark extraction → distorted mouth + unacceptable
  lip-sync (user rejected a 256-driving render: « grave erreur sur la forme de la
  bouche »). SadTalker `--size 256` is fine for STANDALONE output, but re-run at
  `--size 512` when the SadTalker mp4 will feed LivePortrait as the driving video
  (512 was accepted in v4; 256 broke the mouth). The 256→512 change means the
  slow path (~5-14 h for a 5-min voice) — budget accordingly.
- **If LivePortrait's mouth is still rejected even at 512, FALL BACK to SadTalker
  direct** (no LivePortrait): assemble the SadTalker 512 mp4 straight onto the
  animated bg + title + logo (see `assemble_final_v3.py`) — lip sync is correct
  but the face is upscaled 512→1080 (softer). The user's final call this session
  was to abandon LivePortrait for this video and go SadTalker-512-direct.
- **Setup:** `liveportrait/repo/` + dedicated venv (`repo/venv`, torch 2.5.1+cu124).
  Models in `repo/pretrained_weights/` (base_models, insightface, landmark.onnx,
  retargeting). Run from `repo/` with the venv python by full path.

### CLI args (this repo — NOT `--size`)
`inference.py --source <img> --driving <video|.pkl> --output_dir <dir>`.
Output size follows the SOURCE (1024×1024), not a `--size` flag. Other flags:
`--flag_relative_motion` (default True, "expression-friendly"), `--flag_pasteback`,
`--flag_stitching`, `--audio_priority driving|source`.

### CRITICAL: incremental-write patch (long videos OOM/crawl)
The stock `src/live_portrait_pipeline.py` accumulates EVERY pasteback frame
(1024×1024×3 ≈ 3 MB) in `I_p_pstbk_lst` before writing the mp4 at the END — ~20 GB
for a 5-min render, which makes the animation loop crawl from ~3 fps to ~0.02 fps
(observed: 18 h and counting, no output written). FIX (already applied, re-apply
if the repo is re-cloned): open an imageio writer before the loop and write each
`I_p_pstbk` frame incrementally instead of appending, close after the loop, skip
the post-loop `images2video(I_p_pstbk_lst, ...)`. MUST `mkdir(args.output_dir)`
BEFORE `imageio.get_writer` (stock `mkdir` is after the loop → FileNotFoundError).

### Scripts (all in `data/video_youtube/`)
- `liveportrait/run_liveportrait.py` — wrapper (`--source_image --driving_video
  --output_dir`); returns the newest non-`_concat` mp4 in the output dir.
- `assemble_final_v4.py` — single-render assembly: animated bg (looped) + face
  centered 1080×1080 on 1920×1080 + optional title card + watermark logo, NVENC.
- `assemble_liveportrait_final.py` — CHUNK assembly: concat `tr_*.mp4` (natural
  sort, `-f concat -safe 0 -c copy`), loop bg with `-stream_loop -1`, center face,
  logo bottom-right, add audio, NVENC 1080p. Use when rendering the driving video
  in ~15 s chunks (parallel / fault-tolerant) instead of one long render.
- `build_youtube_v2.py` — unified: LivePortrait → assembly → export.
- Driving video for the FULL render = the SadTalker output WITH audio
  (`sadtalker_512_v3.mp4`); the motion template is cached as `<driving>.pkl` (pass
  `--driving <file>.pkl` to skip the ~25 min template extraction, but you then
  lose the driving audio and must add it in assembly).

## SadTalker Upscaling & Quality Optimization

- SadTalker renders natively at 512×512. Post-process upscaling (Lanczos/FFmpeg) often yields soft results.
- **Best Quality Patch:** Force face restoration *during* rendering to prevent detail loss.
  - Use `--enhancer gfpgan` (if model is in `checkpoints/`) or `--enhancer codeformer` (downloads ~376MB).
  - Use `--preprocess full` instead of `--still` to respect 1024×1024 source aspect ratios.
  - Required Checkpoint: Ensure `checkpoints/epoch_20.pth` is present (for 3DMM extraction).
  - Pipeline Tip: Always run from the repo's parent data directory using the local `venv`, not globally. Use `--enhancer gfpgan` in the inference call:
  ```bash
  python inference.py --driven_audio "<audio_file>" --source_image "<portrait_1024_path>" \
    --enhancer gfpgan --preprocess full --size 512
  ```
- **Pitfall:** `--still` does not exist in the base repo. Use `--preprocess full` to handle 1024×1024 source images without destructively cropping the portrait.
- **Model Check:** `codeformer` is listed as a choice but requires downloading a 376MB checkpoint on demand; `gfpgan` (v1.4) is typically pre-cached in `checkpoints/` and is highly effective for full-body portraits.

Repo `antgroup/echomimic_v2`. Full Windows/8 GB setup, exact model list, and the
dependency pitfalls (`clip` build failure, `onnxruntime-gpu` version, `transformers`
vs `diffusers` clash, the `refimg_name` path bug): `references/echomimic-v2-setup.md`.

### Portrait prep (Windows, ffmpeg)
EchoMimicV2 expects a **square 768×768** reference image. For a 16:9 landscape
portrait (e.g. 1920×1080), crop center + scale:
```bash
ffmpeg -y -i portrait.png -vf "crop=ih:ih:(iw-ih)/2:ih*0.1,scale=768:768" ref/portrait.png
```
The `ih*0.1` offset keeps the face near the top (important for capuche/hoodie
portraits where the face sits above center). Verify: `python -c "from PIL import
Image; print(Image.open('ref/portrait.png').size)"` must print `(768, 768)`.

- Inputs = reference image + audio + a **pose sequence** (dir of `.npy` DWPose
  keypoints, one per frame). NOT image+audio alone. Extract pose from a source
  (e.g. a SadTalker run, or the repo's `assets/halfbody_demo/pose/*` demos) via
  `src/models/dwpose/` (needs DWPose `.onnx` models — not in the repo).
- `infer.py` renders a fixed-length clip (default `-L 240` = 10 s @ 24 fps); a
  5-min voice means slicing the audio into clips, running each, then concatenating.
- `--refimg_name` MUST contain a `/` (e.g. `ref/portrait.png`) or infer.py line 170
  (`refimg_name.split('/')[-2]`) raises IndexError.

### Smoke test (validates full pipeline on 8 GB VRAM)

**Use `infer_acc.py` + `infer_acc.yaml` (the `_acc` weights), NOT `infer.py`.**
On an 8 GB card `infer.py` (original weights) STALLS: VRAM pins at ~7850/8192 MiB
and the denoising loop sits at `0/10` steps indefinitely — it loads the SD base
model fine but never advances. The `_acc` variant runs the same smoke test to
completion (~23 s/step, 48 frames in ~3.7 min).

```bash
cd echomimic_v2
ffmpeg -y -i voix.wav -t 3 -ac 1 -ar 16000 audio_3s.wav
venv/Scripts/python.exe infer_acc.py --config ./configs/prompts/infer_acc.yaml \
  --ref_images_dir . --refimg_name ref/portrait.png \
  --audio_dir . --audio_name audio_3s.wav \
  --pose_dir ./assets/halfbody_demo/pose --pose_name 01 -L 48 --steps 10 --seed 3407
```
`weight_dtype: 'fp16'` (in `infer_acc.yaml`) keeps VRAM ~6 GB. Output:
`outputs/<model_flag>-seed<seed>/.../_sig.mp4`. `triton` is reported missing —
harmless (xformers falls back to sdpa). For full-length audio expect 1-3 h.

### Full production workflow
1. Prepare portrait (square 768×768, see portrait prep above)
2. Generate audio with VibeVoice/MaVoix (see `vibevoice-tts` skill — Docker required)
3. Pick pose: `assets/halfbody_demo/pose/01` = natural halfbody + hand gestures.
   For custom pose from a real video, see `references/echomimic-v2-setup.md`
   § Pose sequence (needs DWPose ONNX models, not bundled).
4. Run inference: `-L <frames>` matching audio duration (`frames = seconds × 24`)
5. Assemble final: portrait centered, blurred background, logo overlay, 1080p,
   no subtitles. Output to user-specified directory (typically Desktop).

## SadTalker (full-head animation)

Repo `OpenTalker/SadTalker`. Models are NOT in the repo — download from GitHub
releases (direct links, no HF redirect); exact URLs in `references/models-and-deps.md`.
Needs `facexlib` + `gfpgan` in ADDITION to core deps.

```bash
uv pip install --python venv/Scripts/python.exe "numpy==1.23.5" "kornia==0.7.3" "scikit-image==0.22.0" einops safetensors yacs face-alignment imageio imageio-ffmpeg av pyyaml resampy pydub facexlib basicsr gfpgan
# then re-pin torch CUDA (see pitfalls) and verify torch.cuda.is_available()
```

Run:

```bash
cd repo
../venv/Scripts/python.exe inference.py --driven_audio <wav> --source_image <photo> \
  --result_dir results --preprocess crop --size 512
```

- **Venv path**: there is NO pre-built shared venv in practice — build a DEDICATED
  one at `sadtalker/venv/`. The system `python` has NO torch, so always call the
  venv's `python.exe` by full path. Torch build: `torch==2.5.1+cu124` (cu124 index)
  worked cleanly.
- **GFPGAN is imported HARD in `src/utils/face_enhancer.py`** — a bare
  `from gfpgan import GFPGANer` at line 4. If gfpgan/basicsr are not installed
  (they pull a torch build that breaks, and scikit-image won't compile on
  Python 3.11/Windows). NOTE: the repo's `gfpgan/` submodule ships ONLY `weights/`
  (the checkpoints) — no `.py` source — so the import returns None even when the
  dir exists. To ENABLE `--enhancer gfpgan` (fixes crooked teeth): `pip install
  gfpgan basicsr` (the PyPI package IS the source) + the functional_tensor patch
  (pitfall 7). Only fall back to the try/except (run WITHOUT the enhancer) if you
  don't need face restoration:
  patch it to a try/except so inference runs WITHOUT the
  face enhancer:
  `try: from gfpgan import GFPGANer` / `except ImportError: GFPGANer = None`.
- **scikit-image fails to build from source on Windows/Python 3.11**
  (CCompilerOpt error), and `requirements.txt` pins it plus gfpgan/basicsr/face-alignment.
  Filter those out of `requirements.txt` before `pip install -r`, then install
  `safetensors` (imported by `preprocess.py`) separately. `imageio` must be pinned
  `==2.31.5` + `imageio-ffmpeg==0.4.9` or inference dies with
  `RecursionError: maximum recursion depth exceeded` in the imageio plugin loader.
- `--enhancer gfpgan` = face restoration — REQUIRED to fix the 3DMM crooked-teeth artifact (user: « les dents sont de travers »); without it the teeth look distorted even though lip-sync is correct. Trade-off: GFPGAN itself leaves a faint ghost « double contour » at the hoodie/teeth edges (restored face vs original) that the user may still reject as « dédoublement » after the background is fixed — re-render with `--enhancer codeformer` (cleaner edges, ~376 MB download on first use) if so. `--still` = freeze head pose (faster/less
  VRAM) — OMIT `--still` when the user wants head/eye/neck movement.
- Runtime at 512, no `--still`, on an 8 GB card is ~0.16–0.5 fps ≈ **5–14 h for a
  5-min audio** (observed 13.8 h and still generating on an RTX 3070 Ti). On an
  8 GB card PREFER `--size 256 --batch_size 4`: full head movement, ~4× faster,
  ~5.4 GB VRAM (vs ~7.7 GB at 512). Run in background with notify; only kill if it
  has run far past the estimate (see pitfall 8).
- **The mid-render ~25× slowdown is a VRAM-accumulation BUG — PATCH IT, don't just wait.** `src/facerender/modules/make_animation.py` loops over every frame doing `predictions.append(out['prediction'])` then `torch.stack(predictions, dim=1)` — it holds ALL frames as GPU tensors in VRAM (~6.2 GB for a 5-min voice at 256×256 internal). VRAM climbs to ~96% (7.9/8 GB) → CUDA thrash → speed drops from ~2.3 img/s to ~0.03–0.09 img/s (11–37 s/img), turning a ~1 h render into 25–35 h. FIX (one line, re-apply if the repo is re-cloned): `predictions.append(out['prediction'].cpu())` — move each frame to RAM (64 GB box) so VRAM stays ~5.2 GB and speed holds ~2.25 img/s (~56 min for a 5-min voice). `--batch_size 1` vs `2` does NOT fix it (batch 1 starts at lower VRAM but still accumulates); `.cpu()` is the real fix. Verify: `nvidia-smi` VRAM flat ≈ patched; VRAM climbing to ~8 GB mid-render = unpatched.
- Output lands at `results/<YYYY_MM_DD_HH.MM.SS>.mp4` (the timestamped dir + `.mp4`):
  `inference.py` does `shutil.move(result, save_dir+'.mp4')` then **DELETES** the
  intermediate dir (`.mat`/`.txt`/`first_frame_dir/`) unless `--verbose`. It
  INCLUDES the audio track.
- The output is a **512×512 SQUARE**. To fill a 16:9 4K screen, CROP (never
  stretch): `-vf "scale=3840:3840:flags=lanczos,crop=3840:2160:0:840"` then NVENC.
  This is a ~7.5× upscale and goes soft — the hard quality ceiling for
  SadTalker→4K. Center crop keeps eyes/nose/mouth and trims forehead+chin; raise
  the `y` offset (e.g. `0:1000`) to keep more chin for a talking head.
- Concatenating a title card + the talking head: normalise BOTH audio streams
  first or `concat` mangles/mutes them (title silence is 44.1 kHz stereo, TTS
  voice is 24 kHz mono):
  `[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0];[1:a]aformat=...[a1]`

## Pipeline

```
script (narration) → TTS voice (VibeVoice) → Wav2Lip OR SadTalker → [GFPGAN+Real-ESRGAN] → upscale 4K → overlays + logo → final mp4
```

## GFPGAN + Real-ESRGAN post-upscale (quality boost)

When SadTalker ran at `--size 256` for speed (see above) but the user wants a
sharper 4K result, restore + 2×-upscale the frames with GFPGAN + Real-ESRGAN
BEFORE the 4K Lanczos upscale (256→512→4K beats a straight 15× 256→4K stretch).
Full working script: `scripts/gfpgan_upscale.py`.

Setup (the wav2lip venv has NO pip — use `uv`, and `realesrgan` is NOT bundled
with `gfpgan`/`basicsr` — you must install it):
```bash
uv pip install --python venv/Scripts/python.exe realesrgan --no-deps
curl -sL -o gfpgan/weights/RealESRGAN_x2plus.pth \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth
```

Core (RRDBNet + RealESRGANer wired as GFPGAN's `bg_upsampler`):
```python
from gfpgan import GFPGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
m = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
up = RealESRGANer(scale=2, model_path="RealESRGAN_x2plus.pth", model=m, tile=0, tile_pad=10, pre_pad=0, half=True)
r = GFPGANer(model_path="GFPGANv1.4.pth", upscale=2, arch='clean', channel_multiplier=2, bg_upsampler=up)
_, _, out = r.enhance(img, has_aligned=False, only_center_face=True, paste_back=True, weight=0.5)
```

- ~2.3 img/s on an RTX 3070 Ti (7973 frames ≈ 57 min) — run in background with notify.
- Extract with `ffmpeg -i in.mp4 -qscale:v 1 %05d.png`; reassemble preserving the
  original audio: `ffmpeg -framerate 25 -i out/%05d.png -i in.mp4 -map 0:v -map 1:a -c:a copy out_512.mp4`.
- `weight=0.5` = balanced restore (higher = stronger GFPGAN face; lower = closer
  to the source). `half=True` needs a CUDA GPU that does FP16 (RTX 30xx+ is fine).

## Wav2Lip setup (Windows, Python 3.11, NVIDIA GPU)

The official repo (`Rudrabha/Wav2Lip`) pins ANCIENT deps (torch 1.1.0, numpy 1.17.1,
librosa 0.7.0) that fail on Python 3.11. Ignore `requirements.txt`; install modern
versions:

```bash
uv venv --python "C:/Users/<you>/AppData/Local/Programs/Python/Python311/python.exe" venv
uv pip install --python venv/Scripts/python.exe torch --index-url https://download.pytorch.org/whl/cu121
uv pip install --python venv/Scripts/python.exe "numpy==1.23.5" librosa opencv-python scipy tqdm numba
git clone --depth 1 https://github.com/Rudrabha/Wav2Lip.git repo
```

- `numpy==1.23.5` is REQUIRED: the repo uses `np.int` (removed in numpy 1.24).
- Models are NOT in the repo; download from the HF mirror `camenduru/Wav2Lip`:
  - `checkpoints/wav2lip_gan.pth` (~435 MB) ← `resolve/main/checkpoints/wav2lip_gan.pth`
  - `face_detection/detection/sfd/s3fd.pth` (~89 MB) ← `resolve/main/face_detection/detection/sfd/s3fd.pth`

## REQUIRED code patch — librosa 0.11 API break

`repo/audio.py` ~line 100 calls `librosa.filters.mel(...)` with POSITIONAL args,
which librosa ≥0.10 rejects (keyword-only). Fix:

```python
# before (fails: "mel() takes 0 positional arguments but 2 ... given")
return librosa.filters.mel(hp.sample_rate, hp.n_fft, n_mels=hp.num_mels, fmin=hp.fmin, fmax=hp.fmax)
# after
return librosa.filters.mel(sr=hp.sample_rate, n_fft=hp.n_fft, n_mels=hp.num_mels, fmin=hp.fmin, fmax=hp.fmax)
```

(`save_wav` uses scipy `wavfile.write`, NOT `librosa.output` — that path is fine.)

## Run

```bash
cd repo
../venv/Scripts/python.exe inference.py \
  --checkpoint_path checkpoints/wav2lip_gan.pth \
  --face <portrait.jpg> --audio <voice.wav> \
  --outfile results/lipsync_720p.mp4 --fps 25
```

- `--face` may be `.jpg/.png` (auto-detects a static image). Face must be clear and
  frontal or the s3fd detector finds nothing.
- Output is at the portrait's native res and INCLUDES the audio; upscale afterward
  (`ffmpeg -vf scale=3840:2160:flags=lanczos -c:a copy`).
- For a 4K full-screen result: lip-sync at native res (~720p), then upscale ONCE —
  the mouth region is 96×96 upscaled to the face box and goes soft at 4K regardless.

## Text overlays + 4K assembly

- Render lower-third text as transparent 4K PNGs (PIL + a font; auto-shrink long
  lines), one per section.
- Overlay with timed `enable`: `-loop 1 -i overlay_NN.png` then
  `overlay=0:0:enable='between(t,START,END)'`, chained for N sections. A static logo
  watermark overlays once with no `enable`.
- Time sections by word-count proportion of the script first; refine with
  faster-whisper word timestamps only if frame-accuracy matters.

## YouTube delivery — this user's preference

- **4K with sharpened piqué — the user now WANTS this.** Note the reversal: an
  earlier session recorded "1080p, NOT 4K / n'upscale pas". That preference is
  SUPERSEDED. The user complained the 512-native render looked "trop médiocre /
  pixelisé par rapport à la photo" and asked for a 4K render that is at least as
  sharp as the source photo. Deliver 4K (3840×2160) with the sharpening pipeline
  below, AND keep the 1080p version alongside (never overwrite).
- **Fast 4K sharpening pipeline (verified this session, ~1-3 min per clip via
  NVENC):** the Real-ESRGAN `x2plus` path was tried and is FAR too slow on 8 GB
  (~20 frames/min → hours for a 4.5-min clip). Use FFmpeg double-unsharp +
  Lanczos + NVENC instead — near-instant and visibly sharper than a bare upscale:
  `-vf "unsharp=5:5:1.5:3:3:0.8,scale=3840:2160:flags=lanczos,unsharp=5:5:0.5:3:3:0.3,eq=brightness=0.02:contrast=1.05"`
  with `-c:v h264_nvenc -preset p5 -cq 20 -b:v 0`. The first unsharp sharpens the
  512 source, the second restores edge crispness after the 7.5× Lanczos stretch.
  Be honest with the user: this sharpens but does NOT add real detail beyond the
  512×512 native — the hard ceiling is SadTalker's output resolution.
- **Center the square face on a 16:9 1080p canvas over a BLURRED PORTRAIT
  background** — no black bars, and do NOT crop to 16:9 (the face is already
  framed; cropping trims forehead/chin). Blur+darken the portrait, scale the face
  to 1080×1080, overlay centered:
  `[1:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=28,eq=brightness=-0.25[bg];[0:v]scale=1080:1080:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2`
- **Animated background (this user asked for « fond animé Hermes »).** Alternative to the static blurred background: a looping animated teal/gold gradient with floating gold particles. Generate ~8 s of 1920×1080 frames with numpy+PIL (flowing cyclic gradient `DARK→TEAL→LIGHT→GOLD→DARK` + drifting dots), then:
  `ffmpeg -framerate 25 -i bg_frames/%05d.png -c:v libx264 -crf 18 bg_loop.mp4`
  `ffmpeg -stream_loop -1 -i bg_loop.mp4 -t <audio_duration> -c:v libx264 animated_bg.mp4`
  then overlay the face on `animated_bg.mp4` (same `overlay=(W-w)/2:(H-h)/2` + `-shortest`). The palette lerp uses numpy fancy-indexing (`palette[idx]` with `idx` an int array) — a naive `stops[s][ch]` list-comp over a numpy array raises `TypeError: only integer scalar arrays can be converted to a scalar index`.
- **REVERSAL (latest): white background + big Hermes logo.** The user later
  said « tu as oublié fond blanc avec logo Hermes » — the white background + big
  Hermes logo is now preferred OVER the animated teal/gold background (see
  `assemble_final_v5.py`: `-f lavfi -i color=white:s=1920x1080:r=25` + big
  `hermes_logo_icon.png` scale 1800, `colorchannelmixer=aa=0.60`, centered behind
  the portrait). **On WHITE the logo needs aa≥0.60 — at 0.35 it is effectively
  invisible** (NVIDIA vision reported no logo visible at 0.35); bump to 0.60 +
  ~1800 px and verify with a vision check before delivering. Keep the animated-bg
  path available but ask/confirm which the user wants before rendering.
- **REVERSAL (final): match the SOURCE PHOTO's background + logo VISIBLE in a
  corner.** After the white-bg version, the user said « le logo est caché derrière
  l'animation ... le fond utilisé doit être comme le fond de la photographie
  animée ». Two corrections: (1) the background must MATCH the source photo's own
  background (this user's portrait sits on a brown/wood wall) — NOT white, NOT the
  animated teal/gold. Achieve it by blurring the SadTalker OUTPUT ITSELF as the
  background layer (it already carries the photo's wood background):
  `-vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=25:5"`
  then overlay the sharp face centered (see `assemble_final_v6.py`). (2) A big
  centered logo BEHIND the portrait is hidden — the user explicitly rejected it
  (« caché derrière l'animation »). Put the Hermes logo VISIBLE in a corner
  instead: `hermes_logo_icon.png` (transparent, 1024²) scale ~320px, native alpha,
  `overlay=W-w-40:40` (top-right). `hermes_logo_full.png` has an OPAQUE black
  background (corner alpha 255) — don't overlay it; use the `_icon` variant.
  Verify logo + background with a NVIDIA vision check before delivering.
- **REVERSAL (V7): `boxblur=25` background creates DOUBLE EDGES (dédoublement).**
  Blurring the SadTalker output ITSELF as the bg layer (boxblur 25) still leaves
  the blurred face faintly visible BEHIND the sharp face → user: « dédoublement
  graphique des bords au niveau de la capuche et des dents » (ghost hoodie/teeth
  edges + motion blur). FIX: use a SOLID wood-color background (uniform, matching
  the photo's wood tone — `-f lavfi -i color=c=0x7d562a:s=1920x1080:r=25`) and
  feather the face's left/right edges into it so the 1080×1080 square has no hard
  boundary:
  `geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='if(lt(X,100),X/100*255,if(gt(X,W-100),(W-X)/100*255,255))'`
  geq GOTCHA: `min()` inside a geq expression FAILS (even with escaped commas);
  use nested `if()` — the expression above is the verified-working form. Also
  `geq` needs a luminance/RGB expr too (`lum='p(X,Y)'`) or it errors
  "A luminance or RGB expression is mandatory". See `assemble_final_v7.py`.
- **End screen (CTA).** The user wants a professional like/subscribe end card
  (5–10 s). Generate a 1920×1080 frame with PIL (wood/plain bg, centered text
  « Si vous avez aimé cette vidéo, n'oubliez pas de liker et de vous abonner pour
  soutenir Searching Murphy. », a rounded teal `S'abonner` button, Hermes icon in a
  corner — see `generate_cta.py`), then `ffmpeg -loop 1 -i cta.png -t 8 -vf
  fade=t=in:st=0:d=0.5,fade=t=out:st=7:d=0.8` → add a silent audio track
  (`-f lavfi -i anullsrc=r=48000:cl=stereo`) → concat to the main video with a
  crossfade: `xfade=transition=fade:duration=1:offset=<main_dur-1>` +
  `acrossfade=d=1` (compute main_dur via ffprobe; see `assemble_final_v7.py`).
- **`--enhancer gfpgan` output is 1024×1024 (GFPGAN upscales 2× from 512), NOT
  512×512** — the `_enhanced.mp4` is already 1024², so the assembly upscales it
  only ~1.05× to 1080×1080 (no softness). Confirm with ffprobe before assuming
  512.
- **NO subtitles / text overlays.** The user said "ne met pas de sous-titre,
  youtu.be le fera dans toutes les langues" — YouTube auto-captions in all
  languages, so skip the lower-third text overlays entirely for YouTube delivery.
- Keep the **title intro + logo watermark** (branding stays), drop only the text.

## Rendering speed + delivery

- **4K encode = NVENC, not x264.** libx264 4K `preset medium` runs ~0.5–1 fps
  (hours for a 4-min clip). Use the GPU:
  `-c:v h264_nvenc -preset p5 -cq 20 -b:v 0`. A mostly-static talking head
  compresses to ~2.5 Mbps — fine for YouTube, which re-encodes anyway.
- **Telegram caps bot uploads at 50 MB**; a 4K final easily exceeds it. Deliver the
  4K file locally (for YouTube) and send a 1080p preview via Telegram:
  `ffmpeg -i final_4k.mp4 -vf scale=1920:1080:flags=lanczos -c:v h264_nvenc -preset p5 -cq 23 -b:v 0 -c:a copy preview_1080p.mp4`
- **Files > 50 MB → SwissTransfer** (swisstransfer.com, up to 50 GB, free, no
  account). This user's preferred transfer for large videos: upload then send the
  download link to their email. Upload is via the web UI (no public curl API) —
  browser automation needs Chrome remote-debugging allowed (tick "Allow remote
  debugging for this browser instance" + a 2nd per-connection "Allow").
- **If the user is remote (Telegram on phone) and can't allow Chrome debugging,
  use the gofile.io API instead** — no browser, works from plain curl/Python:
  1. `GET https://api.gofile.io/servers` → pick an `eu`-zone server name
  2. `POST https://{server}.gofile.io/uploadFile` (multipart `file=@...`) →
     `data.downloadPage` is the share link
  `transfer.sh` (`curl --upload-file`) is simpler but was DOWN this session — gofile
  is the reliable fallback. gofile links expire after a few days (free tier). Post
  the link in chat and/or email it via `smtplib` (see `email-campaign`).
  Reusable stdlib uploader (no `requests` needed): `scripts/gofile_upload.py`.
  The response returns both `downloadPage` (the `/d/` share link) and `code`
  (the file code used to build direct download URLs) — use `downloadPage`.
  **Verify before handing over the link**: the upload response's `data.size`
  (and `data.md5`) must equal the local file (`md5sum <file>`). A user reporting
  a SHORT/truncated file (e.g. a 5-min video arriving as 1min02) is a BROWSER
  download truncation, NOT a bad upload — re-upload fresh and tell them to use a
  resume-capable download manager (JDownloader/IDM).
- **Don't overwrite finished mp4s — keep every version.** The user explicitly
  asked: copy ALL deliverable mp4s into a folder on their Desktop named for the
  project (e.g. `hermes tuto\`) together with the YouTube metadata as `.txt`
  files — `titre.txt`, `description.txt`, `mots_cles.txt` (title / full
  description with dependency links / comma-separated tags). Finished YouTube
  deliverables MAY go on the Desktop when the user asks — this overrides the
  general "no files on Desktop" preference.
- **VibeVoice speaks FAST (~174 wpm).** A 741-word script → 4 min 16 s, not ~6 min.
  For an 8–10 min video you need ~1400 words, not ~750. Write long, trim after.

## Pitfalls

1. `uv venv` defaults to Python 3.14 — torch has no cp314 wheels. Always
   `--python <3.11 path>`.
2. `uv venv`'s `Scripts/python.exe` is a LAUNCHER STUB (~274 KB) that spawns the base
   interpreter (~103 KB) as a child: ONE script = TWO python.exe OS processes
   (stub + real python, same CreationDate, parent→child). Don't miscount these as
   duplicate instances and kill a healthy process.
3. `librosa.filters.mel` positional-args TypeError → apply the patch above.
4. If `--face` is a landscape photo with a small/distant face, the 96×96 mouth
   upscale looks poor. Prefer a close-up frontal portrait (≥512 px face region).
5. **numpy 2.x breaks SadTalker** (`np.VisibleDeprecationWarning` removed in 1.25).
   Pin `numpy==1.23.5`; also downgrade kornia (`==0.7.3`) and scikit-image
   (`==0.22.0`) — their latest releases require numpy≥2.
6. **Installing basicsr/facexlib/gfpgan silently upgrades torch to a CPU build**
   from PyPI. After installing them, REINSTALL `torch==2.5.1+cu121` +
   `torchvision==0.20.1+cu121` from the PyTorch CUDA index (cached → fast), then
   verify `torch.cuda.is_available()`.
7. **basicsr 1.4.2 imports `torchvision.transforms.functional_tensor`** (removed in
   torchvision ≥0.15) → patch `site-packages/basicsr/data/degradations.py`:
   `functional_tensor` → `functional`. It's the only such occurrence.
8. **SadTalker writes all frames only at the END.** `src/facerender/animate.py`
   builds the frame list in memory then `imageio.mimsave(...)` once — during
   generation the result dir holds only the stage-1 `.mat`/`.txt` motion
   coefficients and `first_frame_dir/`, with NO `.jpg`/`.mp4` accumulating. GPU
   pinned at 100 % util + no new files = it is WORKING, not stuck — do NOT kill it.
   (Confirm with `nvidia-smi` util% plus a rising CPU-time counter. Clean
   progress signal: NO `ffmpeg` process = still inside `make_animation`
   (generating); `ffmpeg` appearing = final `mimsave` encode, ~10 min left.
   512/no-`--still` on 8 GB can run ~14 h — if wall-clock has clearly overshot,
   kill it and restart at `--size 256 --batch_size 4` rather than waiting forever.)
9. **`-loop 1` + `overlay` without `-shortest` = INFINITE encode.** When you
   composite the talking head over a LOOPING background image
   (`-loop 1 -i bg.png ... [bg][fg]overlay=...`), the looped input never ends, so
   ffmpeg encodes FOREVER — observed 17 h of output (filter at 11.9× speed) and a
   `.mp4` ballooning to 676 MB before being killed. ALWAYS append `-shortest` so
   it stops at the audio/video length. Symptom to catch it early: a step that
   should finish in ~30 s runs tens of minutes and the output keeps growing past
   the expected size.
10. **Launch SadTalker / EchoMimicV2 from a Python wrapper, not bash inline.**
    Passing `/c/Users/...` MSYS paths as CLI args to the venv's `python.exe`
    mangles them (`C:\c\Users\...`, `$_` shell expansion in PowerShell snippets),
    so `inference.py` raises `ValueError: input_path must be a valid path` or
    `RecursionError` in imageio. Write a small `.py` that builds the args with
    native `C:/...` forward-slash paths and `subprocess.run`s the venv python by
    full path. Same for `docker cp` — MSYS rewrites `/c/...` into `C:\c\...`;
    copy via the mounted `/workspace` volume on the host side instead.
11. **VibeVoice output filenames derive from the TXT basename, not the voice.**
    `--txt_path /workspace/script_teaser_v4.txt` → `outputs_teaser_v4/script_teaser_v4_generated.wav`.
    The generated WAV lands on the HOST at `data/vibevoice/outputs_<dir>/` (the
    `data/vibevoice` dir is mounted at `/workspace`), so no `docker cp` is needed —
    read it straight from the host path.

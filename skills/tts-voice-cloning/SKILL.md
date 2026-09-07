---
name: tts-voice-cloning
description: Use when cloning a voice or generating speech locally — XTTS-v2 (Coqui) for natural French, VibeVoice for long-form/multi-speaker.
---

# Local TTS + Voice Cloning (XTTS-v2 + VibeVoice)

## When to use
User wants to clone a voice or generate speech locally. Two engines are installed:
- **XTTS-v2 (Coqui)** — PREFERRED for natural FRENCH (VibeVoice's French output has a foreign accent + diction bugs).
- **VibeVoice** (community fork `vibevoice-community/VibeVoice`) — long-form / multi-speaker dialogue.

## XTTS-v2 (Coqui) — preferred for French voice cloning

Dedicated venv at `data/xtts/` (torch 2.5.1+cu124 + `coqui-tts`). Two mandatory import patches + a ToS bypass — full detail in `references/xtts-v2-setup.md`.

Clone + generate (24 kHz mono WAV out):
```python
from TTS.api import TTS
from TTS.utils.manage import ModelManager
ModelManager.ask_tos = staticmethod(lambda path: True)  # bypass Coqui license prompt

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
tts.tts_to_file(text=texte, speaker_wav="voix_reference.wav", language="fr",
                temperature=0.75, speed=1.0, file_path="out.wav")
```

- **Delivery (this user's preference)**: `temperature=0.75, speed=1.0` = regular,
  steady, no word dragging. Lower temp → robotic; higher → words drag / glitch
  (an "incomprehensible passage").
- **Generate segment-by-segment** (one file per paragraph, then concat with a
  ~0.35 s gap) so a single mangled segment can be re-generated alone instead of
  redoing the whole ~5 min voice.
- Reference audio: 24 kHz mono, 10–30 s (`mavoix5.wav` = validated take, in
  `data/vibevoice/repo/demo/voices/`).
- **French proper nouns get swallowed — write them PHONETICALLY.** XTTS-v2 read
  « Hermes » as « Herms/Hermz » (the final -es dropped). To force a clear
  pronunciation, spell the word phonetically in the source text (« Hermès » or
  « Hermesse » → « Air-mez »). Do NOT guess which spelling sounds right: generate
  a few short variants (Hermes / Hermès / Hermesse / Airmez) at temperature 0.6
  (more consistent), send them as Telegram voice notes, and let the user pick
  (this user chose « Hermesse »). A word-level phonetic rewrite changes the
  segment duration slightly — a full re-render of the lip-sync (SadTalker) is
  required afterward.
- Model `tts_models/multilingual/multi-dataset/xtts_v2` (~1.9 GB); RTF ≈ 1.2–1.3×
  on RTX 3070 Ti.

## Environment (this user's machine)
- Windows 11 + Docker Desktop (WSL2 backend), GPU RTX 3070 Ti (8 GB), 64 GB RAM.
- Engine runs in Docker container `vibevoice-dev` (image `nvcr.io/nvidia/pytorch:24.07-py3`).
- Host project dir `C:\Users\<user>\AppData\Local\hermes\data\vibevoice\` is mounted at `/workspace`; code at `/workspace/repo`.
- Launcher script `vibevoice.sh` lives in that dir: `demo | clone | stream | infer | status | stop`.

## Install workflow (done once; for rebuild/other models)
1. Start Docker Desktop, wait for `docker info` to succeed.
2. Verify GPU passthrough CHEAPLY before pulling the ~15 GB image:
   `docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi`
3. Pull `nvcr.io/nvidia/pytorch:24.07-py3`, then create a PERSISTENT named container (a throwaway `-it --rm` loses the install between steps):
   ```
   MSYS_NO_PATHCONV=1 docker run -d --name vibevoice-dev --gpus all --privileged --ipc=host \
     --ulimit memlock=-1:-1 --ulimit stack=-1:-1 \
     -v C:/Users/<user>/AppData/Local/hermes/data/vibevoice:/workspace \
     -e HF_HOME=/workspace/hf_cache -p 7860:7860 \
     nvcr.io/nvidia/pytorch:24.07-py3 sleep infinity
   ```
4. Inside the container: `apt-get update && apt-get install -y ffmpeg`.
5. Clone the fork on the HOST (persistent, inspectable) into the mounted dir, then `cd /workspace/repo && pip install -e .`.

## Pitfalls (learned the hard way — apply to any NGC/Windows GPU work)
- **NGC pip mirror is dead.** NGC images set `extra-index-url = https://pypi.ngc.nvidia.com` in pip.conf; that host no longer resolves, so pip burns retries on EVERY package before falling back to pypi.org (slow but not fatal). Fix: `PIP_EXTRA_INDEX_URL= pip install -e .` (or `--index-url https://pypi.org/simple`).
- **MSYS path conversion (git-bash):** prefix `docker run`/`docker exec` with `MSYS_NO_PATHCONV=1` whenever a container path starts with `/` (e.g. `/workspace/...`), or it is rewritten to a Git path and the container errors.
- **Windows vs Linux Docker instructions:** drop `sudo`; `--net=host` is unsupported (use default bridge + `-p`); `-it --rm` does not persist across a multi-step install.
- **flash-attn is optional.** The demo requests `flash_attention_2` on CUDA but auto-falls back to `sdpa` (works fine). Skip the long source build unless long-context OOM appears.
- **VRAM budget:** 1.5B (2.7B params) and Realtime-0.5B (1.0B) fit in 8 GB; 7B/"Large" (9.3B) does NOT.

## Voice cloning (zero-shot) — the mechanism
`demo/inference_from_file.py` maps a speaker NAME to a `.wav` in `demo/voices/` (VoiceMapper strips language prefix + gender suffix: `en-Alice_woman.wav` → `Alice`). That `.wav` is the reference prompt (speech prefill). To clone a custom voice, drop its `.wav` into `demo/voices/` (or copy it there) and reference it by name. Reference voices ship in `demo/voices/*.wav` (16-24 kHz mono, ~10-30 s).

Text is passed via a FILE (`--txt_path`), format `"Speaker N: ..."`, NOT inline text.

Launcher one-liner (normalizes ref to 24 kHz mono, writes the text, runs inference):
```
bash vibevoice.sh clone --ref voices_personnages/Jean.wav --name Jean --text "Bonjour, je suis Jean." --out outputs_clone
```

## Multi-speaker dialogue
One `.wav` per character in `demo/voices/`; script with `Speaker 1:` / `Speaker 2:` lines; then:
```
docker exec -it vibevoice-dev bash -c "cd /workspace/repo && python demo/inference_from_file.py \
  --model_path vibevoice/VibeVoice-1.5B --txt_path /workspace/dialogue.txt \
  --speaker_names Jean Sophie --output_dir /workspace/outputs_dialogue"
```
`--speaker_names` order maps to Speaker 1, 2, ... (up to 4).

## Fine-tuning (LoRA)
Single-speaker only, marked "very experimental". LoRA on the Qwen2 LM (target modules `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`); data = `"Speaker X: text"` + audio (JSONL `{text, audio}` or an HF dataset). The example config targets a 24 GB card (batch 8); on 8 GB use `--per_device_train_batch_size 1 --gradient_checkpointing True`.

## Details
See `references/vibevoice.md` for exact model IDs/sizes, demo-script names vs common (wrong) instructions, and dataset/format specifics.

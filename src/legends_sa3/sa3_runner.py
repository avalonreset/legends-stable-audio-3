from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from .doctor import assert_model_dir
from .prompts import NEGATIVE_PROMPT_INSTRUMENTAL, build_prompt


def add_stable_audio_repo(repo: Path | None) -> None:
    if repo is not None:
        sys.path.insert(0, str(repo))


def load_model(model_dir: Path, stable_audio_repo: Path | None = None):
    add_stable_audio_repo(stable_audio_repo)
    assert_model_dir(model_dir)

    try:
        import torch
        import torchaudio
        from stable_audio_3 import StableAudioModel
        from stable_audio_3.loading_utils import load_diffusion_cond
    except Exception as exc:
        raise RuntimeError(
            "Stable Audio 3 runtime is not importable. Install the official repo and pass "
            "--stable-audio-repo, or run from an environment where stable_audio_3 is installed."
        ) from exc

    with (model_dir / "model_config.json").open("r", encoding="utf-8") as f:
        model_config = json.load(f)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_half = device == "cuda"
    model = load_diffusion_cond(
        model_config,
        str(model_dir / "model.safetensors"),
        device=device,
        model_half=model_half,
    )
    model.use_lora = False
    model.lora_names = []
    return StableAudioModel(model, model_config, device, model_half), torch, torchaudio


def convert_audio_to_mp3(input_path: Path, output_path: Path, bitrate: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(input_path),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            bitrate,
            str(output_path),
        ],
        check=True,
    )


def generate_track_batch(
    *,
    model_dir: Path,
    stable_audio_repo: Path | None,
    lora_ckpt_paths: list[Path] | None,
    lora_strength: float | None,
    output_dir: Path,
    recipe: str | None,
    style: str | None,
    track_count: int,
    track_seconds: int,
    steps: int,
    cfg_scale: float,
    seed_base: int,
    mp3_bitrate: str,
    bpm: int | None = None,
    omit_bpm: bool = False,
    negative_prompt: str | None = NEGATIVE_PROMPT_INSTRUMENTAL,
    instrumental: bool = True,
    custom_style: str | None = None,
) -> list[Path]:
    lora_ckpt_paths = lora_ckpt_paths or []
    if lora_strength is not None and not lora_ckpt_paths:
        raise ValueError("--lora-strength requires at least one --lora-ckpt-path")
    missing_loras = [str(path) for path in lora_ckpt_paths if not path.exists()]
    if missing_loras:
        raise FileNotFoundError(f"LoRA checkpoint not found: {', '.join(missing_loras)}")

    model, torch, torchaudio = load_model(model_dir, stable_audio_repo)
    sample_rate = model.model.sample_rate
    sample_size = model.model_config["sample_size"]
    if lora_ckpt_paths:
        print(f"Loading {len(lora_ckpt_paths)} Stable Audio 3 LoRA adapter(s)", flush=True)
        model.load_lora([str(path) for path in lora_ckpt_paths])
        if lora_strength is not None:
            model.set_lora_strength(lora_strength)

    track_dir = output_dir / "tracks_mp3"
    temp_dir = output_dir / "tmp_wav"
    track_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    negative_prompt_applied = negative_prompt is not None and cfg_scale != 1.0
    effective_negative_prompt = negative_prompt if negative_prompt_applied else None
    if negative_prompt and not negative_prompt_applied:
        print(
            "Note: negative prompt is inactive at cfg_scale=1.0; "
            "instrumental control comes from the positive VocalType tag.",
            flush=True,
        )

    manifest = {
        "model": "stabilityai/stable-audio-3-medium",
        "recipe": recipe,
        "style": style,
        "track_seconds": track_seconds,
        "track_count": track_count,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "negative_prompt": negative_prompt,
        "negative_prompt_applied": negative_prompt_applied,
        "effective_negative_prompt": effective_negative_prompt,
        "instrumental": instrumental,
        "sample_rate": sample_rate,
        "sample_size": sample_size,
        "lora_ckpt_paths": [str(path) for path in lora_ckpt_paths],
        "lora_strength": lora_strength,
        "tracks": [],
    }

    track_paths: list[Path] = []
    for index in range(1, track_count + 1):
        slug = f"{index:03d}"
        mp3_path = track_dir / f"{slug}.mp3"
        wav_path = temp_dir / f"{slug}.wav"
        track_paths.append(mp3_path)
        if mp3_path.exists() and mp3_path.stat().st_size > 1_000_000:
            print(f"[{index:03d}/{track_count:03d}] Skipping existing {mp3_path.name}", flush=True)
            continue

        prompt, track_bpm = build_prompt(
            recipe,
            index,
            style=style,
            custom_style=custom_style,
            bpm=bpm,
            instrumental=instrumental,
            omit_bpm=omit_bpm,
        )
        seed = seed_base + index
        print(f"[{index:03d}/{track_count:03d}] Generating seed={seed} bpm={track_bpm}", flush=True)
        started = time.time()
        audio = model.generate(
            prompt=prompt,
            negative_prompt=effective_negative_prompt,
            duration=track_seconds,
            sample_size=sample_size,
            steps=steps,
            cfg_scale=cfg_scale,
            seed=seed,
            chunked_decode=True,
        )
        audio = audio.to(torch.float32).clamp(-1, 1).cpu()
        torchaudio.save(str(wav_path), audio[0], sample_rate)
        del audio
        convert_audio_to_mp3(wav_path, mp3_path, mp3_bitrate)
        wav_path.unlink(missing_ok=True)
        manifest["tracks"].append(
            {
                "index": index,
                "seed": seed,
                "bpm": track_bpm,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "negative_prompt_applied": negative_prompt_applied,
                "effective_negative_prompt": effective_negative_prompt,
                "mp3_path": str(mp3_path),
                "elapsed_seconds": round(time.time() - started, 2),
            }
        )
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"[{index:03d}/{track_count:03d}] Saved {mp3_path.name}", flush=True)

    return track_paths

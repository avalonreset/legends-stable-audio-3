from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from .doctor import assert_model_dir
from .prompts import NEGATIVE_PROMPT_INSTRUMENTAL, build_prompt

BITRATE_RE = re.compile(r"^[1-9]\d{1,3}[kK]?$")
MAX_CONFIG_BYTES = 1_048_576


def add_stable_audio_repo(repo: Path | None) -> None:
    if repo is not None:
        if repo.is_symlink():
            raise ValueError(f"Refusing symlinked stable_audio_repo path: {repo}")
        sys.path.insert(0, str(repo.resolve()))


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

    config_path = model_dir / "model_config.json"
    weights_path = model_dir / "model.safetensors"
    if config_path.is_symlink() or weights_path.is_symlink():
        raise ValueError("Refusing symlinked model configuration or safetensors weights")
    if config_path.stat().st_size > MAX_CONFIG_BYTES:
        raise ValueError("model_config.json exceeds 1 MiB safety limit")
    with config_path.open("r", encoding="utf-8") as f:
        model_config = json.load(f)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_half = device == "cuda"
    model = load_diffusion_cond(
        model_config,
        str(weights_path.resolve()),
        device=device,
        model_half=model_half,
    )
    model.use_lora = False
    model.lora_names = []
    return StableAudioModel(model, model_config, device, model_half), torch, torchaudio


def convert_audio_to_mp3(
    input_path: Path,
    output_path: Path,
    bitrate: str,
    *,
    timeout: float = 300.0,
) -> None:
    if not BITRATE_RE.fullmatch(bitrate):
        raise ValueError(f"Invalid MP3 bitrate: {bitrate!r}")
    if input_path.is_symlink() or output_path.is_symlink():
        raise ValueError("Refusing symlinked audio input or MP3 output path")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(input_path.resolve()),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            bitrate,
            "--",
            str(output_path.resolve()),
        ],
        check=True,
        timeout=timeout,
    )


def validate_lora_ckpt_paths(lora_ckpt_paths: list[Path]) -> list[Path]:
    validated: list[Path] = []
    missing_loras: list[str] = []
    for path in lora_ckpt_paths:
        if path.is_symlink():
            raise ValueError(f"Refusing symlinked LoRA checkpoint: {path}")
        if path.suffix.lower() != ".safetensors":
            raise ValueError(
                f"LoRA checkpoint must be a .safetensors file (pickle checkpoints are forbidden): {path}"
            )
        if not path.is_file():
            missing_loras.append(str(path))
        else:
            validated.append(path.resolve())
    if missing_loras:
        raise FileNotFoundError(f"LoRA checkpoint not found: {', '.join(missing_loras)}")
    return validated


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
    overwrite: bool = False,
) -> list[Path]:
    if not BITRATE_RE.fullmatch(mp3_bitrate):
        raise ValueError(f"Invalid MP3 bitrate: {mp3_bitrate!r}")
    if output_dir.is_symlink():
        raise ValueError(f"Refusing symlinked output directory: {output_dir}")
    manifest_file = output_dir / "manifest.json"
    if manifest_file.is_symlink():
        raise ValueError(f"Refusing symlinked manifest path: {manifest_file}")
    if manifest_file.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing generation manifest without --overwrite: {manifest_file}"
        )

    lora_ckpt_paths = lora_ckpt_paths or []
    if lora_strength is not None and not lora_ckpt_paths:
        raise ValueError("--lora-strength requires at least one --lora-ckpt-path")
    validated_loras = validate_lora_ckpt_paths(lora_ckpt_paths)

    model, torch, torchaudio = load_model(model_dir, stable_audio_repo)
    sample_rate = model.model.sample_rate
    sample_size = model.model_config["sample_size"]
    if validated_loras:
        print(f"Loading {len(validated_loras)} Stable Audio 3 LoRA adapter(s)", flush=True)
        model.load_lora([str(path) for path in validated_loras])
        if lora_strength is not None:
            model.set_lora_strength(lora_strength)

    track_dir = output_dir / "tracks_mp3"
    temp_dir = output_dir / "tmp_wav"
    if track_dir.is_symlink() or temp_dir.is_symlink():
        raise ValueError(f"Refusing symlinked track or temporary directory inside {output_dir}")
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
        if mp3_path.is_symlink() or wav_path.is_symlink():
            raise ValueError(f"Refusing symlinked track or temporary audio file: {mp3_path}")
        track_paths.append(mp3_path)
        if mp3_path.exists():
            if not overwrite:
                if mp3_path.stat().st_size > 1_000_000:
                    print(f"[{index:03d}/{track_count:03d}] Skipping existing {mp3_path.name}", flush=True)
                    continue
                raise RuntimeError(
                    f"Refusing to overwrite existing track without --overwrite: {mp3_path}"
                )

        prompt, track_bpm = build_prompt(
            recipe,
            index,
            style=style,
            custom_style=custom_style,
            bpm=bpm,
            instrumental=instrumental,
            omit_bpm=omit_bpm,
        )
        seed = seed_base + index - 1
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

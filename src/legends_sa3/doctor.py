from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DoctorReport:
    platform: str
    architecture: str
    python: str
    ffmpeg: bool
    ffprobe: bool
    torch: bool
    cuda: bool
    mps: bool
    gpu_name: str | None
    vram_gb: float | None
    local_medium_backend: str


def detect_torch() -> tuple[bool, bool, bool, str | None, float | None]:
    try:
        import torch
    except Exception:
        return False, False, False, None, None

    mps_available = bool(
        hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    )
    if not torch.cuda.is_available():
        return True, False, mps_available, None, None

    device_index = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device_index)
    return True, True, mps_available, props.name, round(props.total_memory / (1024**3), 2)


def run_doctor() -> DoctorReport:
    torch_ok, cuda_ok, mps_ok, gpu_name, vram_gb = detect_torch()
    return DoctorReport(
        platform=platform.system().lower(),
        architecture=platform.machine().lower(),
        python=platform.python_version(),
        ffmpeg=shutil.which("ffmpeg") is not None,
        ffprobe=shutil.which("ffprobe") is not None,
        torch=torch_ok,
        cuda=cuda_ok,
        mps=mps_ok,
        gpu_name=gpu_name,
        vram_gb=vram_gb,
        local_medium_backend="cuda" if cuda_ok else "cpu",
    )


def assert_model_dir(model_dir: Path) -> None:
    required = [
        model_dir / "model_config.json",
        model_dir / "model.safetensors",
        model_dir / "t5gemma-b-b-ul2" / "config.json",
        model_dir / "t5gemma-b-b-ul2" / "model.safetensors",
        model_dir / "t5gemma-b-b-ul2" / "tokenizer.json",
    ]
    missing = [str(path.relative_to(model_dir)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Incomplete Stable Audio 3 Medium bundle in {model_dir}; missing: {', '.join(missing)}. "
            "Run `legends-sa3 download-model --model medium --output <that-directory>` "
            "after accepting the gated Stability and Gemma terms."
        )


def ffprobe_duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-hide_banner",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return float(proc.stdout.strip())

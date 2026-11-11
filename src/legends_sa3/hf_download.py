from __future__ import annotations

import json
import re
from pathlib import Path

MODEL_REPOS = {
    "medium": "stabilityai/stable-audio-3-medium",
}
DEFAULT_MODEL_REVISIONS = {
    "medium": "d4d3579395a8ac0df4ab13b5b1d7138ce7290f81",
}
FORBIDDEN_WEIGHT_PATTERNS = [
    "*.bin",
    "*.ckpt",
    "*.pkl",
    "*.pt",
    "*.pth",
]
REVISION_RE = re.compile(r"^[A-Za-z0-9._/-]{1,128}$")
MAX_CONFIG_BYTES = 1_048_576


def download_model(model: str, output: Path, *, revision: str | None = None) -> Path:
    """Download gated model files after the user has accepted terms."""
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        raise RuntimeError(
            "Install the download support first: `python -m pip install '.[download]'` "
            "from a source checkout, or `python -m pip install "
            "legends-stable-audio-3[download]` from a package index."
        ) from exc

    if model not in MODEL_REPOS:
        raise ValueError(f"Unknown model {model}. Available: {', '.join(sorted(MODEL_REPOS))}")

    resolved_revision = (revision or DEFAULT_MODEL_REVISIONS[model]).strip()
    if not REVISION_RE.fullmatch(resolved_revision) or ".." in resolved_revision:
        raise ValueError(f"Invalid Hugging Face revision: {resolved_revision!r}")

    if output.is_symlink():
        raise ValueError(f"Refusing symlinked model output directory: {output}")

    output.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_REPOS[model],
        revision=resolved_revision,
        local_dir=str(output),
        token=True,
        allow_patterns=[
            "model_config.json",
            "model.safetensors",
            "t5gemma-b-b-ul2/*",
            "LICENSE.md",
            "LICENSE_GEMMA.md",
            "NOTICE",
            "README.md",
        ],
        ignore_patterns=list(FORBIDDEN_WEIGHT_PATTERNS),
    )
    config_path = output / "model_config.json"
    conditioner_dir = output / "t5gemma-b-b-ul2"
    if config_path.is_symlink() or conditioner_dir.is_symlink():
        raise ValueError(f"Refusing symlinked model_config.json or conditioner directory in {output}")
    for downloaded in output.rglob("*"):
        if downloaded.is_symlink():
            raise ValueError(f"Refusing symlinked downloaded file: {downloaded}")
    if config_path.stat().st_size > MAX_CONFIG_BYTES:
        raise ValueError("model_config.json exceeds 1 MiB safety limit")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    conditioners = config.get("model", {}).get("conditioning", {}).get("configs", [])
    for conditioner in conditioners:
        if conditioner.get("type") == "t5gemma":
            conditioner.setdefault("config", {})["model_path"] = str(
                conditioner_dir.resolve()
            )
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return output

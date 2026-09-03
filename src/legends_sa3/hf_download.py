from __future__ import annotations

from pathlib import Path


MODEL_REPOS = {
    "medium": "stabilityai/stable-audio-3-medium",
}


def download_model(model: str, output: Path) -> Path:
    """Download gated model files after the user has accepted terms."""
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        raise RuntimeError("Install with `pip install -e .[download]` first") from exc

    if model not in MODEL_REPOS:
        raise ValueError(f"Unknown model {model}. Available: {', '.join(sorted(MODEL_REPOS))}")

    output.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_REPOS[model],
        local_dir=str(output),
        local_dir_use_symlinks=False,
        token=True,
        allow_patterns=["model_config.json", "model.safetensors"],
    )
    return output


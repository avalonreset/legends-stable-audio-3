from __future__ import annotations

import json
from pathlib import Path

MODEL_REPOS = {
    "medium": "stabilityai/stable-audio-3-medium",
}


def download_model(model: str, output: Path) -> Path:
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

    output.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_REPOS[model],
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
    )
    config_path = output / "model_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    conditioners = config.get("model", {}).get("conditioning", {}).get("configs", [])
    for conditioner in conditioners:
        if conditioner.get("type") == "t5gemma":
            conditioner.setdefault("config", {})["model_path"] = str(
                (output / "t5gemma-b-b-ul2").resolve()
            )
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return output

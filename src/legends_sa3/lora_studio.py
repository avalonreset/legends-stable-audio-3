from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


UNDERFIT_REPO_URL = "https://github.com/dada-bots/underfit"
UNDERFIT_COMMIT = "8a96800a58c0e8b82327fc04ac31c473ed900b73"
UNDERFIT_LICENSE = "MIT"
UNDERFIT_LICENSE_SHA256 = "073a815ba79b8f629ef29f6a0699c14233fe18ae40daea8245941bb410bc8a09"
DEFAULT_STUDIO_DIR = Path(".legends") / "lora-studio" / "underfit"
DEFAULT_ADAPTERS_DIR = Path(".legends") / "adapters"


@dataclass(frozen=True)
class AdapterImport:
    adapter_path: Path
    manifest_path: Path
    sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify_adapter_name(value: str) -> str:
    cleaned = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    slug = "".join(cleaned).strip("-")
    return slug or "adapter"


def default_adapter_name(source: Path) -> str:
    name = source.stem
    if name.isdigit() and source.parent.name:
        name = f"{source.parent.name}-{name}"
    return slugify_adapter_name(name)


def ensure_git_available() -> None:
    if shutil.which("git") is None:
        raise RuntimeError("git is required to install Underfit. Install git and rerun lora-studio install.")


def ensure_bash_available() -> str:
    bash = shutil.which("bash")
    if bash is None:
        raise RuntimeError(
            "Underfit ships Linux shell scripts. Install Git Bash, use WSL/Linux, or use the Pinokio wrapper, "
            "then rerun the command."
        )
    return bash


def normalize_git_url(value: str) -> str:
    normalized = value.strip().replace("\\", "/").rstrip("/")
    if normalized.lower().endswith(".git"):
        normalized = normalized[:-4]
    return normalized.lower()


def git_text(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def clone_or_update_underfit(
    *,
    root: Path,
    update: bool = False,
) -> Path:
    ensure_git_available()
    root = root.expanduser()
    root.parent.mkdir(parents=True, exist_ok=True)
    if (root / ".git").exists():
        verify_underfit_checkout(root)
        if update:
            if git_text(root, "status", "--porcelain"):
                raise RuntimeError("Refusing to update an Underfit checkout with local changes.")
            subprocess.run(
                ["git", "-C", str(root), "fetch", "--depth", "1", "origin", UNDERFIT_COMMIT],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "checkout", "--detach", "FETCH_HEAD"],
                check=True,
            )
    elif root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Underfit root exists and is not an empty git checkout: {root}")
    else:
        root.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(root), "init"], check=True)
        subprocess.run(["git", "-C", str(root), "remote", "add", "origin", UNDERFIT_REPO_URL], check=True)
        subprocess.run(
            ["git", "-C", str(root), "fetch", "--depth", "1", "origin", UNDERFIT_COMMIT],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "checkout", "--detach", "FETCH_HEAD"],
            check=True,
        )
    verify_underfit_checkout(root)
    return root


def verify_underfit_checkout(root: Path) -> None:
    root = root.expanduser()
    if not (root / ".git").exists():
        raise RuntimeError(f"Underfit root is not a git checkout: {root}")
    origin = git_text(root, "remote", "get-url", "origin")
    if normalize_git_url(origin) != normalize_git_url(UNDERFIT_REPO_URL):
        raise RuntimeError(f"Unexpected Underfit origin: {origin}")
    commit = git_text(root, "rev-parse", "HEAD").lower()
    if commit != UNDERFIT_COMMIT:
        raise RuntimeError(f"Unexpected Underfit commit: {commit}; expected {UNDERFIT_COMMIT}")
    required = ["README.md", "LICENSE", "install.sh", "run.sh", "dashboard/server.py"]
    missing = [item for item in required if not (root / item).exists()]
    if missing:
        raise FileNotFoundError(f"Underfit checkout is missing required files: {', '.join(missing)}")
    license_hash = sha256_file(root / "LICENSE")
    if license_hash != UNDERFIT_LICENSE_SHA256:
        raise RuntimeError(
            f"Unexpected Underfit LICENSE hash: {license_hash}; expected {UNDERFIT_LICENSE_SHA256}"
        )


def run_underfit_install(*, root: Path, backend: str | None = "sa3", no_setup: bool = False) -> None:
    verify_underfit_checkout(root)
    bash = ensure_bash_available()
    command = [bash, "install.sh"]
    if no_setup:
        command.append("--no-setup")
    if backend:
        command.extend(["--backend", backend])
    subprocess.run(command, cwd=root, check=True)


def run_underfit_dashboard(
    *,
    root: Path,
    host: str | None = None,
    port: int | None = None,
    state_dir: Path | None = None,
    models_dir: Path | None = None,
) -> None:
    verify_underfit_checkout(root)
    bash = ensure_bash_available()
    env = os.environ.copy()
    if host:
        env["UNDERFIT_DASHBOARD_HOST"] = host
    if port is not None:
        env["UNDERFIT_DASHBOARD_PORT"] = str(port)
    if state_dir is not None:
        env["UNDERFIT_STATE_DIR"] = str(state_dir.expanduser())
    if models_dir is not None:
        env["UNDERFIT_MODELS_DIR"] = str(models_dir.expanduser())
    subprocess.run([bash, "run.sh"], cwd=root, env=env, check=True)


def import_adapter(
    *,
    source: Path,
    adapters_dir: Path = DEFAULT_ADAPTERS_DIR,
    name: str | None = None,
    source_run: str | None = None,
    overwrite: bool = False,
) -> AdapterImport:
    source = source.expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Adapter checkpoint not found: {source}")
    if source.suffix.lower() != ".safetensors":
        raise ValueError("LoRA Studio imports only .safetensors adapter checkpoints.")

    adapters_dir = adapters_dir.expanduser()
    adapters_dir.mkdir(parents=True, exist_ok=True)
    adapter_name = slugify_adapter_name(name) if name else default_adapter_name(source)
    destination = adapters_dir / f"{adapter_name}.safetensors"
    manifest_path = adapters_dir / f"{adapter_name}.json"
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Adapter already exists: {destination}. Use --overwrite or choose --name.")

    shutil.copy2(source, destination)
    digest = sha256_file(destination)
    manifest = {
        "name": adapter_name,
        "adapter_path": str(destination),
        "source_path": str(source),
        "source_run": source_run,
        "format": "native-stable-audio-3-lora",
        "sha256": digest,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "loader_hint": f"legends-sa3 generate --lora-ckpt-path {destination}",
        "notes": [
            "Do not commit adapter checkpoints unless you have explicit rights to redistribute them.",
            "Stable Audio model terms are separate from the Underfit MIT license.",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return AdapterImport(adapter_path=destination, manifest_path=manifest_path, sha256=digest)


def list_imported_adapters(adapters_dir: Path = DEFAULT_ADAPTERS_DIR) -> list[dict[str, object]]:
    adapters_dir = adapters_dir.expanduser()
    if not adapters_dir.exists():
        return []
    rows: list[dict[str, object]] = []
    for manifest_path in sorted(adapters_dir.glob("*.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        adapter_path = Path(str(manifest.get("adapter_path", "")))
        rows.append(
            {
                "name": manifest.get("name", manifest_path.stem),
                "adapter_path": str(adapter_path),
                "exists": adapter_path.exists(),
                "sha256": manifest.get("sha256", ""),
                "manifest_path": str(manifest_path),
            }
        )
    return rows


def underfit_status(*, root: Path = DEFAULT_STUDIO_DIR, adapters_dir: Path = DEFAULT_ADAPTERS_DIR) -> dict[str, object]:
    root = root.expanduser()
    installed = (root / ".git").exists()
    verified = False
    verification_error = "not installed"
    commit = "not installed"
    origin = "not installed"
    if installed:
        try:
            origin = git_text(root, "remote", "get-url", "origin")
            commit = git_text(root, "rev-parse", "HEAD")
            verify_underfit_checkout(root)
            verified = True
            verification_error = ""
        except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
            verification_error = str(exc)
    return {
        "underfit_root": str(root),
        "underfit_repo": UNDERFIT_REPO_URL,
        "underfit_expected_commit": UNDERFIT_COMMIT,
        "underfit_origin": origin,
        "underfit_commit": commit,
        "underfit_installed": installed,
        "underfit_verified": verified,
        "underfit_verification_error": verification_error,
        "underfit_license": UNDERFIT_LICENSE if verified else "unknown",
        "adapters_dir": str(adapters_dir.expanduser()),
        "adapter_count": len(list_imported_adapters(adapters_dir)),
        "python": sys.executable,
    }

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "skill-package.json"
FORBIDDEN_RELEASE_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".flac",
    ".mp3",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
    ".wav",
}
PUBLIC_SURFACE = (
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "GEMINI.md",
    "GROK.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CITATION.cff",
    "assets/PROVENANCE.md",
    "docs/agent-compatibility.md",
    "docs/commercial-use-and-license.md",
    "docs/hosted-surfaces-and-receipts.md",
    "docs/model-access.md",
    "docs/platform-support.md",
    "docs/release-checklist.md",
    "docs/source-license-decision.md",
    "pyproject.toml",
)
FALLBACK_EXCLUDED_PARTS = {
    ".git",
    ".legends",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".release-venv",
    "__pycache__",
    "build",
    "dist",
    "models",
    "output",
    "runs",
    "tmp",
}


def load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def package_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def copy_package(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for relative, content in package_files(source).items():
        target = destination / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def parse_frontmatter(skill_path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    text = skill_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}, [f"{skill_path}: missing opening YAML delimiter"]
    try:
        closing = lines.index("---", 1)
    except ValueError:
        return {}, [f"{skill_path}: missing closing YAML delimiter"]

    values: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"{skill_path}: invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values, errors


def git_release_files(root: Path = ROOT) -> list[Path]:
    if not (root / ".git").exists():
        return sorted(
            path.relative_to(root)
            for path in root.rglob("*")
            if path.is_file()
            and not any(part in FALLBACK_EXCLUDED_PARTS or part.endswith(".egg-info") for part in path.relative_to(root).parts)
        )
    commands = (
        ["git", "ls-files", "-z"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    paths: set[Path] = set()
    for command in commands:
        result = subprocess.run(
            command,
            cwd=root,
            check=True,
            capture_output=True,
        )
        for raw in result.stdout.split(b"\0"):
            if raw:
                paths.add(Path(raw.decode("utf-8")))
    return sorted(paths)


def validate() -> list[str]:
    manifest = load_manifest()
    name = str(manifest["name"])
    canonical = ROOT / str(manifest["canonical"])
    errors: list[str] = []

    values, frontmatter_errors = parse_frontmatter(canonical / "SKILL.md")
    errors.extend(frontmatter_errors)
    if set(values) != {"name", "description"}:
        errors.append("SKILL.md frontmatter must contain only name and description")
    if values.get("name") != name or canonical.name != name:
        errors.append("skill name, canonical folder, and manifest name must match")
    if not values.get("description"):
        errors.append("SKILL.md description must not be empty")

    skill_text = " ".join(
        (canonical / "SKILL.md").read_text(encoding="utf-8").lower().split()
    )
    required_skill_markers = (
        "local stable audio 3 medium",
        "hosted stable audio 3 large",
        "stable audio web studio",
        "legends downstream mixer or daw",
        "8 ping-pong steps",
        "negative prompts are inactive",
        "references/surfaces-and-receipts.md",
        "references/large-api.md",
        "references/prompt-mastery.md",
        "tracktype: sfx",
        "large result --generation-id",
        "pending receipt",
        "licensed under apache license 2.0",
        "independent compatibility project",
        "separately licensed",
    )
    for marker in required_skill_markers:
        if marker not in skill_text:
            errors.append(f"canonical skill is missing required operating marker: {marker}")

    canonical_files = package_files(canonical)
    metadata = canonical_files.get("agents/openai.yaml", b"").decode("utf-8")
    if f"${name}" not in metadata:
        errors.append("agents/openai.yaml default_prompt must name the skill explicitly")

    markdown_link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for relative, content in canonical_files.items():
        if not relative.lower().endswith(".md"):
            continue
        text = content.decode("utf-8")
        for target in markdown_link.findall(text):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            clean_target = target.split("#", 1)[0].replace("\\", "/")
            resolved = (canonical / Path(relative).parent / clean_target).resolve()
            if not resolved.is_file() or canonical.resolve() not in resolved.parents:
                errors.append(f"{relative}: unresolved local Markdown link: {target}")

    private_skill_patterns = {
        "e:\\empire": "private Empire path",
        "[[": "Obsidian wiki-link syntax",
        "c:\\users\\": "private user path",
    }
    for relative, content in canonical_files.items():
        if not relative.lower().endswith((".md", ".yaml", ".yml", ".json")):
            continue
        lowered = content.decode("utf-8").lower()
        for pattern, description in private_skill_patterns.items():
            if pattern in lowered:
                errors.append(f"{relative}: contains {description}")

    for label, relative in dict(manifest["mirrors"]).items():
        mirror = ROOT / str(relative)
        mirror_files = package_files(mirror) if mirror.exists() else {}
        if mirror_files != canonical_files:
            errors.append(f"{label} mirror is not synchronized: {relative}")

    canonical_reference = str(manifest["canonical"]).replace("\\", "/")
    stale_adapter_patterns = {
        "stable audio 3 medium operator": "Medium-only scope",
        "steps: `12`": "12-step default",
        "default of `12`": "12-step default",
        "crossfade: 12 seconds.": "unqualified universal crossfade",
        "start at 380 second segments.": "unqualified 380-second creative default",
        "shape the prompt, recipe, negative prompt, duration, seed, steps, and cfg":
            "CFG 1.0 negative-prompt misinformation",
    }
    for label, relative in dict(manifest["adapters"]).items():
        adapter = ROOT / str(relative)
        if not adapter.is_file():
            errors.append(f"missing {label} adapter: {relative}")
            continue
        if adapter.suffix.lower() == ".md":
            normalized = adapter.read_text(encoding="utf-8").replace("\\", "/")
            if canonical_reference not in normalized:
                errors.append(f"{label} adapter does not reference {canonical_reference}")
            lowered = normalized.lower()
            for pattern, description in stale_adapter_patterns.items():
                if pattern in lowered:
                    errors.append(f"{relative}: contains {description}")

    stale_patterns = {
        "legends-stable-audio-3" + ".0": "point-oh project name",
        "private-source": "private-source positioning",
        "private preview": "private-preview positioning",
        "proprietary legends pro": "superseded proprietary positioning",
        "eventual public open-source release": "superseded tentative open-source positioning",
        "treat this repository as proprietary": "superseded proprietary instruction",
        "source is proprietary": "superseded proprietary instruction",
        "mit or apache-2.0": "superseded license-selection language",
        "license selection pending": "superseded license-selection language",
        "license choice remains": "superseded license-selection language",
        "avalonreset" + "-pro": "private organization slug",
        "github.com/legends-pro/": "retired repository URL",
        "github.com/cto-legends/": "private repository URL",
        "e:\\empire": "private Empire path",
        "c:\\users\\": "private user path",
    }
    for relative in PUBLIC_SURFACE:
        path = ROOT / relative
        if not path.exists():
            continue
        lowered = path.read_text(encoding="utf-8").lower()
        for pattern, description in stale_patterns.items():
            if pattern in lowered:
                errors.append(f"{relative}: contains {description}")

    secret_patterns = (
        re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    )
    for relative in git_release_files(ROOT):
        if relative.suffix.lower() in FORBIDDEN_RELEASE_SUFFIXES:
            errors.append(f"release tree contains forbidden binary artifact: {relative}")
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in secret_patterns):
            errors.append(f"release tree contains a token-shaped secret: {relative}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize and validate the canonical cross-platform agent skill."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Copy the canonical skill package to committed platform mirrors.",
    )
    parser.add_argument(
        "--install-target",
        type=Path,
        help="Copy the canonical skill folder into a user-supplied skills directory.",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    canonical = ROOT / str(manifest["canonical"])
    if args.sync:
        for relative in dict(manifest["mirrors"]).values():
            copy_package(canonical, ROOT / str(relative))
    if args.install_target:
        destination = args.install_target.expanduser().resolve() / str(manifest["name"])
        if destination.exists():
            raise SystemExit(f"Refusing to replace existing skill directory: {destination}")
        copy_package(canonical, destination)

    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("skill package: ok")
    print(f"canonical: {canonical.relative_to(ROOT).as_posix()}")
    print(f"mirrors: {len(dict(manifest['mirrors']))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

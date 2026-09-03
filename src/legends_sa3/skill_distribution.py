from __future__ import annotations

import re
import shutil
from pathlib import Path

SKILL_NAME = "legends-stable-audio-3"


def bundled_skill_path() -> Path:
    path = Path(__file__).resolve().parent / "_bundled_skill" / SKILL_NAME
    if not path.is_dir():
        raise RuntimeError("The installed package is missing its bundled agent skill.")
    return path


def validate_skill(path: Path | None = None) -> list[str]:
    root = (path or bundled_skill_path()).resolve()
    errors: list[str] = []
    skill_path = root / "SKILL.md"
    metadata_path = root / "agents" / "openai.yaml"

    if not skill_path.is_file():
        errors.append(f"missing skill entrypoint: {skill_path}")
    else:
        lines = skill_path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0] != "---":
            errors.append("SKILL.md is missing its opening YAML delimiter")
        else:
            try:
                closing = lines.index("---", 1)
            except ValueError:
                errors.append("SKILL.md is missing its closing YAML delimiter")
            else:
                fields: dict[str, str] = {}
                for line in lines[1:closing]:
                    if line.strip() and ":" in line:
                        key, value = line.split(":", 1)
                        fields[key.strip()] = value.strip()
                if set(fields) != {"name", "description"}:
                    errors.append("SKILL.md frontmatter must contain only name and description")
                if fields.get("name") != SKILL_NAME:
                    errors.append(f"SKILL.md name must be {SKILL_NAME}")
                if not fields.get("description"):
                    errors.append("SKILL.md description must not be empty")

    if not metadata_path.is_file():
        errors.append(f"missing Codex UI metadata: {metadata_path}")
    elif f"${SKILL_NAME}" not in metadata_path.read_text(encoding="utf-8"):
        errors.append("agents/openai.yaml must reference the skill in default_prompt")

    markdown_link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for markdown_path in root.rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")
        lowered = text.lower()
        for pattern, description in (
            ("e:\\empire", "private Empire path"),
            ("[[", "Obsidian wiki-link syntax"),
            ("c:\\users\\", "private user path"),
        ):
            if pattern in lowered:
                errors.append(f"{markdown_path}: contains {description}")
        for target in markdown_link.findall(text):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            clean_target = target.split("#", 1)[0]
            resolved = (markdown_path.parent / clean_target).resolve()
            if not resolved.is_file() or root not in resolved.parents:
                errors.append(f"{markdown_path}: unresolved local Markdown link: {target}")
    return errors


def install_bundled_skill(target: Path) -> Path:
    target_root = target.expanduser().resolve()
    destination = target_root / SKILL_NAME
    if destination.exists():
        raise FileExistsError(
            f"Refusing to replace existing skill directory: {destination}. "
            "Remove or move it explicitly, then retry."
        )
    target_root.mkdir(parents=True, exist_ok=True)
    source = bundled_skill_path()
    errors = validate_skill(source)
    if errors:
        raise RuntimeError("Bundled skill validation failed: " + "; ".join(errors))
    shutil.copytree(source, destination)
    installed_errors = validate_skill(destination)
    if installed_errors:
        shutil.rmtree(destination)
        raise RuntimeError("Installed skill validation failed: " + "; ".join(installed_errors))
    return destination

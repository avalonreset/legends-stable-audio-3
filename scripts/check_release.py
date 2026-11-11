#!/usr/bin/env python3
"""Offline release readiness gate for legends-stable-audio-3."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SUPPORT.md",
    "CITATION.cff",
    "AGENTS.md",
    "MANIFEST.in",
    "docs/AGENT-RECIPE.md",
    ".legends-module",
    ".legends-router-pin",
    "skills/cto-legends/SKILL.md",
    "assets/banner.png",
    "assets/banner.webp",
    "assets/preview.png",
    "assets/social-preview.png",
    "assets/stable-audio-3-youtube.png",
    "assets/manifest.json",
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".release-venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".legends",
    "models",
    "output",
    "runs",
    "tmp",
}

TEXT_EXTS = {".py", ".md", ".toml", ".json", ".yml", ".yaml", ".cff", ".txt", ".in", ".cfg", ".ini"}
FORBIDDEN_FILES = {".pem", ".key", ".p12", ".pfx", ".ps1", ".bat", ".cmd", ".vbs", ".ahk"}

FORBIDDEN_PATTERNS = [
    r"(?i)[a-z]:\\users\\(?!public\b|default\b|someone\b|you\b|<)",
    r"(?i)\.tail[a-z0-9]+\.ts\.net",
    r"(?i)nsec1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{30,}",
    r"gh[pousr]_[A-Za-z0-9]{20,}",
    r"sk_live_[A-Za-z0-9]{16,}",
    r"rk_live_[A-Za-z0-9]{16,}",
    r"whsec_[A-Za-z0-9]{16,}",
    r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
    r"CREATE_NO_WINDOW",
    r"0x08000000",
    r"(?i)-WindowStyle\s+Hidden",
    r"(?i)-ExecutionPolicy\s+Bypass",
    r"ctypes\.windll",
    r"(?i)CryptUnprotectData",
    r"(?i)GetAsyncKeyState",
    r"(?i)IndexedDB",
]

PNG_METADATA_CHUNKS = {"tEXt", "zTXt", "iTXt", "eXIf"}
WEBP_METADATA_CHUNKS = {b"EXIF", b"XMP "}


def image_metadata_issues(path: Path) -> list[str]:
    """Flag raster metadata chunks that can carry authoring residue."""
    try:
        raw = path.read_bytes()
    except OSError:
        return [f"Cannot read image: {path}"]
    issues: list[str] = []
    suffix = path.suffix.lower()
    if suffix == ".png":
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            return [f"{path.name}: invalid PNG header"]
        offset = 8
        while offset + 8 <= len(raw):
            length = struct.unpack(">I", raw[offset : offset + 4])[0]
            chunk_type = raw[offset + 4 : offset + 8].decode("latin1", errors="replace")
            if chunk_type in PNG_METADATA_CHUNKS:
                issues.append(f"{path.name}: forbidden metadata chunk {chunk_type}")
            if chunk_type == "IEND":
                break
            offset += 12 + length
    elif suffix == ".webp":
        if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
            return [f"{path.name}: invalid WebP header"]
        offset = 12
        while offset + 8 <= len(raw):
            tag = raw[offset : offset + 4]
            length = struct.unpack("<I", raw[offset + 4 : offset + 8])[0]
            if tag in WEBP_METADATA_CHUNKS:
                label = tag.decode("ascii", errors="replace").strip()
                issues.append(f"{path.name}: forbidden metadata chunk {label}")
                break
            offset += 8 + length + (length % 2)
    return issues


def check(root: Path = ROOT) -> list[str]:
    issues: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            issues.append(f"Missing required file: {rel}")

    if (root / ".legends-module").is_file():
        mod = (root / ".legends-module").read_text(encoding="utf-8").strip()
        if mod != "legends-stable-audio-3":
            issues.append(f".legends-module mismatch: {mod!r}")

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    init_py = (root / "src/legends_sa3/__init__.py").read_text(encoding="utf-8")
    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")

    m_py = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    m_init = re.search(r'^__version__\s*=\s*"([^"]+)"', init_py, re.M)
    m_cit = re.search(r'^version:\s*"?([^"\n]+)"?', citation, re.M)
    m_chg = re.search(r"^##\s+\[?v?(\d+\.\d+\.\d+)\]?", changelog, re.M)

    versions = {
        "pyproject.toml": m_py.group(1) if m_py else None,
        "__init__.py": m_init.group(1) if m_init else None,
        "CITATION.cff": m_cit.group(1).strip() if m_cit else None,
        "CHANGELOG.md": m_chg.group(1) if m_chg else None,
    }
    if len(set(versions.values())) != 1 or None in versions.values():
        issues.append(f"Version mismatch across files: {versions}")

    manifest_path = root / "assets" / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            entries = manifest_data.get("files", [])
            if not entries:
                issues.append("assets/manifest.json is missing 'files' entries")
        except (ValueError, KeyError) as exc:
            issues.append(f"assets/manifest.json invalid: {exc}")
            entries = []
        for entry in entries:
            target = root / "assets" / entry.get("name", "")
            try:
                raw = target.read_bytes()
            except OSError:
                issues.append(f"Manifest asset missing: {entry.get('name')}")
                continue
            if len(raw) != entry.get("bytes"):
                issues.append(f"Manifest byte mismatch: {entry.get('name')}")
            if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
                issues.append(f"Manifest hash mismatch: {entry.get('name')}")

    skill_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")
        ]
        for fn in filenames:
            path = Path(dirpath) / fn
            rel = path.relative_to(root).as_posix()
            if fn == "SKILL.md":
                skill_files.append(rel)
            if path.suffix.lower() in FORBIDDEN_FILES:
                issues.append(f"Forbidden file extension in repo: {rel}")
                continue
            if path.suffix.lower() in {".png", ".webp"}:
                issues.extend(f"{rel}: {err}" for err in image_metadata_issues(path))
                continue
            if path.suffix.lower() in TEXT_EXTS or path.name in {"LICENSE", "NOTICE"}:
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except UnicodeDecodeError:
                    issues.append(f"Non-UTF-8 file: {rel}")
                    continue
                if "\ufffd" in text:
                    issues.append(f"Replacement character U+FFFD in {rel}")
                if rel not in {"scripts/check_release.py", "src/legends_sa3/skill_distribution.py"}:
                    for pat in FORBIDDEN_PATTERNS:
                        if re.search(pat, text):
                            issues.append(f"Forbidden pattern {pat!r} matched in {rel}")
                if path.suffix.lower() == ".md":
                    if "\u2014" in text or "\u2013" in text:
                        issues.append(f"Em/en-dash found in markdown file: {rel}")
                    for target_link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                        if target_link.startswith(("https://", "http://", "mailto:", "#")):
                            continue
                        cleaned = unquote(target_link.split("#", 1)[0].split("?", 1)[0]).strip()
                        if not cleaned:
                            continue
                        resolved = (path.parent / cleaned).resolve()
                        if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                            issues.append(f"Broken or external local link: {rel}: {target_link}")

    if skill_files != ["skills/cto-legends/SKILL.md"]:
        issues.append(f"One-Skill Rule violation: found SKILL.md at {skill_files}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline release checks.")
    parser.add_argument("--root", type=Path, default=ROOT)
    options = parser.parse_args()
    issues = check(options.root)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        print(f"Release checks: FAIL ({len(issues)} issues)")
        return 1

    print("Release checks: PASS (0 issues)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

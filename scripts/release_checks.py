from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tarfile
import zipfile
from pathlib import Path

from sync_skill_adapters import FORBIDDEN_RELEASE_SUFFIXES, git_release_files

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.4.1"
PUBLIC_URL = "https://github.com/avalonreset/legends-stable-audio-3"
APACHE_LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
REQUIRED_FILES = (
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "CITATION.cff",
    "SUPPORT.md",
    "assets/PROVENANCE.md",
    "docs/platform-support.md",
    "scripts/export_public_source.py",
    "src/legends_sa3/hosted.py",
    "skills/legends-stable-audio-3/SKILL.md",
    "skills/legends-stable-audio-3/references/prompt-mastery.md",
    "skills/legends-stable-audio-3/references/surfaces-and-receipts.md",
    "skills/legends-stable-audio-3/references/mixing-and-adapters.md",
    "skills/legends-stable-audio-3/references/licensing-and-dependencies.md",
    "skills/legends-stable-audio-3/references/large-api.md",
    "skills/legends-stable-audio-3/references/mastery-eval.md",
)
ACTIVE_STALE_PATTERNS = {
    "legends-stable-audio-3.0": "retired point-oh slug",
    "Legends Stable Audio 3.0": "retired point-oh product name",
    "github.com/legends-pro/": "retired repository URL",
    "github.com/cto-legends/": "private repository URL",
    "source license pending": "superseded license gate",
    "license selection pending": "superseded license gate",
    "MIT or Apache-2.0": "superseded license selection",
    "the public repository does not exist": "stale pre-publication state",
    "no public release is being created": "stale pre-publication state",
    "repository is in public-release preparation": "stale pre-publication state",
}
HISTORICAL_RELEASES = {
    Path("docs/releases/v0.1.0.md"),
    Path("docs/releases/v0.1.1.md"),
    Path("docs/releases/v0.2.0.md"),
    Path("docs/releases/v0.3.0.md"),
}
STALE_SCAN_EXCLUSIONS = {
    Path("scripts/release_checks.py"),
    Path("scripts/sync_skill_adapters.py"),
}
SECRET_PATTERNS = (
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_tree(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required release file: {relative}")

    license_path = root / "LICENSE"
    if license_path.is_file() and sha256(license_path) != APACHE_LICENSE_SHA256:
        errors.append("LICENSE is not the complete unmodified Apache-2.0 text")

    version_surfaces = {
        "pyproject.toml": f'version = "{VERSION}"',
        "src/legends_sa3/__init__.py": f'__version__ = "{VERSION}"',
        "gemini-extension.json": f'"version": "{VERSION}"',
        "CITATION.cff": f'version: "{VERSION}"',
        "docs/releases/v0.4.1.md": "# v0.4.1 - Public Onboarding Polish",
    }
    for relative, marker in version_surfaces.items():
        path = root / relative
        if not path.is_file() or marker not in path.read_text(encoding="utf-8"):
            errors.append(f"{relative}: missing version marker {VERSION}")

    hardened_large_markers = {
        "src/legends_sa3/hosted.py": (
            "def write_submission_receipt(",
            "def write_recovery_receipt(",
            "Refusing to overwrite existing output",
            "Stable Audio result validation failed",
        ),
        "src/legends_sa3/cli.py": (
            "def cmd_large_result(",
            'large_sub.add_parser(\n        "result"',
            "_preflight_large_audio(request)",
            'large_generate.add_argument("--overwrite"',
        ),
    }
    for relative, markers in hardened_large_markers.items():
        path = root / relative
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        for marker in markers:
            if marker not in content:
                errors.append(f"{relative}: missing hosted Large hardening marker {marker}")

    for relative in ("README.md", "pyproject.toml", "SECURITY.md", "SUPPORT.md", "CITATION.cff"):
        path = root / relative
        if path.is_file() and PUBLIC_URL not in path.read_text(encoding="utf-8"):
            errors.append(f"{relative}: missing public repository URL")

    for relative in git_release_files(root):
        if any(part in {"models", "output", "runs", ".legends"} for part in relative.parts):
            errors.append(f"release tree contains forbidden local-state path: {relative.as_posix()}")
        if relative.suffix.lower() in FORBIDDEN_RELEASE_SUFFIXES:
            errors.append(f"release tree contains forbidden binary artifact: {relative.as_posix()}")
            continue
        path = root / relative
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            errors.append(f"release tree contains a token/key-shaped secret: {relative.as_posix()}")
        if relative not in HISTORICAL_RELEASES and relative not in STALE_SCAN_EXCLUSIONS:
            for pattern, description in ACTIVE_STALE_PATTERNS.items():
                if pattern.lower() in content.lower():
                    errors.append(f"{relative.as_posix()}: contains {description}")

    for historical in HISTORICAL_RELEASES:
        path = root / historical
        if path.is_file() and "histor" not in path.read_text(encoding="utf-8").lower()[:400]:
            errors.append(f"{historical.as_posix()}: historical private release is not clearly labeled")

    workflow = root / ".github" / "workflows" / "ci.yml"
    if not workflow.is_file():
        errors.append("missing .github/workflows/ci.yml")
    else:
        workflow_text = workflow.read_text(encoding="utf-8")
        if "permissions:\n  contents: read" not in workflow_text:
            errors.append("CI must declare least-privilege contents: read permissions")
        for line in workflow_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("uses:"):
                reference = stripped.split("@", 1)[-1].split()[0]
                if not re.fullmatch(r"[0-9a-f]{40}", reference):
                    errors.append(f"CI action is not pinned to a full commit SHA: {stripped}")
    return errors


def archive_members(path: Path) -> list[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    with tarfile.open(path, "r:gz") as archive:
        return archive.getnames()


def validate_archive(path: Path) -> list[str]:
    errors: list[str] = []
    members = [member.replace("\\", "/") for member in archive_members(path)]
    lowered = [member.lower() for member in members]
    for member in members:
        suffix = Path(member).suffix.lower()
        if suffix in FORBIDDEN_RELEASE_SUFFIXES:
            errors.append(f"{path.name}: forbidden artifact {member}")
        if any(part in {"models", "output", "runs", ".legends", ".git"} for part in Path(member).parts):
            errors.append(f"{path.name}: forbidden path {member}")

    required_suffixes = ["/license", "/notice", "/third_party_notices.md"]
    if path.suffix == ".whl":
        required_suffixes.extend(
            [
                "legends_sa3/_bundled_skill/legends-stable-audio-3/skill.md",
                "legends_sa3/_bundled_skill/legends-stable-audio-3/agents/openai.yaml",
                "legends_sa3/_bundled_skill/legends-stable-audio-3/references/licensing-and-dependencies.md",
                "legends_sa3/_bundled_skill/legends-stable-audio-3/references/large-api.md",
                "legends_sa3/_bundled_skill/legends-stable-audio-3/references/prompt-mastery.md",
                "legends_sa3/_bundled_skill/legends-stable-audio-3/references/surfaces-and-receipts.md",
                "legends_sa3/_bundled_skill/legends-stable-audio-3/references/mixing-and-adapters.md",
                "legends_sa3/_bundled_skill/legends-stable-audio-3/references/mastery-eval.md",
            ]
        )
    else:
        required_suffixes.extend(
            [
                "/agents.md",
                "/claude.md",
                "/gemini.md",
                "/grok.md",
                "/gemini-extension.json",
                "/.agents/skills/legends-stable-audio-3/skill.md",
                "/.claude/skills/legends-stable-audio-3/skill.md",
                "/skills/legends-stable-audio-3/skill.md",
                "/skills/legends-stable-audio-3/agents/openai.yaml",
                "/skills/legends-stable-audio-3/references/licensing-and-dependencies.md",
                "/skills/legends-stable-audio-3/references/large-api.md",
                "/skills/legends-stable-audio-3/references/prompt-mastery.md",
                "/skills/legends-stable-audio-3/references/surfaces-and-receipts.md",
                "/skills/legends-stable-audio-3/references/mixing-and-adapters.md",
                "/skills/legends-stable-audio-3/references/mastery-eval.md",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/skill.md",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/agents/openai.yaml",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/references/licensing-and-dependencies.md",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/references/large-api.md",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/references/prompt-mastery.md",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/references/surfaces-and-receipts.md",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/references/mixing-and-adapters.md",
                "/src/legends_sa3/_bundled_skill/legends-stable-audio-3/references/mastery-eval.md",
            ]
        )
    for suffix in required_suffixes:
        if not any(member.endswith(suffix) for member in lowered):
            errors.append(f"{path.name}: missing archive member ending with {suffix}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the public source tree and built artifacts.")
    parser.add_argument("--dist", type=Path, help="Optional directory containing one wheel and one sdist")
    args = parser.parse_args()

    errors = validate_tree()
    if args.dist:
        artifacts = sorted(args.dist.glob(f"legends_stable_audio_3-{VERSION}*"))
        wheels = [path for path in artifacts if path.suffix == ".whl"]
        sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
        if len(wheels) != 1 or len(sdists) != 1:
            errors.append(
                f"dist must contain exactly one v{VERSION} wheel and one v{VERSION} sdist"
            )
        for artifact in wheels + sdists:
            errors.extend(validate_archive(artifact))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("release checks: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from sync_skill_adapters import ROOT, git_release_files


def export_public_source(output: Path) -> Path:
    output = output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to replace existing export directory: {output}")

    files = git_release_files(ROOT)
    output.mkdir(parents=True)
    for relative in files:
        source = ROOT / relative
        if not source.is_file():
            continue
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    checks = (
        [sys.executable, "scripts/sync_skill_adapters.py"],
        [sys.executable, "scripts/release_checks.py"],
    )
    for command in checks:
        result = subprocess.run(command, cwd=output, text=True, capture_output=True)
        if result.returncode:
            details = (result.stdout + result.stderr).strip()
            raise RuntimeError(f"export validation failed: {' '.join(command)}\n{details}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a validated Git-less source snapshot for a clean public repository."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        exported = export_public_source(args.output)
    except (FileExistsError, RuntimeError) as error:
        raise SystemExit(str(error)) from error
    print(f"public source export: {exported}")
    print("validation: skill package ok; release checks ok; no Git history copied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

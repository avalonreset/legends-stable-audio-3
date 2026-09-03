from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, check=True, text=True, capture_output=True, env=env)
    if result.stdout.strip():
        print(result.stdout.strip())


def verify_artifact(artifact: Path, label: str) -> None:
    with tempfile.TemporaryDirectory(prefix=f"legends-sa3-{label}-") as temp:
        root = Path(temp)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cli = environment / ("Scripts/legends-sa3.exe" if os.name == "nt" else "bin/legends-sa3")
        run([str(python), "-m", "pip", "install", "--disable-pip-version-check", str(artifact)])
        run([str(python), "-c", "import legends_sa3; assert legends_sa3.__version__ == '0.4.1'"])
        run([str(cli), "--version"])
        run([str(cli), "skill", "validate"])
        install_target = root / "skills"
        run([str(cli), "skill", "install", "--target", str(install_target)])
        installed = install_target / "legends-stable-audio-3" / "SKILL.md"
        if not installed.is_file():
            raise RuntimeError(f"{label} install did not create {installed}")
        references = installed.parent / "references"
        expected_references = {
            "licensing-and-dependencies.md",
            "large-api.md",
            "mastery-eval.md",
            "mixing-and-adapters.md",
            "prompt-mastery.md",
            "surfaces-and-receipts.md",
        }
        actual_references = {path.name for path in references.glob("*.md")}
        if actual_references != expected_references:
            raise RuntimeError(
                f"{label} portable knowledge mismatch: {sorted(actual_references)}"
            )
        run([str(cli), "doctor"])
        run(
            [
                str(cli),
                "prompt",
                "--style",
                "deep dub techno, 118 BPM",
                "--count",
                "3",
            ]
        )
        run([str(cli), "plan", "--hours", "10", "--vram-gb", "24", "--crossfade", "12"])
        run(
            [
                str(cli),
                "large",
                "plan",
                "--prompt",
                "TrackType: SFX, VocalType: None, one-shot metal impact",
                "--duration",
                "10",
                "--output-format",
                "wav",
            ]
        )
        run([str(cli), "large", "result", "--help"])
        print(f"clean {label} install: ok")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install and smoke-test built wheel and source artifacts.")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    args = parser.parse_args()
    wheels = sorted(args.dist.glob("legends_stable_audio_3-0.4.1-*.whl"))
    sdists = sorted(args.dist.glob("legends_stable_audio_3-0.4.1.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("Expected exactly one v0.4.1 wheel and one v0.4.1 sdist")
    verify_artifact(wheels[0].resolve(), "wheel")
    verify_artifact(sdists[0].resolve(), "sdist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from legends_sa3.skill_distribution import bundled_skill_path, install_bundled_skill, validate_skill

ROOT = Path(__file__).resolve().parents[1]


class SkillDistributionTests(unittest.TestCase):
    def assert_portable_skill(self, skill_root: Path):
        markdown_link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for markdown_path in skill_root.rglob("*.md"):
            text = markdown_path.read_text(encoding="utf-8")
            lowered = text.lower()
            self.assertNotIn("e:\\empire", lowered)
            self.assertNotIn("c:\\users\\", lowered)
            self.assertNotIn("[[", text)
            for target in markdown_link.findall(text):
                if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                    continue
                resolved = (markdown_path.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(resolved.is_file(), f"{markdown_path}: {target}")
                self.assertIn(skill_root.resolve(), resolved.parents)

    def test_python_package_bundle_validates(self):
        self.assertEqual(validate_skill(bundled_skill_path()), [])

    def test_python_package_bundle_installs_only_to_explicit_target(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "agent-skills"
            installed = install_bundled_skill(target)

            self.assertEqual(installed, target.resolve() / "legends-stable-audio-3")
            self.assertEqual(validate_skill(installed), [])
            self.assert_portable_skill(installed)
            with self.assertRaises(FileExistsError):
                install_bundled_skill(target)

    def test_canonical_skill_and_mirrors_are_identical(self):
        manifest = json.loads((ROOT / "skill-package.json").read_text(encoding="utf-8"))
        canonical = ROOT / manifest["canonical"]
        expected = {
            path.relative_to(canonical).as_posix(): path.read_bytes()
            for path in canonical.rglob("*")
            if path.is_file()
        }

        for mirror in manifest["mirrors"].values():
            mirror_root = ROOT / mirror
            actual = {
                path.relative_to(mirror_root).as_posix(): path.read_bytes()
                for path in mirror_root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual, expected, mirror)

    def test_release_skill_validator_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/sync_skill_adapters.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skill package: ok", result.stdout)

    def test_install_target_gets_complete_canonical_package(self):
        manifest = json.loads((ROOT / "skill-package.json").read_text(encoding="utf-8"))
        canonical = ROOT / manifest["canonical"]
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/sync_skill_adapters.py",
                    "--install-target",
                    temp,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            installed = Path(temp) / manifest["name"]

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                {
                    path.relative_to(installed).as_posix(): path.read_bytes()
                    for path in installed.rglob("*")
                    if path.is_file()
                },
                {
                    path.relative_to(canonical).as_posix(): path.read_bytes()
                    for path in canonical.rglob("*")
                    if path.is_file()
                },
            )
            self.assert_portable_skill(installed)


if __name__ == "__main__":
    unittest.main()

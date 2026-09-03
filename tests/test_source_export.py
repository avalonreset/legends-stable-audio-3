import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceExportTests(unittest.TestCase):
    def test_gitless_source_export_validates(self):
        with tempfile.TemporaryDirectory() as temp:
            export = Path(temp) / "legends-stable-audio-3"
            created = subprocess.run(
                [
                    sys.executable,
                    "scripts/export_public_source.py",
                    "--output",
                    str(export),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            self.assertFalse((export / ".git").exists())

            skill = subprocess.run(
                [sys.executable, "scripts/sync_skill_adapters.py"],
                cwd=export,
                text=True,
                capture_output=True,
            )
            release = subprocess.run(
                [sys.executable, "scripts/release_checks.py"],
                cwd=export,
                text=True,
                capture_output=True,
            )

            self.assertEqual(skill.returncode, 0, skill.stdout + skill.stderr)
            self.assertEqual(release.returncode, 0, release.stdout + release.stderr)

    def test_export_refuses_existing_target(self):
        with tempfile.TemporaryDirectory() as temp:
            existing = Path(temp) / "existing"
            existing.mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/export_public_source.py",
                    "--output",
                    str(existing),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to replace existing export directory", result.stderr)


if __name__ == "__main__":
    unittest.main()

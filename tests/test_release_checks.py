import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseChecksTests(unittest.TestCase):
    def test_release_tree_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/release_checks.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("release checks: ok", result.stdout)


if __name__ == "__main__":
    unittest.main()

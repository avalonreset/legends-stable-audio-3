import unittest
from pathlib import Path

import legends_sa3


class MetadataTests(unittest.TestCase):
    def test_package_version_matches_pyproject(self):
        root = Path(__file__).resolve().parents[1]
        version_line = next(
            line
            for line in (root / "pyproject.toml").read_text(encoding="utf-8").splitlines()
            if line.startswith("version = ")
        )
        pyproject_version = version_line.split('"')[1]

        self.assertEqual(legends_sa3.__version__, pyproject_version)


if __name__ == "__main__":
    unittest.main()

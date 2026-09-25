import re
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

    def test_repo_registers_no_module_skill(self):
        # Router-native reset: the repo must not register
        # legends-stable-audio-3 as its own skill. Only the pinned
        # cto-legends router copy may live under skills/.
        self.assertFalse((ROOT / "skills" / "legends-stable-audio-3").exists())
        self.assertFalse((ROOT / "SKILL.md").is_file())
        self.assertFalse((ROOT / "skill-package.json").is_file())
        for mirror in (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills"):
            self.assertFalse(mirror.is_dir() and any(mirror.iterdir()))
        vendored = ROOT / "skills" / "cto-legends" / "SKILL.md"
        self.assertTrue(vendored.is_file())


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

from legends_sa3.lora_studio import (
    UNDERFIT_COMMIT,
    UNDERFIT_LICENSE_SHA256,
    UNDERFIT_REPO_URL,
    clone_or_update_underfit,
    default_adapter_name,
    import_adapter,
    list_imported_adapters,
    normalize_git_url,
    slugify_adapter_name,
    verify_underfit_checkout,
)


class LoraStudioTests(unittest.TestCase):
    def make_underfit_layout(self, root: Path) -> None:
        for relative in (".git/config", "README.md", "LICENSE", "install.sh", "run.sh", "dashboard/server.py"):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test", encoding="utf-8")

    def test_git_url_normalization_accepts_canonical_dot_git_form(self):
        self.assertEqual(
            normalize_git_url("https://github.com/dada-bots/underfit.git/"),
            normalize_git_url(UNDERFIT_REPO_URL),
        )

    @patch("legends_sa3.lora_studio.sha256_file", return_value=UNDERFIT_LICENSE_SHA256)
    @patch("legends_sa3.lora_studio.git_text")
    def test_underfit_checkout_verifies_origin_commit_license_and_layout(self, git_text_mock, _hash_mock):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_underfit_layout(root)
            git_text_mock.side_effect = [UNDERFIT_REPO_URL + ".git", UNDERFIT_COMMIT]

            verify_underfit_checkout(root)

    @patch("legends_sa3.lora_studio.sha256_file", return_value=UNDERFIT_LICENSE_SHA256)
    @patch("legends_sa3.lora_studio.git_text", side_effect=["https://example.invalid/underfit", UNDERFIT_COMMIT])
    def test_underfit_checkout_rejects_wrong_origin(self, _git_text_mock, _hash_mock):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_underfit_layout(root)

            with self.assertRaisesRegex(RuntimeError, "Unexpected Underfit origin"):
                verify_underfit_checkout(root)

    @patch("legends_sa3.lora_studio.sha256_file", return_value=UNDERFIT_LICENSE_SHA256)
    @patch("legends_sa3.lora_studio.git_text", side_effect=[UNDERFIT_REPO_URL, "0" * 40])
    def test_underfit_checkout_rejects_wrong_commit(self, _git_text_mock, _hash_mock):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_underfit_layout(root)

            with self.assertRaisesRegex(RuntimeError, "Unexpected Underfit commit"):
                verify_underfit_checkout(root)

    @patch("legends_sa3.lora_studio.sha256_file", return_value="0" * 64)
    @patch("legends_sa3.lora_studio.git_text", side_effect=[UNDERFIT_REPO_URL, UNDERFIT_COMMIT])
    def test_underfit_checkout_rejects_license_mismatch(self, _git_text_mock, _hash_mock):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_underfit_layout(root)

            with self.assertRaisesRegex(RuntimeError, "Unexpected Underfit LICENSE hash"):
                verify_underfit_checkout(root)

    @patch("legends_sa3.lora_studio.verify_underfit_checkout")
    @patch("legends_sa3.lora_studio.subprocess.run")
    @patch("legends_sa3.lora_studio.git_text", return_value="")
    @patch("legends_sa3.lora_studio.ensure_git_available")
    def test_underfit_update_fetches_only_the_pinned_commit(
        self, _git_mock, _git_text_mock, run_mock, verify_mock
    ):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()

            clone_or_update_underfit(root=root, update=True)

            self.assertEqual(verify_mock.call_count, 2)
            self.assertIn(
                call(
                    ["git", "-C", str(root), "fetch", "--depth", "1", "origin", UNDERFIT_COMMIT],
                    check=True,
                ),
                run_mock.call_args_list,
            )

    def test_slugify_adapter_name(self):
        self.assertEqual(slugify_adapter_name("My Custom Style!"), "my-custom-style")
        self.assertEqual(slugify_adapter_name("  Weird___Name  "), "weird-name")

    def test_default_adapter_name_uses_parent_for_numeric_checkpoint(self):
        source = Path("state/runs/dadabots-breaks/5000.safetensors")

        self.assertEqual(default_adapter_name(source), "dadabots-breaks-5000")

    def test_import_adapter_copies_checkpoint_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "state" / "runs" / "my-run" / "5000.safetensors"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"fake adapter")

            imported = import_adapter(
                source=source,
                adapters_dir=root / "adapters",
                name="My Style",
                source_run="my-run",
            )

            self.assertTrue(imported.adapter_path.exists())
            self.assertEqual(imported.adapter_path.name, "my-style.safetensors")
            manifest = json.loads(imported.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], "my-style")
            self.assertEqual(manifest["source_run"], "my-run")
            self.assertEqual(manifest["format"], "native-stable-audio-3-lora")
            self.assertEqual(manifest["sha256"], imported.sha256)
            self.assertIn("legends-sa3 generate --lora-ckpt-path", manifest["loader_hint"])

    def test_list_imported_adapters_reads_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "checkpoint.safetensors"
            source.write_bytes(b"fake adapter")
            import_adapter(source=source, adapters_dir=root / "adapters", name="Listed")

            adapters = list_imported_adapters(root / "adapters")

            self.assertEqual(len(adapters), 1)
            self.assertEqual(adapters[0]["name"], "listed")
            self.assertTrue(adapters[0]["exists"])

    def test_import_rejects_non_safetensors(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "checkpoint.pt"
            source.write_bytes(b"not supported")

            with self.assertRaises(ValueError):
                import_adapter(source=source, adapters_dir=Path(temp) / "adapters")


if __name__ == "__main__":
    unittest.main()

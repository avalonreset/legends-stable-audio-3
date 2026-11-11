import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from legends_sa3.doctor import assert_model_dir
from legends_sa3.hf_download import DEFAULT_MODEL_REVISIONS, download_model
from legends_sa3.sa3_runner import validate_lora_ckpt_paths


class ModelDownloadTests(unittest.TestCase):
    def test_download_fetches_and_wires_complete_conditioner_bundle(self):
        calls = []

        def snapshot_download(**kwargs):
            calls.append(kwargs)
            output = Path(kwargs["local_dir"])
            conditioner = output / "t5gemma-b-b-ul2"
            conditioner.mkdir(parents=True)
            (output / "model.safetensors").write_bytes(b"model")
            (conditioner / "model.safetensors").write_bytes(b"conditioner")
            (conditioner / "config.json").write_text("{}", encoding="utf-8")
            (conditioner / "tokenizer.json").write_text("{}", encoding="utf-8")
            (output / "model_config.json").write_text(
                json.dumps(
                    {
                        "model": {
                            "conditioning": {
                                "configs": [
                                    {
                                        "type": "t5gemma",
                                        "config": {"model_path": "stale/path"},
                                    }
                                ]
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

        fake_hub = types.SimpleNamespace(snapshot_download=snapshot_download)
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            sys.modules, {"huggingface_hub": fake_hub}
        ):
            output = download_model("medium", Path(temp) / "model")
            assert_model_dir(output)
            config = json.loads((output / "model_config.json").read_text(encoding="utf-8"))
            path = config["model"]["conditioning"]["configs"][0]["config"]["model_path"]
            self.assertEqual(path, str((output / "t5gemma-b-b-ul2").resolve()))

        self.assertIn("t5gemma-b-b-ul2/*", calls[0]["allow_patterns"])
        self.assertEqual(calls[0]["revision"], "d4d3579395a8ac0df4ab13b5b1d7138ce7290f81")
        self.assertEqual(calls[0]["revision"], DEFAULT_MODEL_REVISIONS["medium"])
        self.assertIn("*.ckpt", calls[0]["ignore_patterns"])
        self.assertIn("*.pkl", calls[0]["ignore_patterns"])

    def test_lora_ckpt_validation_rejects_non_safetensors(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "adapter.ckpt"
            bad.write_bytes(b"pickle")
            with self.assertRaisesRegex(ValueError, r"\.safetensors"):
                validate_lora_ckpt_paths([bad])
            good = Path(temp) / "adapter.safetensors"
            good.write_bytes(b"safetensors")
            self.assertEqual(validate_lora_ckpt_paths([good]), [good.resolve()])

    def test_incomplete_bundle_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "model_config.json").write_text("{}", encoding="utf-8")
            (root / "model.safetensors").write_bytes(b"model")
            with self.assertRaisesRegex(FileNotFoundError, "T5Gemma|t5gemma"):
                assert_model_dir(root)


if __name__ == "__main__":
    unittest.main()

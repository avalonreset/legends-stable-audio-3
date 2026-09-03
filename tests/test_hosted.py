import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from legends_sa3.cli import main
from legends_sa3.hosted import (
    HostedAPIError,
    LargeRequest,
    poll_large_result,
    submit_large,
    write_public_receipt,
    write_submission_receipt,
)


class FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def getcode(self):
        return self.status

    def read(self):
        return self.body


class HostedLargeTests(unittest.TestCase):
    def test_text_plan_matches_live_schema(self):
        request = LargeRequest(operation="text-to-audio", prompt="Dark dub, 118 BPM")
        plan = request.public_plan()
        self.assertEqual(plan["model"], "stable-audio-3")
        self.assertTrue(plan["endpoint"].endswith("/stable-audio/text-to-audio"))
        self.assertEqual(plan["request"]["duration"], "190")
        self.assertEqual(plan["reference_credits"], 26)

    def test_audio_operations_require_supported_input(self):
        with self.assertRaisesRegex(ValueError, "requires --audio"):
            LargeRequest(operation="audio-to-audio", prompt="Transform").validate()
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.wav"
            source.write_bytes(b"RIFFfake")
            request = LargeRequest(
                operation="inpaint",
                prompt="Replace the break",
                duration=100,
                audio=source,
                mask_start=20,
                mask_end=40,
            )
            self.assertEqual(request.form_fields()["mask_end"], "40")

    def test_submit_and_poll_do_not_put_key_in_body_or_receipt(self):
        submitted = FakeResponse(202, json.dumps({"id": "gen-123"}).encode())
        pending = FakeResponse(202, json.dumps({"id": "gen-123", "status": "in-progress"}).encode())
        finished = FakeResponse(
            200,
            b"RIFF\x04\x00\x00\x00WAVEdata",
            {
                "Content-Type": "audio/wav",
                "seed": "42",
                "finish-reason": "SUCCESS",
                "x-request-id": "req-1",
            },
        )
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            return [submitted, pending, finished][len(requests) - 1]

        with tempfile.TemporaryDirectory() as temp, patch(
            "urllib.request.urlopen", side_effect=fake_urlopen
        ):
            request = LargeRequest(operation="text-to-audio", prompt="One-shot impact", duration=10)
            generation_id = submit_large(request, "secret-test-key")
            output = Path(temp) / "result.wav"
            result = poll_large_result(
                generation_id,
                "secret-test-key",
                output,
                output_format="wav",
                poll_interval=0,
                sleep=lambda _: None,
            )
            self.assertEqual(result["output"], "result.wav")
            self.assertEqual(output.read_bytes(), b"RIFF\x04\x00\x00\x00WAVEdata")
            self.assertNotIn(b"secret-test-key", requests[0].data)

            receipt = Path(temp) / "receipt.json"
            write_public_receipt(receipt, request, result, confirmed_live_credits=26)
            receipt_text = receipt.read_text(encoding="utf-8")
            self.assertNotIn("secret-test-key", receipt_text)
            self.assertNotIn(str(Path(temp).resolve()), receipt_text)

    def test_submission_receipt_preserves_resume_id_without_private_path(self):
        with tempfile.TemporaryDirectory() as temp:
            request = LargeRequest(operation="text-to-audio", prompt="One-shot impact", duration=10)
            receipt = Path(temp) / "pending.json"
            write_submission_receipt(
                receipt,
                request,
                "gen_123-safe",
                confirmed_live_credits=26,
                output_file=str(Path(temp) / "private" / "result.wav"),
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["generation_id"], "gen_123-safe")
            self.assertEqual(payload["output_file"], "result.wav")
            self.assertEqual(payload["status"], "submitted")
            self.assertNotIn(str(Path(temp).resolve()), receipt.read_text(encoding="utf-8"))

    def test_poll_refuses_overwrite_before_network(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.wav"
            output.write_bytes(b"existing")
            with patch("urllib.request.urlopen") as urlopen:
                with self.assertRaisesRegex(FileExistsError, "--overwrite"):
                    poll_large_result("gen-123", "secret", output, output_format="wav")
            urlopen.assert_not_called()

    def test_poll_rejects_non_audio_success_payload(self):
        response = FakeResponse(200, b'{"error":"not audio"}', {"Content-Type": "application/json"})
        with tempfile.TemporaryDirectory() as temp, patch(
            "urllib.request.urlopen", return_value=response
        ):
            output = Path(temp) / "result.wav"
            with self.assertRaisesRegex(HostedAPIError, "validation failed"):
                poll_large_result("gen-123", "secret", output, output_format="wav")
            self.assertFalse(output.exists())

    def test_submission_network_error_warns_against_duplicate_paid_call(self):
        request = LargeRequest(operation="text-to-audio", prompt="One-shot impact", duration=10)
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection reset"),
        ):
            with self.assertRaisesRegex(HostedAPIError, "Do not blindly submit again"):
                submit_large(request, "secret")

    def test_cli_refuses_paid_call_without_confirmation(self):
        with patch.dict(os.environ, {"STABILITY_API_KEY": "test"}):
            with self.assertRaisesRegex(SystemExit, "--confirm-paid"):
                main(
                    [
                        "large",
                        "generate",
                        "--prompt",
                        "test",
                        "--output",
                        "test.wav",
                        "--confirmed-live-credits",
                        "26",
                    ]
                )

    def test_cli_rejects_nonpositive_credit_confirmation(self):
        with patch.dict(os.environ, {"STABILITY_API_KEY": "test"}):
            with self.assertRaisesRegex(SystemExit, "greater than zero"):
                main(
                    [
                        "large",
                        "generate",
                        "--prompt",
                        "test",
                        "--output",
                        "test.wav",
                        "--confirmed-live-credits",
                        "0",
                        "--confirm-paid",
                    ]
                )

    def test_cli_refuses_existing_output_before_paid_submission(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"STABILITY_API_KEY": "test"}
        ), patch("legends_sa3.cli.submit_large") as submit:
            output = Path(temp) / "result.wav"
            output.write_bytes(b"existing")
            with self.assertRaisesRegex(SystemExit, "--overwrite"):
                main(
                    [
                        "large",
                        "generate",
                        "--prompt",
                        "test",
                        "--output",
                        str(output),
                        "--confirmed-live-credits",
                        "26",
                        "--confirm-paid",
                    ]
                )
            submit.assert_not_called()

    def test_cli_rejects_wrong_output_extension_before_paid_submission(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"STABILITY_API_KEY": "test"}
        ), patch("legends_sa3.cli.submit_large") as submit:
            with self.assertRaisesRegex(SystemExit, "must end in .wav"):
                main(
                    [
                        "large",
                        "generate",
                        "--prompt",
                        "test",
                        "--output",
                        str(Path(temp) / "result.mp3"),
                        "--confirmed-live-credits",
                        "26",
                        "--confirm-paid",
                    ]
                )
            submit.assert_not_called()

    def test_cli_rejects_directory_output_before_paid_submission(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"STABILITY_API_KEY": "test"}
        ), patch("legends_sa3.cli.submit_large") as submit:
            output = Path(temp) / "result.wav"
            output.mkdir()
            with self.assertRaisesRegex(SystemExit, "file target is a directory"):
                main(
                    [
                        "large",
                        "generate",
                        "--prompt",
                        "test",
                        "--output",
                        str(output),
                        "--confirmed-live-credits",
                        "26",
                        "--confirm-paid",
                        "--overwrite",
                    ]
                )
            submit.assert_not_called()

    def test_cli_rejects_invalid_input_duration_before_paid_submission(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"STABILITY_API_KEY": "test"}
        ), patch("legends_sa3.cli.ffprobe_duration", return_value=3.0), patch(
            "legends_sa3.cli.submit_large"
        ) as submit:
            source = Path(temp) / "short.wav"
            source.write_bytes(b"RIFFfake")
            with self.assertRaisesRegex(SystemExit, "6-380 seconds"):
                main(
                    [
                        "large",
                        "generate",
                        "--operation",
                        "audio-to-audio",
                        "--prompt",
                        "test",
                        "--audio",
                        str(source),
                        "--output",
                        str(Path(temp) / "result.wav"),
                        "--confirmed-live-credits",
                        "26",
                        "--confirm-paid",
                    ]
                )
            submit.assert_not_called()

    def test_paid_submission_writes_recovery_receipt_before_polling(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"STABILITY_API_KEY": "test"}
        ), patch("legends_sa3.cli.submit_large", return_value="gen-123"), patch(
            "legends_sa3.cli.poll_large_result",
            side_effect=TimeoutError("still running"),
        ):
            output = Path(temp) / "result.wav"
            receipt = Path(temp) / "pending.json"
            with self.assertRaisesRegex(SystemExit, "still running"):
                main(
                    [
                        "large",
                        "generate",
                        "--prompt",
                        "test",
                        "--output",
                        str(output),
                        "--receipt",
                        str(receipt),
                        "--confirmed-live-credits",
                        "26",
                        "--confirm-paid",
                    ]
                )
            pending = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(pending["generation_id"], "gen-123")
            self.assertEqual(pending["status"], "submitted")
            self.assertFalse(output.exists())

    def test_cli_can_resume_existing_generation_without_submission(self):
        result = {
            "generation_id": "gen-123",
            "output": "result.wav",
            "output_format": "wav",
            "bytes": 16,
            "sha256": "abc",
        }
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"STABILITY_API_KEY": "test"}
        ), patch("legends_sa3.cli.poll_large_result", return_value=result) as poll, patch(
            "legends_sa3.cli.write_recovery_receipt",
            return_value=Path(temp) / "result.wav.receipt.json",
        ), patch("legends_sa3.cli.submit_large") as submit:
            output = Path(temp) / "result.wav"
            code = main(
                [
                    "large",
                    "result",
                    "--generation-id",
                    "gen-123",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(code, 0)
            submit.assert_not_called()
            poll.assert_called_once()


if __name__ == "__main__":
    unittest.main()

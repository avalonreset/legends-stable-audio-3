import copy
import shutil
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from legends_sa3.cli import build_parser
from legends_sa3.hosted import LargeRequest
from legends_sa3.mixer import decode_audio
from legends_sa3.production import (
    blend,
    plan_production,
    render_arrangement,
    validate_arrangement,
)


def fixture():
    return {
        "tracks": [
            {"source": f"{i}.wav", "selection_reason": "full-song candidate", "stage": "production"}
            for i in range(3)
        ],
        "transitions": [
            {"seconds": 1, "reason": "first ending", "curve": "linear"},
            {"seconds": 2, "reason": "second ending", "curve": "equal-power"},
        ],
    }


class ProductionTests(unittest.TestCase):
    def test_hosted_defaults_maximize_full_song_value(self):
        self.assertEqual(LargeRequest("text-to-audio", "music").duration, 380)
        args = build_parser().parse_args(["large", "plan", "--prompt", "music"])
        self.assertEqual(args.duration, 380)
        args = build_parser().parse_args(["large", "plan", "--prompt", "cue", "--duration", "20"])
        self.assertEqual(args.duration, 20)

    def test_approximate_target_does_not_shorten_songs(self):
        plan = plan_production(minutes=20)
        self.assertEqual(plan["song_seconds"], 380)
        self.assertEqual(plan["song_count"], 4)
        self.assertEqual(plan["estimated_mix_seconds"], 1484)
        self.assertEqual(plan["estimated_credits"], 104)
        self.assertFalse(plan["trim_to_target"])

    def test_exact_edit_is_explicit_and_separate(self):
        plan = plan_production(minutes=20, runtime_intent="exact")
        self.assertTrue(plan["exact_edit_required"])
        self.assertFalse(plan["trim_to_target"])

    def test_invalid_planning_numbers(self):
        for seconds in (float("nan"), float("inf"), 381, -1, True):
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                plan_production(minutes=20, song_seconds=seconds)

    def test_full_boundaries_are_preserved_by_default(self):
        cuts = validate_arrangement(fixture(), [380, 380, 380])
        self.assertEqual([c["seconds"] for c in cuts], [380]*3)

    def test_discovery_cannot_be_silently_promoted(self):
        doc = fixture()
        doc["tracks"][0]["stage"] = "discovery"
        with self.assertRaisesRegex(ValueError, "promotion"):
            validate_arrangement(doc, [380]*3)
        doc["tracks"][0]["promotion_reason"] = "Explicitly reviewed for short-cue brief"
        validate_arrangement(doc, [380]*3)

    def test_trims_need_reasons(self):
        for key, value in (("in_seconds", 5), ("out_seconds", 300)):
            doc = fixture()
            doc["tracks"][0][key] = value
            with self.assertRaisesRegex(ValueError, "trim_reason"):
                validate_arrangement(doc, [380]*3)

    def test_invalid_or_colliding_transitions_fail(self):
        for seconds in (float("nan"), -1, 4):
            doc = fixture()
            doc["transitions"][0]["seconds"] = seconds
            with self.assertRaises(ValueError):
                validate_arrangement(doc, [5]*3)
        doc = fixture()
        doc["transitions"][0]["reason"] = ""
        with self.assertRaises(ValueError):
            validate_arrangement(doc, [380]*3)

    def test_blend_does_not_silently_clip(self):
        data = np.ones((101, 2), dtype=np.float32)
        result = blend(data, data, "equal-power")
        self.assertGreater(float(result.max()), 1.4)
        self.assertAlmostEqual(float(result[0, 0]), 1)
        self.assertAlmostEqual(float(result[-1, 0]), 1, places=6)

    def test_independent_fades_preserve_the_natural_tail(self):
        data = np.ones((101, 2), dtype=np.float32)
        result = blend(data, data, "linear", fade_in_samples=10, fade_out_samples=10)
        self.assertEqual(float(result[0, 0]), 1)
        self.assertEqual(float(result[50, 0]), 2)
        self.assertEqual(float(result[-1, 0]), 1)
        doc = fixture()
        doc["transitions"][0]["fade_in_seconds"] = 2
        with self.assertRaises(ValueError):
            validate_arrangement(doc, [380]*3)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg integration test")
    def test_streaming_variable_fades_preserve_count_and_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            rate = 8000
            for i in range(3):
                samples = np.full((5*rate, 2), (i+1)*1000, dtype="<i2")
                with wave.open(str(base/f"{i}.wav"), "wb") as wav:
                    wav.setnchannels(2)
                    wav.setsampwidth(2)
                    wav.setframerate(rate)
                    wav.writeframes(samples.tobytes())
            doc = fixture()
            original = copy.deepcopy(doc)
            output = base/"mixed.wav"
            receipt = render_arrangement(doc, output, base=base, rate=rate)
            self.assertEqual(doc, original)
            self.assertEqual(receipt["rendered_samples"], 12*rate)
            self.assertEqual(receipt["listening_review"], "unreviewed")
            audio = decode_audio(output, rate, 2)
            self.assertEqual(len(audio), 12*rate)
            self.assertAlmostEqual(float(audio[0, 0]), 1000/32768)
            self.assertAlmostEqual(float(audio[-1, 0]), 3000/32768)
            self.assertEqual([t["mix_start_seconds"] for t in receipt["tracks"]], [0, 4, 7])
            with self.assertRaises(FileExistsError):
                render_arrangement(doc, output, base=base, rate=rate)
            for join in doc["transitions"]:
                join["seconds"] = 0
            receipt = render_arrangement(doc, base/"butt-joins.wav", base=base, rate=rate)
            self.assertEqual(receipt["rendered_samples"], 15*rate)
            self.assertEqual(len(receipt["transitions"]), 2)


if __name__ == "__main__":
    unittest.main()

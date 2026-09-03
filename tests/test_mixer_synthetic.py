import math
import shutil
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from legends_sa3.doctor import ffprobe_duration
from legends_sa3.mixer import mix_tracks


def write_tone(
    path: Path,
    frequency: float,
    seconds: float,
    sample_rate: int = 44_100,
    *,
    leading_silence: float = 0.0,
    trailing_silence: float = 0.0,
) -> None:
    tone_frames = int(seconds * sample_rate)
    t = np.arange(tone_frames, dtype=np.float32) / sample_rate
    mono = 0.2 * np.sin(2 * math.pi * frequency * t)
    leading = np.zeros(int(leading_silence * sample_rate), dtype=np.float32)
    trailing = np.zeros(int(trailing_silence * sample_rate), dtype=np.float32)
    mono = np.concatenate([leading, mono, trailing])
    stereo = np.stack([mono, mono], axis=1)
    pcm = np.clip(stereo * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def write_silence(path: Path, seconds: float, sample_rate: int = 44_100) -> None:
    frames = int(seconds * sample_rate)
    stereo = np.zeros((frames, 2), dtype="<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(stereo.tobytes())


class MixerSyntheticTests(unittest.TestCase):
    def test_streaming_crossfade_duration(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("ffmpeg/ffprobe not installed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tracks = []
            for index, frequency in enumerate([220, 330, 440], start=1):
                path = root / f"{index:03d}.wav"
                write_tone(path, frequency, 2.0)
                tracks.append(path)

            output = root / "mix.mp3"
            manifest = mix_tracks(tracks, output, crossfade_seconds=0.25, bitrate="192k")
            duration = ffprobe_duration(output)
            self.assertTrue(output.exists())
            self.assertAlmostEqual(manifest["rendered_seconds_estimate"], 5.5, places=2)
            self.assertAlmostEqual(duration, 5.5, delta=0.15)

    def test_active_cue_trims_generated_dead_air(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("ffmpeg/ffprobe not installed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "001.wav"
            second = root / "002.wav"
            write_tone(first, 220, 2.0, trailing_silence=1.0)
            write_tone(second, 330, 2.0, leading_silence=1.0)

            output = root / "mix.mp3"
            manifest = mix_tracks(
                [first, second],
                output,
                crossfade_seconds=0.5,
                bitrate="192k",
                cue_padding_seconds=0.0,
            )
            duration = ffprobe_duration(output)
            self.assertTrue(output.exists())
            self.assertAlmostEqual(manifest["rendered_seconds_estimate"], 3.5, places=2)
            self.assertAlmostEqual(duration, 3.5, delta=0.15)
            self.assertAlmostEqual(manifest["tracks"][0]["tail_trim_seconds"], 1.0, delta=0.11)
            self.assertAlmostEqual(manifest["tracks"][1]["head_trim_seconds"], 1.0, delta=0.11)

    def test_active_cue_rejects_all_silence(self):
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg not installed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silent = root / "silent.wav"
            write_silence(silent, 2.0)

            with self.assertRaisesRegex(RuntimeError, "no usable audio"):
                mix_tracks([silent], root / "mix.mp3", crossfade_seconds=0.0)

    def test_fail_quality_gate_preflights_before_temp_output(self):
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg not installed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            silent = root / "silent.wav"
            output = root / "mix.mp3"
            write_silence(silent, 2.0)

            with self.assertRaisesRegex(RuntimeError, "no usable audio"):
                mix_tracks([silent], output, crossfade_seconds=0.0, quality_gate="fail")
            self.assertFalse(output.exists())
            self.assertFalse((root / "mix.tmp.mp3").exists())


if __name__ == "__main__":
    unittest.main()

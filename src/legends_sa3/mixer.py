from __future__ import annotations

import json
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

MIN_DBFS = -120.0
MIX_POLICIES = ("active-cue", "strict")
QUALITY_GATES = ("warn", "fail", "off")


@dataclass
class TrackAnalysis:
    source_path: str
    input_samples: int
    input_seconds: float
    max_dbfs: float
    rms_dbfs: float
    cue_start_sample: int
    cue_end_sample: int
    silence_start_sample: int
    silence_end_sample: int
    leading_quiet_seconds: float
    trailing_quiet_seconds: float
    leading_silence_seconds: float
    trailing_silence_seconds: float
    active_seconds: float
    warnings: list[str]


def decode_audio(path: Path, sample_rate: int, channels: int) -> np.ndarray:
    args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-",
    ]
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decode failed for {path}:\n{proc.stderr.decode(errors='replace')}")
    frame_bytes = channels * np.dtype("<f4").itemsize
    usable = len(proc.stdout) - (len(proc.stdout) % frame_bytes)
    return np.frombuffer(proc.stdout[:usable], dtype="<f4").reshape((-1, channels))


def start_encoder(output_path: Path, sample_rate: int, channels: int, bitrate: str) -> subprocess.Popen:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-i",
        "-",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(output_path),
    ]
    return subprocess.Popen(args, stdin=subprocess.PIPE)


def write_audio(encoder: subprocess.Popen, audio: np.ndarray, sample_rate: int, channels: int) -> None:
    if encoder.stdin is None:
        raise RuntimeError("encoder stdin is closed")
    if audio.size == 0:
        return
    contiguous = np.ascontiguousarray(audio, dtype="<f4")
    view = memoryview(contiguous).cast("B")
    chunk_size = sample_rate * channels * 4 * 60
    for offset in range(0, len(view), chunk_size):
        encoder.stdin.write(view[offset : offset + chunk_size])


def linear_crossfade(previous_tail: np.ndarray, next_head: np.ndarray) -> np.ndarray:
    n = min(previous_tail.shape[0], next_head.shape[0])
    fade = np.linspace(0.0, 1.0, n, endpoint=False, dtype=np.float32).reshape((-1, 1))
    mixed = previous_tail[-n:] * (1.0 - fade) + next_head[:n] * fade
    return np.clip(mixed, -1.0, 1.0)


def _dbfs(value: float) -> float:
    if value <= 1e-12:
        return MIN_DBFS
    return max(MIN_DBFS, 20.0 * math.log10(value))


def _first_last_true(mask: np.ndarray) -> tuple[int | None, int | None]:
    matches = np.flatnonzero(mask)
    if matches.size == 0:
        return None, None
    return int(matches[0]), int(matches[-1])


def _frame_rms_dbfs(audio: np.ndarray, frame_samples: int) -> np.ndarray:
    if audio.shape[0] == 0:
        return np.array([], dtype=np.float32)
    frame_count = math.ceil(audio.shape[0] / frame_samples)
    levels = np.empty(frame_count, dtype=np.float32)
    for index in range(frame_count):
        start = index * frame_samples
        end = min(audio.shape[0], start + frame_samples)
        frame = audio[start:end].astype(np.float64, copy=False)
        levels[index] = _dbfs(float(np.sqrt(np.mean(np.square(frame)))))
    return levels


def analyze_audio(
    path: Path,
    audio: np.ndarray,
    *,
    sample_rate: int,
    cue_threshold_db: float = -50.0,
    silence_threshold_db: float = -80.0,
    cue_padding_seconds: float = 0.25,
    analysis_window_seconds: float = 0.10,
) -> TrackAnalysis:
    if audio.shape[0] == 0:
        raise RuntimeError(f"{path.name} decoded to zero samples")
    if silence_threshold_db >= cue_threshold_db:
        raise ValueError("silence_threshold_db must be lower than cue_threshold_db")

    frame_samples = max(1, int(round(sample_rate * analysis_window_seconds)))
    cue_padding_samples = max(0, int(round(sample_rate * cue_padding_seconds)))
    frame_levels = _frame_rms_dbfs(audio, frame_samples)

    cue_first, cue_last = _first_last_true(frame_levels >= cue_threshold_db)
    sound_first, sound_last = _first_last_true(frame_levels >= silence_threshold_db)

    warnings: list[str] = []
    if sound_first is None or sound_last is None:
        warnings.append("no usable audio above silence threshold")
        sound_first = 0
        sound_last = max(0, frame_levels.shape[0] - 1)

    if cue_first is None or cue_last is None:
        warnings.append("no stable active cue above cue threshold")
        cue_first = sound_first
        cue_last = sound_last

    raw_cue_start = min(audio.shape[0], cue_first * frame_samples)
    raw_cue_end = min(audio.shape[0], (cue_last + 1) * frame_samples)
    cue_start = max(0, raw_cue_start - cue_padding_samples)
    cue_end = min(audio.shape[0], raw_cue_end + cue_padding_samples)

    silence_start = min(audio.shape[0], sound_first * frame_samples)
    silence_end = min(audio.shape[0], (sound_last + 1) * frame_samples)

    leading_quiet_seconds = raw_cue_start / sample_rate
    trailing_quiet_seconds = max(0, audio.shape[0] - raw_cue_end) / sample_rate
    leading_silence_seconds = silence_start / sample_rate
    trailing_silence_seconds = max(0, audio.shape[0] - silence_end) / sample_rate

    if leading_silence_seconds >= 1.0:
        warnings.append(f"leading near-silence: {leading_silence_seconds:.2f}s")
    if trailing_silence_seconds >= 1.0:
        warnings.append(f"trailing near-silence: {trailing_silence_seconds:.2f}s")
    if leading_quiet_seconds >= 4.0:
        warnings.append(f"slow or quiet intro before active cue: {leading_quiet_seconds:.2f}s")
    if trailing_quiet_seconds >= 4.0:
        warnings.append(f"quiet tail after active cue: {trailing_quiet_seconds:.2f}s")

    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio.astype(np.float64, copy=False)))))

    return TrackAnalysis(
        source_path=str(path),
        input_samples=int(audio.shape[0]),
        input_seconds=audio.shape[0] / sample_rate,
        max_dbfs=_dbfs(peak),
        rms_dbfs=_dbfs(rms),
        cue_start_sample=int(cue_start),
        cue_end_sample=int(cue_end),
        silence_start_sample=int(silence_start),
        silence_end_sample=int(silence_end),
        leading_quiet_seconds=leading_quiet_seconds,
        trailing_quiet_seconds=trailing_quiet_seconds,
        leading_silence_seconds=leading_silence_seconds,
        trailing_silence_seconds=trailing_silence_seconds,
        active_seconds=max(0, cue_end - cue_start) / sample_rate,
        warnings=warnings,
    )


def _slice_for_policy(
    audio: np.ndarray,
    analysis: TrackAnalysis,
    *,
    track_index: int,
    mix_policy: str,
) -> tuple[np.ndarray, int, int]:
    if mix_policy == "strict":
        return audio, 0, audio.shape[0]

    start = analysis.silence_start_sample if track_index == 1 else analysis.cue_start_sample
    end = analysis.cue_end_sample
    if end <= start:
        raise RuntimeError(
            f"{Path(analysis.source_path).name} has no usable audio after active-cue trimming"
        )
    return audio[start:end], start, end


def mix_tracks(
    track_paths: list[Path],
    output_path: Path,
    *,
    crossfade_seconds: float = 12,
    sample_rate: int = 44_100,
    channels: int = 2,
    bitrate: str = "320k",
    mix_policy: str = "active-cue",
    quality_gate: str = "warn",
    cue_threshold_db: float = -50.0,
    silence_threshold_db: float = -80.0,
    cue_padding_seconds: float = 0.25,
    manifest_path: Path | None = None,
) -> dict:
    if not track_paths:
        raise ValueError("track_paths cannot be empty")
    if mix_policy not in MIX_POLICIES:
        raise ValueError(f"mix_policy must be one of {', '.join(MIX_POLICIES)}")
    if quality_gate not in QUALITY_GATES:
        raise ValueError(f"quality_gate must be one of {', '.join(QUALITY_GATES)}")

    crossfade_samples = int(round(sample_rate * crossfade_seconds))
    if crossfade_samples < 0:
        raise ValueError("crossfade_seconds cannot be negative")

    preflight_analyses: dict[Path, TrackAnalysis] = {}
    if quality_gate == "fail":
        for track in track_paths:
            audio = decode_audio(track, sample_rate, channels)
            analysis = analyze_audio(
                track,
                audio,
                sample_rate=sample_rate,
                cue_threshold_db=cue_threshold_db,
                silence_threshold_db=silence_threshold_db,
                cue_padding_seconds=cue_padding_seconds,
            )
            if mix_policy == "active-cue" and "no usable audio above silence threshold" in analysis.warnings:
                raise RuntimeError(f"{track.name} has no usable audio above silence threshold")
            if analysis.warnings:
                joined = "; ".join(analysis.warnings)
                raise RuntimeError(f"{track.name} failed quality gate: {joined}")
            preflight_analyses[track] = analysis

    temp_output = output_path.with_name(f"{output_path.stem}.tmp{output_path.suffix}")
    if temp_output.exists():
        temp_output.unlink()

    encoder = start_encoder(temp_output, sample_rate, channels, bitrate)
    previous_tail: np.ndarray | None = None
    written_samples = 0
    track_entries: list[dict] = []

    try:
        for index, track in enumerate(track_paths, start=1):
            print(f"[{index:03d}/{len(track_paths):03d}] Mixing {track.name}", flush=True)
            audio = decode_audio(track, sample_rate, channels)
            analysis = preflight_analyses.get(track)
            if analysis is None:
                analysis = analyze_audio(
                    track,
                    audio,
                    sample_rate=sample_rate,
                    cue_threshold_db=cue_threshold_db,
                    silence_threshold_db=silence_threshold_db,
                    cue_padding_seconds=cue_padding_seconds,
                )

            if quality_gate == "warn":
                for warning in analysis.warnings:
                    print(f"[quality] {track.name}: {warning}", flush=True)
            if mix_policy == "active-cue" and "no usable audio above silence threshold" in analysis.warnings:
                raise RuntimeError(f"{track.name} has no usable audio above silence threshold")

            audio, segment_start, segment_end = _slice_for_policy(
                audio,
                analysis,
                track_index=index,
                mix_policy=mix_policy,
            )
            if crossfade_samples and audio.shape[0] <= crossfade_samples:
                raise RuntimeError(f"{track.name} is too short for a {crossfade_seconds}s crossfade")

            if previous_tail is None:
                if crossfade_samples:
                    write_audio(encoder, audio[:-crossfade_samples], sample_rate, channels)
                    written_samples += max(0, audio.shape[0] - crossfade_samples)
                else:
                    write_audio(encoder, audio, sample_rate, channels)
                    written_samples += audio.shape[0]
            else:
                if crossfade_samples:
                    overlap = linear_crossfade(previous_tail, audio[:crossfade_samples])
                    write_audio(encoder, overlap, sample_rate, channels)
                    write_audio(encoder, audio[crossfade_samples:-crossfade_samples], sample_rate, channels)
                    written_samples += overlap.shape[0]
                    written_samples += max(0, audio.shape[0] - (2 * crossfade_samples))
                else:
                    write_audio(encoder, audio, sample_rate, channels)
                    written_samples += audio.shape[0]

            previous_tail = audio[-crossfade_samples:] if crossfade_samples else None
            entry = asdict(analysis)
            entry.update(
                {
                    "used_start_seconds": segment_start / sample_rate,
                    "used_end_seconds": segment_end / sample_rate,
                    "used_seconds": audio.shape[0] / sample_rate,
                    "head_trim_seconds": segment_start / sample_rate,
                    "tail_trim_seconds": max(0, analysis.input_samples - segment_end) / sample_rate,
                }
            )
            track_entries.append(entry)

        if previous_tail is not None:
            write_audio(encoder, previous_tail, sample_rate, channels)
            written_samples += previous_tail.shape[0]

        if encoder.stdin is not None:
            encoder.stdin.close()
        rc = encoder.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg encoder failed with exit code {rc}")

        if output_path.exists():
            output_path.unlink()
        temp_output.replace(output_path)
    except Exception:
        if encoder.poll() is None:
            if encoder.stdin is not None:
                try:
                    encoder.stdin.close()
                except OSError:
                    pass
            encoder.kill()
            encoder.wait()
        if temp_output.exists():
            temp_output.unlink()
        raise

    manifest = {
        "track_count": len(track_paths),
        "crossfade_seconds": crossfade_seconds,
        "sample_rate": sample_rate,
        "channels": channels,
        "bitrate": bitrate,
        "mix_policy": mix_policy,
        "quality_gate": quality_gate,
        "cue_threshold_db": cue_threshold_db,
        "silence_threshold_db": silence_threshold_db,
        "cue_padding_seconds": cue_padding_seconds,
        "output_path": str(output_path),
        "rendered_samples": written_samples,
        "rendered_seconds_estimate": written_samples / sample_rate,
        "tracks": track_entries,
    }
    if manifest_path:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

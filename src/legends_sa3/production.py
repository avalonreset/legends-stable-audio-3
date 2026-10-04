"""Full-song planning and explicit, per-transition arrangement rendering."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import uuid
from pathlib import Path

import numpy as np

from .mixer import decode_audio, write_audio


def _number(value: object, name: str, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return float(value)


def plan_production(
    *, minutes: float, song_seconds: float = 380, overlap_estimate: float = 12,
    runtime_intent: str = "approximate", credits_per_job: float = 26,
) -> dict:
    """Overlap is a count estimate, never an instruction to trim to a clock."""
    target = _number(minutes, "minutes", 0.01) * 60
    duration = _number(song_seconds, "song_seconds", 1)
    overlap = _number(overlap_estimate, "overlap_estimate")
    cost = _number(credits_per_job, "credits_per_job")
    if duration > 380 or overlap >= duration:
        raise ValueError("song_seconds must be <= 380 and overlap must be shorter")
    if runtime_intent not in ("approximate", "minimum", "exact"):
        raise ValueError("runtime_intent must be approximate, minimum or exact")
    count = max(1, math.ceil((target - overlap) / (duration - overlap)))
    return {
        "schema_version": 1, "surface": "hosted-large", "model": "stable-audio-3",
        "role": "full-song", "song_seconds": duration, "song_count": count,
        "target_seconds": target, "runtime_intent": runtime_intent,
        "overlap_estimate_seconds": overlap,
        "estimated_mix_seconds": count * duration - (count - 1) * overlap,
        "estimated_credits": count * cost,
        "pricing_status": "reference only; verify live price before spending",
        "duration_reason": "maximize usable music per flat-rate generation",
        "trim_to_target": False,
        "exact_edit_required": runtime_intent == "exact",
        "next": "generate one full-length candidate; assess before expanding",
        "transition_policy": "choose and record each pair's musical cues after generation",
    }


def validate_arrangement(document: dict, durations: list[float]) -> list[dict]:
    """Reject hidden trims, unpromoted discoveries and colliding overlaps."""
    tracks = document.get("tracks", [])
    joins = document.get("transitions", [])
    if not tracks or len(tracks) != len(durations) or len(joins) != len(tracks) - 1:
        raise ValueError("provide tracks and exactly one transition per adjacent pair")
    intent = document.get("runtime_intent", "approximate")
    if intent not in ("approximate", "minimum", "exact"):
        raise ValueError("invalid runtime_intent")
    cuts = []
    for track, duration in zip(tracks, durations):
        start = _number(track.get("in_seconds", 0), "in_seconds")
        end = _number(track.get("out_seconds", duration), "out_seconds")
        if not start < end <= duration + 1e-6:
            raise ValueError("source cues must satisfy 0 <= in < out <= duration")
        trimmed = start > 0 or end < duration - 1e-6
        if trimmed and not str(track.get("trim_reason", "")).strip():
            raise ValueError("every source trim needs a trim_reason")
        if track.get("stage") == "discovery" and not track.get("promotion_reason"):
            raise ValueError("discovery source needs an explicit promotion_reason")
        if not track.get("selection_reason"):
            raise ValueError("every source needs a selection_reason")
        cuts.append({"in_seconds": start, "out_seconds": end, "seconds": end-start})
    for index, join in enumerate(joins):
        overlap = _number(join.get("seconds"), "transition seconds")
        if not join.get("reason"):
            raise ValueError("every transition needs a cue reason")
        if join.get("curve", "equal-power") not in ("linear", "equal-power"):
            raise ValueError("curve must be linear or equal-power")
        for name in ("fade_in_seconds", "fade_out_seconds"):
            if name in join and not 0 < _number(join[name], name) <= overlap:
                raise ValueError(f"{name} must be positive and within the overlap")
        if overlap >= min(cuts[index]["seconds"], cuts[index+1]["seconds"]):
            raise ValueError("transition must be shorter than both adjacent sources")
    for index, cut in enumerate(cuts):
        incoming = joins[index-1]["seconds"] if index else 0
        outgoing = joins[index]["seconds"] if index < len(joins) else 0
        if incoming + outgoing >= cut["seconds"]:
            raise ValueError("incoming and outgoing transitions overlap within a song")
    return cuts


def blend(
    outgoing: np.ndarray, incoming: np.ndarray, curve: str,
    *, fade_in_samples: int | None = None, fade_out_samples: int | None = None,
) -> np.ndarray:
    if outgoing.shape != incoming.shape:
        raise ValueError("crossfade buffers must have equal shape")
    count = len(outgoing)
    ins = count if fade_in_samples is None else fade_in_samples
    outs = count if fade_out_samples is None else fade_out_samples
    if not 1 <= ins <= count or not 1 <= outs <= count:
        raise ValueError("fade lengths must fit overlap buffers")
    phase_in = np.ones((count, 1), dtype=np.float32)
    phase_out = np.zeros((count, 1), dtype=np.float32)
    phase_in[:ins, 0] = np.linspace(0, 1, ins, dtype=np.float32)
    phase_out[-outs:, 0] = np.linspace(0, 1, outs, dtype=np.float32)
    if curve == "equal-power":
        return outgoing * np.cos(phase_out*np.pi/2) + incoming * np.sin(phase_in*np.pi/2)
    if curve == "linear":
        return outgoing * (1-phase_out) + incoming * phase_in
    raise ValueError("unknown curve")


def render_arrangement(document: dict, output: Path, *, base: Path, rate: int = 44100) -> dict:
    """Stream explicit pairwise fades to float WAV; master/encode afterward.

    This renderer never optimizes to a target duration, guesses musical review,
    applies global fades, or silently clips overlapping audio.
    """
    if output.suffix.lower() != ".wav":
        raise ValueError("arrange renders WAV; master and encode delivery formats afterward")
    manifest_path = output.with_suffix(".arrangement.json")
    if output.exists() or manifest_path.exists():
        raise FileExistsError("output or arrangement receipt already exists")
    paths = [(base / t["source"]).resolve() for t in document["tracks"]]
    durations = [len(decode_audio(p, rate, 2))/rate for p in paths]
    cuts = validate_arrangement(document, durations)
    joins = document.get("transitions", [])
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f"{output.stem}.{uuid.uuid4().hex}.tmp.wav")
    encoder = subprocess.Popen([
        "ffmpeg", "-v", "error", "-nostdin", "-f", "f32le", "-ar", str(rate),
        "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", str(temporary),
    ], stdin=subprocess.PIPE)
    tail = None
    count = 0
    peak = 0.0
    entries = []
    transition_entries = []

    def write(data: np.ndarray) -> None:
        nonlocal count, peak
        if data.size:
            peak = max(peak, float(np.max(np.abs(data))))
            write_audio(encoder, data, rate, 2)
            count += len(data)

    try:
        for index, (path, cut) in enumerate(zip(paths, cuts)):
            data = decode_audio(path, rate, 2)
            begin, end = round(cut["in_seconds"]*rate), round(cut["out_seconds"]*rate)
            data = data[begin:end]
            incoming = round(joins[index-1]["seconds"]*rate) if index else 0
            outgoing = round(joins[index]["seconds"]*rate) if index < len(joins) else 0
            start = count/rate
            if incoming:
                join = joins[index-1]
                write(blend(
                    tail, data[:incoming], join.get("curve", "equal-power"),
                    fade_in_samples=max(1, round(join.get("fade_in_seconds", incoming/rate)*rate)),
                    fade_out_samples=max(1, round(join.get("fade_out_seconds", incoming/rate)*rate)),
                ))
            if index:
                join = joins[index-1]
                transition_entries.append({
                    **join, "mix_start_seconds": start, "mix_end_seconds": count/rate,
                    "outgoing_source_start_seconds": cuts[index-1]["out_seconds"]-incoming/rate,
                    "incoming_source_start_seconds": begin/rate,
                })
            stop = len(data)-outgoing
            write(data[incoming:stop])
            tail = data[stop:] if outgoing else None
            entries.append({
                **document["tracks"][index], **cut, "mix_start_seconds": start,
                "head_trim_seconds": begin/rate,
                "tail_trim_seconds": durations[index]-end/rate,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError("arrangement encoder failed")
        temporary.replace(output)
    except BaseException:
        if encoder.poll() is None:
            encoder.kill()
            encoder.wait()
        temporary.unlink(missing_ok=True)
        raise
    receipt = {
        "schema_version": 1, "tracks": entries, "transitions": transition_entries,
        "sample_rate": rate, "rendered_samples": count, "rendered_seconds": count/rate,
        "runtime_intent": document.get("runtime_intent", "approximate"),
        "trim_to_target": False, "sample_peak": peak,
        "needs_mastering": True,
        "listening_review": document.get("listening_review", "unreviewed"),
    }
    manifest_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt

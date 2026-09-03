from __future__ import annotations

from dataclasses import dataclass
from math import ceil


DEFAULT_MODEL_MAX_SECONDS = 380


@dataclass(frozen=True)
class MixPlan:
    target_seconds: int
    track_seconds: int
    crossfade_seconds: int
    track_count: int
    final_seconds: int

    @property
    def final_hours(self) -> float:
        return self.final_seconds / 3600


def recommend_track_seconds(vram_gb: float | None, model_max_seconds: int = DEFAULT_MODEL_MAX_SECONDS) -> int:
    """Return a conservative segment length for Stable Audio 3 Medium."""
    if vram_gb is None:
        return min(180, model_max_seconds)
    if vram_gb >= 23.5:
        return min(380, model_max_seconds)
    if vram_gb >= 20:
        return min(300, model_max_seconds)
    if vram_gb >= 16:
        return min(240, model_max_seconds)
    if vram_gb >= 12:
        return min(180, model_max_seconds)
    if vram_gb >= 8:
        return min(120, model_max_seconds)
    return min(75, model_max_seconds)


def build_mix_plan(
    *,
    hours: float | None = None,
    minutes: float | None = None,
    target_seconds: int | None = None,
    track_seconds: int,
    crossfade_seconds: int,
) -> MixPlan:
    if target_seconds is None:
        if hours is not None:
            target_seconds = int(round(hours * 3600))
        elif minutes is not None:
            target_seconds = int(round(minutes * 60))
        else:
            raise ValueError("Provide hours, minutes, or target_seconds")

    if track_seconds <= 0:
        raise ValueError("track_seconds must be positive")
    if crossfade_seconds < 0:
        raise ValueError("crossfade_seconds cannot be negative")
    if crossfade_seconds >= track_seconds:
        raise ValueError("crossfade_seconds must be shorter than track_seconds")

    if target_seconds <= track_seconds:
        track_count = 1
    else:
        track_count = ceil((target_seconds - crossfade_seconds) / (track_seconds - crossfade_seconds))

    final_seconds = track_count * track_seconds - max(0, track_count - 1) * crossfade_seconds
    return MixPlan(
        target_seconds=target_seconds,
        track_seconds=track_seconds,
        crossfade_seconds=crossfade_seconds,
        track_count=track_count,
        final_seconds=final_seconds,
    )

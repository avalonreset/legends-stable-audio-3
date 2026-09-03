from __future__ import annotations

import re
from dataclasses import dataclass

NEGATIVE_PROMPT_GENERAL = (
    "poor quality, clipping, harsh distortion, sudden genre switch, "
    "jarring transition, distorted master"
)

NEGATIVE_PROMPT_INSTRUMENTAL = (
    "vocals, singing, rapping, spoken words, speech, crowd noise, "
    "harsh distortion, clipping, sudden genre switch, jarring transition"
)


@dataclass(frozen=True)
class GenrePreset:
    name: str
    base_style: str
    moods: tuple[str, ...]
    instruments: tuple[str, ...]
    drums: tuple[str, ...]
    bass: tuple[str, ...]
    colors: tuple[str, ...]
    bpm_cycle: tuple[int, ...]


LOFI_STUDY = GenrePreset(
    name="lofi-study",
    base_style=(
        "Instrumental lo-fi chill hip hop study music, calm background music for deep work, "
        "dusty vinyl texture, warm tape saturation, smooth long-form arrangement, no vocals"
    ),
    moods=(
        "rain on window ambience",
        "quiet library atmosphere",
        "blue-hour bedroom studio mood",
        "soft coffee shop room tone",
        "night bus through wet streets",
        "amber desk lamp mood",
        "snowy window ambience",
        "midnight sampler mood",
        "green banker lamp mood",
        "early dawn room tone",
        "empty campus hallway at night",
        "foggy city balcony mood",
        "late train home ambience",
        "dim archive room mood",
        "after-hours bookstore mood",
        "warm basement studio mood",
    ),
    instruments=(
        "warm Rhodes electric piano",
        "muted jazz guitar phrases",
        "mellow Wurlitzer keys",
        "soft felt piano chords",
        "warm organ chords",
        "hazy analog pad and sparse electric piano",
        "chopped warm keyboard samples",
        "mellow Rhodes chords with muted guitar answers",
    ),
    drums=(
        "soft boom bap drums",
        "laid-back boom bap groove",
        "dusty sampled drum loop",
        "brushed snare and soft kick",
        "restrained drum loop",
        "gentle shuffled hats and warm snare",
        "low-key head-nod rhythm",
        "soft kick and snare with quiet vinyl crackle",
    ),
    bass=(
        "mellow rounded bass",
        "warm upright bass",
        "deep smooth bassline",
        "smooth bass guitar",
        "rounded sub bass",
        "soft dub bass pulses",
    ),
    colors=(
        "subtle jazz harmony",
        "understated melodic motif",
        "relaxed head-nod rhythm",
        "peaceful non-distracting groove",
        "cohesive study-session flow",
        "low-key melodic movement",
        "warm final-track glow",
        "gentle sleepy rhythm",
    ),
    bpm_cycle=(74, 76, 78, 80, 82, 84, 79, 81, 75, 83),
)


TRIP_HOP_TRANCE = GenrePreset(
    name="trip-hop-trance",
    base_style=(
        "Instrumental trip hop trance, gritty downtempo breakbeat groove with "
        "hypnotic trance synthesis, forward momentum, dark cinematic club energy, "
        "arpeggiated synth patterns, deep bass pressure, no vocals"
    ),
    moods=(
        "warehouse after-midnight energy",
        "neon tunnel momentum",
        "rainy industrial skyline tension",
        "underground club sound system pressure",
        "late-night highway hypnosis",
        "strobe-lit back room atmosphere",
        "dark city overpass motion",
        "magnetic trance floor pull",
        "blue laser haze",
        "afterhours concrete room tone",
    ),
    instruments=(
        "acid arpeggiated synth line",
        "gated supersaw pad swells",
        "dark plucked synth ostinato",
        "filtered trance lead motif",
        "granular vocal-like synth texture without words",
        "metallic delay stabs",
        "pulsing analog sequence",
        "wide resonant pad and sharp arps",
    ),
    drums=(
        "punchy trip hop breakbeat",
        "driving broken beat kick and snare",
        "syncopated breakbeat drums with open hats",
        "heavy half-time breakbeat with trance pulse",
        "dusty but forceful sampled drums",
        "tight kick, cracking snare, rolling percussion",
    ),
    bass=(
        "deep rolling sub bass",
        "rubbery acid bassline",
        "dark Reese bass movement",
        "tight pulsing bass sequence",
        "distilled dub sub pressure",
        "saw bass pulses locked to the arpeggio",
    ),
    colors=(
        "minor key tension",
        "hypnotic build without a vocal hook",
        "more trance floor than lounge",
        "psychedelic arpeggio drift",
        "forward-driving nocturnal groove",
        "cinematic pressure and release",
        "cohesive dark melodic momentum",
    ),
    bpm_cycle=(96, 100, 104, 108, 112, 118, 102, 106, 110, 114),
)


PRESETS = {
    LOFI_STUDY.name: LOFI_STUDY,
    TRIP_HOP_TRANCE.name: TRIP_HOP_TRANCE,
}

DEFAULT_BPM_CYCLE = (84, 88, 92, 96, 100, 104, 108, 112)

FREEFORM_ARRANGEMENTS = (
    "cohesive full-track arrangement with a clear intro, evolving middle, and natural outro",
    "steady musical development with subtle variation every section",
    "consistent groove and arrangement that stays in the requested style",
    "song-form structure with recurring themes and no abrupt genre switch",
    "polished arrangement that feels like one finished cue",
    "smooth section changes with musical continuity",
)

FREEFORM_PRODUCTION = (
    "clean 44.1 kHz stereo production",
    "balanced mix with controlled low end and clear transients",
    "wide stereo image with tasteful ambience",
    "warm polished master with no clipping",
    "detailed production texture without harsh high frequencies",
    "stable rhythm bed with musical headroom",
)

FREEFORM_COLOR = (
    "memorable central motif",
    "strong rhythmic identity",
    "tasteful harmonic movement",
    "clear instrumental focus",
    "cinematic movement without overproduction",
    "musical phrasing with coherent energy",
)


def list_presets() -> list[str]:
    return sorted(PRESETS)


def extract_bpm(style: str) -> int | None:
    match = re.search(r"\b([4-9]\d|1[0-9]{2}|2[0-2]\d)\s*bpm\b", style, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _has_tag(style: str, tag: str) -> bool:
    return f"{tag.lower()}:" in style.lower()


def is_sfx_style(style: str | None) -> bool:
    if not style:
        return False
    return bool(re.search(r"\bTrackType\s*:\s*(?:SFX|Sound Effect)\b", style, flags=re.IGNORECASE))


def _normalize_track_type(style: str) -> str:
    return re.sub(
        r"\bTrackType\s*:\s*Sound Effect\b",
        "TrackType: SFX",
        style,
        flags=re.IGNORECASE,
    )


def _style_with_routing_tags(style: str, *, instrumental: bool) -> str:
    """Add optional wrapper routing tags while preserving explicit user tags."""
    style = _normalize_track_type(style)
    parts: list[str] = []
    if not _has_tag(style, "TrackType"):
        parts.append("TrackType: Music")
    if instrumental and not is_sfx_style(style) and not _has_tag(style, "VocalType"):
        parts.append("VocalType: Instrumental")
    parts.append(style.strip().strip("., "))
    return ", ".join(part for part in parts if part)


def _bpm_from_cycle(index: int, bpm_cycle: tuple[int, ...], bpm: int | None) -> int:
    if bpm is not None:
        return bpm
    return bpm_cycle[(index - 1) % len(bpm_cycle)]


def slugify_style(label: str, *, fallback: str = "custom-style") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return slug[:64].strip("-") or fallback


def build_freeform_prompt(
    style: str,
    index: int,
    *,
    bpm: int | None = None,
    instrumental: bool = True,
    omit_bpm: bool = False,
) -> tuple[str, int | None]:
    if not style or not style.strip():
        raise ValueError("style cannot be empty")
    clean_style = style.strip().rstrip("., ")
    detected_bpm = extract_bpm(clean_style)
    suppress_automatic_bpm = omit_bpm or is_sfx_style(clean_style)
    chosen_bpm = bpm if bpm is not None else detected_bpm
    if chosen_bpm is None and not suppress_automatic_bpm:
        chosen_bpm = _bpm_from_cycle(index, DEFAULT_BPM_CYCLE, None)
    tagged_style = _style_with_routing_tags(clean_style, instrumental=instrumental)
    if detected_bpm is not None:
        return tagged_style, chosen_bpm
    if chosen_bpm is None:
        return tagged_style, None
    return f"{tagged_style}, {chosen_bpm} BPM", chosen_bpm


def build_recipe_prompt(
    recipe: str,
    index: int,
    *,
    custom_style: str | None = None,
    bpm: int | None = None,
    instrumental: bool = True,
    omit_bpm: bool = False,
) -> tuple[str, int | None]:
    preset = PRESETS[recipe]
    chosen_bpm = None if omit_bpm and bpm is None else _bpm_from_cycle(index, preset.bpm_cycle, bpm)
    base = custom_style if custom_style else preset.base_style
    base = _style_with_routing_tags(base, instrumental=instrumental)
    bpm_clause = f", {chosen_bpm} BPM" if chosen_bpm is not None else ""
    prompt = (
        f"{base}{bpm_clause}, "
        f"{preset.instruments[(index * 3 - 3) % len(preset.instruments)]}, "
        f"{preset.drums[(index * 5 - 5) % len(preset.drums)]}, "
        f"{preset.bass[(index * 7 - 7) % len(preset.bass)]}, "
        f"{preset.moods[(index - 1) % len(preset.moods)]}, "
        f"{preset.colors[(index * 11 - 11) % len(preset.colors)]}"
    )
    return prompt, chosen_bpm


def build_prompt(
    recipe: str | None,
    index: int,
    *,
    style: str | None = None,
    custom_style: str | None = None,
    bpm: int | None = None,
    instrumental: bool = True,
    omit_bpm: bool = False,
) -> tuple[str, int | None]:
    if style:
        return build_freeform_prompt(
            style,
            index,
            bpm=bpm,
            instrumental=instrumental,
            omit_bpm=omit_bpm,
        )
    recipe_name = recipe or LOFI_STUDY.name
    return build_recipe_prompt(
        recipe_name,
        index,
        custom_style=custom_style,
        bpm=bpm,
        instrumental=instrumental,
        omit_bpm=omit_bpm,
    )

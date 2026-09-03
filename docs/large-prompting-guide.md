# Stable Audio 3 Large Prompting and Duration Guide

Use this guide for hosted Stable Audio 3 Large through the Stability Platform
REST model ID `stable-audio-3`. Keep it separate from local Medium controls and
from the Stable Audio web studio.

## Evidence-backed defaults

- Instrumental prefix: `TrackType: Music, VocalType: Instrumental,`
- Steps: `8`
- CFG: `1.0`
- Output: native WAV
- Complete-song quality band: `120-190s`
- API maximum: `380s`

The Stable Audio 3 technical report evaluates Large at `20`, `120`, `190`, and
`380` seconds. It reports the strongest performance at intermediate lengths,
typically `120-190s`. At `380s`, prompt alignment degrades and the model can
drift toward ambient or classical material because those genres dominate the
longest training examples.

Duration is a model conditioning signal, not an export crop. Always choose it
deliberately. Omitting `duration` selects the API's fixed `190s` default; it is
not an adaptive `AUTO` mode.

## Organic duration ranges

| Family | Starting range |
|---|---:|
| Digital hardcore, dense DnB | `120-160s` |
| Breakbeat, big beat, acid industrial | `135-180s` |
| Trip-hop, downtempo breakbeat | `150-190s` |
| Goa, psytrance, progressive trance | `165-210s` |
| Minimal psytrance, dark/ambient dub, cinematic electronic | `180-240s` |
| Ambient, drone, classical, slow soundscape | `210-320s` |

These are house hypotheses derived from the official duration evidence, not a
published Stability genre table. Refine them with blind duration tournaments.

## Duration tournament

1. Generate at least three `120s` discovery seeds per prompt family.
2. Promote the winning family into its genre range.
3. Keep prompt, BPM, and settings fixed while testing three nearby durations.
   Repeat the same set of at least three requested seeds at every duration so
   one lucky or unlucky seed cannot decide the policy.
4. Select the shortest range that consistently creates a complete arc.
5. Move upward only when added time produces musical development. Move downward
   when added time produces repetition, blandness, dead air, or prompt drift.

Do not use `20-60s` full-song canaries as the Large default. The technical
report found degradation at very short lengths because short training examples
were mostly loops rather than complete songs. Verify current Platform pricing
before spending; do not assume a shorter request saves credits.

## Prompt shape

```text
TrackType: Music, VocalType: Instrumental, Genre: [primary], Genre: [secondary],
[exact BPM] BPM, Instruments: [main instruments], [rhythm and performance],
[mood and energy], [arrangement development], [production character],
[role in the production]
```

Large uses the Stable Audio 3 family prompt grammar. It does not expose a
negative-prompt field. Prefer positive format, instrumentation, arrangement,
and production instructions. Use explicit development language rather than a
rigid bracketed timeline.

## Fourteen-minute soundtrack default

For a `14:09.452` program, begin with either:

- five sources around `175-190s`; or
- six sources around `145-170s`.

Use denser genres toward the shorter/more-sources side and spacious genres
toward the longer/fewer-sources side. Generate enough source headroom for phrase
selection and overlaps. Choose transitions after tempo and phrase analysis;
Stable Audio publishes no official crossfade duration.

The prior three-source `300s` calibration remains valid evidence but is not the
default production formula.

## Primary sources

- Technical report: `https://arxiv.org/html/2605.17991`
- Official Stable Audio 3 prompt guide:
  `https://stability.ai/guides/stable-audio-3-prompt-guide`
- Platform API reference: `https://platform.stability.ai/docs/api-reference`

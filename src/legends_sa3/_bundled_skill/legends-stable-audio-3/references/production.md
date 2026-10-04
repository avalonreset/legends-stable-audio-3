# Hosted Large: full songs first

For full songs and continuous music sets, request **380 seconds per song**.
The Legends CLI sends this duration explicitly. The upstream API's omitted-field
default remains 190 seconds. Set `--duration` deliberately for short cues,
loops, SFX, or an explicit user override.

At the Platform price verified on 2026-10-04, each successful generation costs
26 credits regardless of duration. Optimize usable music per paid job. Short
trials do not save credits under flat-rate pricing. Verify current pricing
before execution; the planner's cost is a reference estimate.

## Calibrate the arrangement at production length

1. Extract the musical role, desired character and arrangement from the brief.
   "For a video" does not imply sparse music, shortened songs or a hard runtime.
2. Generate one full-length 380-second candidate with 8 steps, CFG 1 and WAV
   output. Describe development, a breakdown, a varied return and an ending.
3. Check the whole recording for rhythm continuity, genre drift, repetition,
   musical development, ending quality, unwanted vocals and artifacts.
   Separate listening observations from signal measurements. Record absent
   listening review as unreviewed, never as a creative-quality pass.
4. Expand a successful direction into a small set of full-length variations.
   Reuse accepted calibration recordings as production sources. Preserve all
   originals and generation IDs; recover submitted jobs instead of paying twice.
5. If a long candidate fails, revise the prompt or seed before automatically
   shortening everything. A shorter comparison is justified by documented
   quality problems or an explicit brief. For comparisons, hold other settings
   fixed and compare multiple requested seeds if results are uncertain.

Discovery files are a separate role. They cannot silently fill a production
set. The arrangement validator requires a promotion reason for discoveries.
Longer is a value-oriented starting policy, not a guarantee of better music.

The official technical report evaluates Large at 20, 120, 190 and 380 seconds.
Aggregate prompt alignment falls at 380 seconds, with reported ambient/classical
bias. This is a risk to evaluate. It does not establish preferred D&B song
lengths or justify treating all dense genres as two-minute songs. Local GPU
memory recommendations do not constrain hosted Large.

## Plan songs independently of the final runtime

```sh
legends-sa3 production-plan --minutes 20
```

This plans four 380-second songs. The printed 12-second overlap is only a
count estimate. The actual set duration follows the chosen sources and
individual musical transitions; there is no automatic trim to 20 minutes.

Approximate is the default. `--runtime-intent minimum` plans sufficient sources.
`--runtime-intent exact` explicitly records the need for a separate final edit;
it does not secretly crop the arrangement. A genuinely exact deliverable must
be edited and verified as a separate requested output.

## Choose transitions from the recordings

Use [the arrangement workflow](#arrange-full-songs-with-individual-transitions) to record separate cue times,
overlap lengths, curves and reasons for each pair. Keep complete arrangements
by default. Trim only for a stated musical or explicit editorial reason.
Beat estimates alone are not phrase detection. Energy thresholds alone cannot
distinguish a slow introduction from unwanted silence.

There is no universal crossfade duration. Preserve the first opening and final
ending. Master the assembled float WAV, check peaks and loudness, and export
lossless and listening formats. Preserve raw and standalone tracks separately.

## Prompt shape

```text
TrackType: Music, VocalType: Instrumental, Genre: [genre], [BPM] BPM,
[instruments], [groove], [mood], full-length extended instrumental composition.
[Developed introduction, sustained groove, evolving themes, breakdown,
varied return, and musical ending]. [Production character].
```

This is descriptive conditioning, not a guarantee of timed sections.
Large has no exposed negative-prompt field.

## Sources checked 2026-10-04

- https://platform.stability.ai/docs/api-reference
- https://platform.stability.ai/pricing
- https://arxiv.org/html/2605.17991
- https://stability.ai/guides/stable-audio-3-prompt-guide


# Arrange full songs with individual transitions

`production-plan` estimates how many full-length hosted songs to generate.
`arrange` renders a reviewed or explicitly unreviewed cue sheet without a
runtime target. It writes float WAV to preserve overlap headroom; normalize
or master afterward before exporting PCM/MP3. It does not automatically
listen, detect phrases, beat-match, or establish musical quality.

Paths below resolve relative to the JSON plan file.

```json
{
  "runtime_intent": "approximate",
  "listening_review": "unreviewed; signal-assisted candidate cues",
  "tracks": [
    {
      "source": "first.wav",
      "stage": "production",
      "selection_reason": "Full-length candidate matching the production brief"
    },
    {
      "source": "second.wav",
      "stage": "production",
      "selection_reason": "Companion full-length candidate"
    }
  ],
  "transitions": [
    {
      "seconds": 9.5,
      "curve": "equal-power",
      "reason": "Illustrative only: replace with this pair's measured/reviewed outro cue"
    }
  ]
}
```

```sh
legends-sa3 arrange --plan arrangement.json --output arrangement-float.wav
```

Omitted `in_seconds` and `out_seconds` preserve the entire source. If either
omits material, `trim_reason` is required. A `stage: discovery` source requires
an explicit `promotion_reason`. Every source needs `selection_reason`; every
transition needs `reason`. Available curves are `linear` and `equal-power`.
Use linear where correlated material makes equal-power gain undesirable.
Optional `fade_in_seconds` and `fade_out_seconds` must be positive and fit
inside the overlap. The incoming fade begins at the overlap start; the outgoing
fade ends at the overlap end. For a naturally decaying outro, a short incoming
fade can preserve the next introduction while the outgoing tail decays at
unity until its own final fade. The default fades span the full overlap.

Each overlap starts at the outgoing selected endpoint minus its duration and
at the incoming selected start. The receipt records both source cues and
sample-derived mix timestamps. Zero overlap is allowed for an intentional
butt join. Incoming and outgoing fades cannot collide within one song.

The renderer preserves source boundaries and applies no global fade. It
protects existing outputs, reports peak headroom without clipping, and writes
`<output>.arrangement.json` with source hashes, all trims, individual joins and
review status. An unreviewed render is a deliverable candidate, not a passed
creative calibration.

For rhythmic music, inspect the outro and intro, phrase changes, competing
bass lines and drum alignment. A fixed eight-bar fade across every pair is
not a substitute for these decisions. If beat estimates are unreliable,
choose a sparse ending-to-opening handoff instead of forcing a beat match.

For an approximate set length, preserve musical development and report the
actual duration. Do not shorten song bodies to land on a round number.
Exact-duration versions require an explicit request and a separate edit.

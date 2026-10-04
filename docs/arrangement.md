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

# Continuous mix workflow

Stable Audio 3 Medium cannot create a multi-hour file in a single generation.
This workflow creates long continuous audio by producing many separate tracks in
a coherent style, then crossfading them into one master MP3.

## Why this works

Stable Audio 3 Medium has a practical single-shot ceiling around 380 seconds.
Instead of pretending that limit does not exist, the operator creates many
cohesive tracks with varied seeds, moods, instruments, drums, bass, and BPM.

This is one workflow, not the whole product. The same operator can also help
with one-off generations, prompt shaping, recipe selection, model access, VRAM
planning, and troubleshooting.

## Default long-mix formula

- Prompt style: free-form `--style`, or optional `--recipe`
- Negative prompt: vocals, lyrics, harsh distortion, clipping, jarring transitions
- Segment length on 24 GB VRAM: `380s`
- Crossfade: `12s`
- Mix policy: `active-cue`
- MP3 bitrate: `320k`
- Steps: `12`
- CFG scale: `1.0`

## Commands

Plan:

```powershell
legends-sa3 plan --hours 10 --vram-gb 24 --crossfade 12
```

Generate and mix:

```powershell
legends-sa3 generate `
  --model-dir .\models\stable-audio-3-medium `
  --stable-audio-repo ..\stable-audio-3 `
  --style "lo-fi study hip hop, warm Rhodes, soft boom bap drums, no vocals" `
  --hours 10 `
  --vram-gb 24 `
  --output .\output\lofi-study-10h
```

Preview prompts first:

```powershell
legends-sa3 prompt `
  --style "lo-fi study hip hop, warm Rhodes, soft boom bap drums, no vocals" `
  --count 3
```

Analyze source tracks before mixing:

```powershell
legends-sa3 analyze `
  --input-dir .\output\lofi-study-10h\tracks_mp3 `
  --json-output .\output\lofi-study-10h\track-analysis.json
```

Mix existing tracks:

```powershell
legends-sa3 mix `
  --input-dir .\output\lofi-study-10h\tracks_mp3 `
  --output .\output\lofi-study-10h\master.mp3 `
  --crossfade 12 `
  --mix-policy active-cue
```

## Resumability

The generator skips existing MP3 tracks that are already present and larger than
1 MB. If a run stops after track 61, rerun the same command and it should continue
from the missing tracks.

## Mixing implementation

The mixer streams one source track at a time into the MP3 encoder and keeps only
the current overlap in memory. This avoids ffmpeg memory failures from very large
multi-input `acrossfade` filter graphs.

The default `active-cue` policy runs cue analysis before rendering. It trims
generated near-silent dead air, trims quiet tails that would waste the overlap
window, starts incoming tracks at a usable cue point, and keeps the first and
last track free of global fade-in/fade-out processing. The manifest records the
trim points, cue warnings, and final render estimate.

Run `legends-sa3 analyze` when you want to inspect those cue warnings before the
mix stage. Run `legends-sa3 mix --quality-gate fail` when warnings should stop
the render.

Planner durations are pre-trim estimates. The final active-cue master can be
shorter if generated tracks contain quiet heads or tails.

For exact raw-boundary behavior, use:

```powershell
legends-sa3 mix `
  --input-dir .\output\lofi-study-10h\tracks_mp3 `
  --output .\output\lofi-study-10h\strict-master.mp3 `
  --crossfade 12 `
  --mix-policy strict
```

# Mixing and adapters

## Long-form assembly

Preserve generated source tracks. Analyze cue boundaries before assembling a
long program. The default `active-cue` policy removes near-silent heads and
quiet tails that waste overlap time and starts incoming tracks at usable cues.
Use `strict` when exact raw boundaries are part of the experiment.

Choose transition length by listening in musical bars and phrase boundaries.
Twelve seconds is a proven Legends local option, not a Stability standard or a
universal creative default. Tempo-align when double kicks or phase collisions
occur. Do not add a global fade-in or fade-out unless the brief requests one.

For very long output, use streaming crossfade assembly. A single all-input
ffmpeg `acrossfade` graph can exhaust memory. Verify final duration, sample rate,
channels, codec, loudness/true peak when relevant, gaps, transition energy, and
output hash.

The historical 24 GB throughput proof was 98 sources at 380 seconds with
12-second overlaps, yielding 36,076 seconds (about 10:01:16) as stereo 44.1 kHz
320 kbps MP3. This proves capacity and resumable assembly; it does not prescribe
ordinary source duration or transition length.

## Adapter escalation

Escalate to a LoRA or DoRA only after a repeatable prompt gap survives multiple
prompt families and seeds. Use a clean, rights-cleared, stylistically coherent
dataset and keep datasets and checkpoints outside the source repository.

`--lora-ckpt-path` accepts native Stable Audio 3 LoRA/DoRA `.safetensors`
checkpoints supported by the official runtime. Repeat the flag for multiple
native adapters. Use `--lora-strength` only with at least one adapter path.
PEFT-layout adapters require a separate integration and are not silently
compatible.

Evaluate an adapter with the same prompt, requested seed, duration, steps, and
CFG both with and without the adapter. Judge source tracks before final mixing
so downstream edits do not hide the adapter effect. Record adapter identity and
hash privately when licensing permits; never package the weight in this skill.

The optional Underfit LoRA Studio bridge uses separately licensed MIT code
pinned to a reviewed immutable commit. Verify origin, commit, required files,
and license hash before executing downloaded scripts. Its model packs, datasets,
and generated checkpoints remain separately licensed and outside git.


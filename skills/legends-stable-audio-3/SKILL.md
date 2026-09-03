---
name: legends-stable-audio-3
description: Operate and troubleshoot Stable Audio 3 across local Medium, hosted Large, and web-studio workflows. Use for gated model setup, prompt and seed planning, VRAM-aware generation, native LoRA or DoRA adapters, evidence-backed benchmarks, resumable batches, and long-form crossfaded mixes.
---

# legends-stable-audio-3

Use the repository CLI for local Medium operations and keep hosted Large, the
web studio, and downstream mixing visibly separate in plans and receipts.

## Boundaries

- Project-owned source code, documentation, tests, and designated assets are
  licensed under Apache License 2.0. Read
  [Licensing and dependencies](references/licensing-and-dependencies.md) before
  redistribution.
- Treat Legends Stable Audio 3 as an independent compatibility project. Do not
  claim affiliation with, sponsorship by, or endorsement from Stability AI.
- Treat model weights, hosted services, gated terms, datasets, adapters,
  generated media, and third-party components as separately licensed. Never use
  those dependency terms to reclassify the project-owned source as proprietary.
- Never package, mirror, copy, or commit model weights.
- Never package, mirror, copy, or commit adapter weights.
- Never package secrets, private generated media, local state, or private
  organization paths and content.
- Never bypass model approval. The user must accept gated Hugging Face terms.
- The skill, hosted client, planning, and FFmpeg workflows are cross-platform.
  Local Medium uses CUDA when available and otherwise falls back to CPU; do not
  claim Apple MPS acceleration or practical Mac-local generation without a
  separately proven runtime.
- Confirm before any paid API or web-studio generation. Identify the credit pool
  and current cost from live product evidence rather than memory.
- Native Stable Audio 3 LoRA or DoRA adapters can be loaded with
  `--lora-ckpt-path`; PEFT-style adapters need a separate integration path.
- The optional Underfit LoRA Studio is MIT-licensed code and can be installed
  locally with `legends-sa3 lora-studio`; model weights, datasets, and trained
  adapter checkpoints still stay out of git/package artifacts.
- Underfit installation is pinned to a reviewed immutable commit. Verify its
  origin, exact commit, required files, and license hash before executing its
  downloaded scripts.
- Do not describe this as only a long-form instrumental music tool. It can support
  any use case Stable Audio 3 Medium supports, subject to model limits.
- Do not describe this as a Suno-style lyric-song generator. Stable Audio 3
  Medium can create vocal-like textures, but official docs say it does not output
  intelligible vocals and is not designed for speech or voice generation.
- Keep generated source tracks resumable and render assembled long outputs as MP3.
- Prefer free-form `--style` prompts. Treat recipes as optional scaffolds, not a
  complete preset catalog.
- Use `legends-sa3 prompt` to preview expanded prompts before expensive long
  runs.
- For instrumental music, positively prefix `TrackType: Music, VocalType:
  Instrumental`. At the post-trained Medium default `cfg_scale=1.0`, negative
  prompts are inactive in the official sampler.
- Use `--allow-vocals` only for vocal-texture experiments, not as a reliable
  lyric or clean-singing feature.
- For very long outputs, use streaming crossfade mixing. Avoid a single huge ffmpeg
  `acrossfade` graph because it can run out of memory.
- Use the default `active-cue` mix policy for long masters. It trims generated
  near-silent dead air, quiet tails that would waste overlap time, and starts
  incoming tracks at usable cue points.
- Do not add global fade-in to the first track or global fade-out to the final
  track unless requested.
- Read [Prompt mastery](references/prompt-mastery.md) for prompting, BPM,
  duration, seed tournaments, speech beds, and SFX. Read
  [Large REST API](references/large-api.md) before planning or executing hosted
  Stable Audio 3 Large requests. Read
  [Surfaces and receipts](references/surfaces-and-receipts.md) before hosted or
  benchmark work. Read [Mixing and adapters](references/mixing-and-adapters.md)
  before long assembly or adapter use. These references ship inside every
  installed copy of the skill; an Empire or Obsidian vault is never required.

## Hosted Large and web studio boundaries

Keep these four surfaces distinct in every plan and receipt:

1. local Stable Audio 3 Medium;
2. hosted Stable Audio 3 Large through the Platform REST model ID `stable-audio-3`;
3. Stable Audio web studio (some official KB screens call the engine ST-1);
4. the Stable Audio DAW plugin;
5. the Legends downstream mixer or DAW.

Route the operation before choosing tools: use the local CLI for Medium; use an
authorized Stability Platform client or the guarded `legends-sa3 large`
commands for hosted Large; use browser interaction
only for a verified web-studio session; use the mixer or DAW only after source
generation. Never silently substitute one surface for another.

- The Large REST API supports text-to-audio, audio-to-audio, inpaint, and async
  result retrieval. It does not expose the web studio's Full Mix, Multi-Track,
  lane, tape-editing, DSP, or mixdown controls.
- Preview requests with `legends-sa3 large plan`. Execute with `legends-sa3
  large generate` only after a live price/balance check, an explicit
  `--confirmed-live-credits` value, and `--confirm-paid`; load the secret only
  from `STABILITY_API_KEY`.
- The paid command writes a pending receipt immediately after submission. If
  polling is interrupted, recover the existing job with `legends-sa3 large
  result --generation-id <id>`; do not submit the prompt again. Output and
  receipt files are never overwritten unless `--overwrite` is explicit.
- Download and hash successful Large results promptly. Verify the live retention
  window before relying on it. Record the generation ID, request, timestamps,
  response headers, output facts, SHA-256, credit cost, and model label without
  recording `STABILITY_API_KEY`.
- Treat Platform API credits and Stable Audio web credits as separate pools.
  The dated official plugin guide says plugin cloud generations share the web
  account pool through Stable Sessions; verify that live before spending.
  Identify the pool and expected cost before any paid action.
- **Full Mix** means one combined stereo composition. **Multi-Track** means one
  synchronized composition generated as separate instrument lanes or stems.
  Neither means a sequence of completed songs, an automatic DJ mix, or an
  official crossfade duration.
- A web-studio result is not labeled Large unless live product evidence proves
  that exact tier and version. Preserve its displayed model metadata separately.
- For web work, read [Surfaces and receipts](references/surfaces-and-receipts.md)
  for the Full Mix/Multi-Track router, exact generative actions, lane/regeneration
  workflow, current export controls, dated credit schedule, and plugin boundary.
- For a Large benchmark, acquire paid source audio only through the Platform
  REST model ID `stable-audio-3`. Do not spend web credits or substitute a
  web-studio result unless the live session explicitly proves the exact Large
  tier and version.
- Before clicking web Start, visually prove the exact prompt, mode, length,
  pre-run web credit balance, and enabled Start state. Afterward, prove the
  result, credit delta, session model, lane count, and generative-action ledger.
  A semantic click is not proof that text was entered.
- Do not claim stableaudio.com is agent-operable end to end until one successful
  prompt entry, generation, result inspection, and export have been proven with
  the active browser transport.
- The Legends 12-second active-cue crossfade is a local production default, not
  a Stability.ai standard. When benchmarking, choose a transition policy after
  listening to the calibration family, then apply it identically to both model
  arms unless the comparison is explicitly about different workflows.
- Treat Large duration as a creative conditioning control, not merely a file
  length. The official technical report finds the strongest complete-song
  evidence at intermediate `120-190s` lengths and reduced prompt adherence at
  `380s`, with the longest examples biased toward ambient/classical material.
- For Large discovery, prefer `120s` canaries. Verify current Platform pricing
  before spending; very short full-song requests are not the documented quality
  sweet spot.
- Choose a genre-sensitive production range instead of one universal duration.
  For a `14:09.452` program, begin with five sources around `175-190s` or six
  around `145-170s`; use shorter/more sources for dense genres and longer/fewer
  sources for spacious genres. See
  [Prompt mastery](references/prompt-mastery.md).
- Omitting the Large API `duration` chooses the fixed `190s` default. Do not
  describe omission as an adaptive `AUTO` mode.

For paid or benchmark work, read
[Surfaces and receipts](references/surfaces-and-receipts.md). Freeze the prompt,
role, requested BPM, duration, integer seed,
steps, CFG, source format, and downstream treatment before a Medium/Large A/B.
Disclose that equal seed numbers do not imply equivalent latent noise and that
the hosted checkpoint revision is not necessarily exposed.

## Workflow

0. Bootstrap a source checkout with an isolated environment. On Windows use
   `python -m venv .venv`, then `.\.venv\Scripts\python.exe -m pip install -e
   ".[download]"` and invoke `.\.venv\Scripts\legends-sa3.exe`. On macOS/Linux
   use `python3 -m venv .venv`, `./.venv/bin/python -m pip install -e
   '.[download]'`, and `./.venv/bin/legends-sa3`. Install `[generate]` only
   after selecting the correct PyTorch build for the machine.
1. Run `legends-sa3 doctor` from that environment.
2. If model files are missing, explain the approval step and run:
   `legends-sa3 download-model --model medium --output ./models/stable-audio-3-medium`.
3. Help shape the metadata-plus-prose prompt, duration, and seed tournament.
   Default post-trained Medium to 8 Ping-Pong steps and CFG 1.0. Treat negative
   guidance at non-default CFG as an experiment, not a quality upgrade.
4. Plan duration when needed. For example:
   `legends-sa3 plan --minutes 60 --vram-gb 16 --crossfade 12`.
5. Preview prompts when needed. For important music, compare 3-4 prompt families
   with at least 4 short seeds each before a long render. `prompt --count` shows
   expansion only; the actual local canary is a short one-track generation such
   as `legends-sa3 generate --model-dir ./models/stable-audio-3-medium
   --stable-audio-repo ../stable-audio-3 --style "lo-fi study hip hop, warm
   Rhodes, soft boom bap drums, 82 BPM" --minutes 1 --track-seconds 60
   --seed-base 41000 --steps 8 --cfg-scale 1 --output ./output/canary-41000`.
   Repeat with a new output directory and seed base. `--seed-base` is the first
   track's seed; later tracks increment by one.
6. Generate:
   `legends-sa3 generate --model-dir ./models/stable-audio-3-medium
   --stable-audio-repo ../stable-audio-3 --style "lo-fi study hip hop, warm
   Rhodes, soft boom bap drums, 82 BPM" --minutes 60 --vram-gb 16
   --seed-base 41000 --steps 8 --cfg-scale 1 --output ./output/lofi-study-60m`.
7. Optionally load native Stable Audio 3 LoRA or DoRA adapters:
   `legends-sa3 generate --lora-ckpt-path ./adapters/eisbach-medium/model.safetensors --lora-strength 1.0 ...`.
8. Use `legends-sa3 lora-studio install/start/import/list-adapters` when the user
   wants to train or manage custom Underfit adapters.
9. Analyze source tracks before long mixes when cue quality matters:
   `legends-sa3 analyze --input-dir ./output/lofi-study-10h/tracks_mp3`.
10. If tracks already exist and the user wants a continuous master, mix only:
   `legends-sa3 mix --input-dir ./output/lofi-study-10h/tracks_mp3 --output ./output/lofi-study-10h/master.mp3 --mix-policy active-cue`.
11. Verify with `ffprobe`.

For every material run, preserve native sources and a public-safe receipt with
the surface, operation, exact positive prompt, requested and assessed BPM,
duration, seed, steps, CFG, whether negative guidance applied, cost pool,
result ID when provided, timestamps, output facts, SHA-256, cue warnings,
artifacts, and claim boundary. Never put secret values or private local paths in
the receipt.

For sound effects, start with `TrackType: SFX, VocalType: None`, name
one event, describe attack and decay, request `one-shot, sparse, no rhythmic
bed`, compare seeds, preserve the raw render, and trim only after selection.

## Mix Quality Policy

- `active-cue` is the default and preferred long-master policy.
- `strict` keeps exact raw track boundaries and only applies the overlap
  crossfade.
- `--quality-gate warn` reports cue findings and still renders.
- `--quality-gate fail` stops before rendering if source tracks have cue-analysis
  warnings.

## VRAM defaults

- 24 GB class: 380 seconds is a hardware ceiling starting point, not a universal
  creative-duration recommendation.
- 20 GB: 300 second segments.
- 16 GB: 240 second segments.
- 12 GB: 180 second segments.
- 8 GB: 120 second segments.
- Below 8 GB: use short Medium segments, queue a Medium-capable host, or stop and ask.

## Starter recipes

- `lofi-study`: softer study/background bed direction.
- `trip-hop-trance`: more driving breakbeat/trance direction without chill positioning.

## Known Long-Mix Formula

For a 24 GB RTX 4090, this formula worked:

- `98` tracks
- `380s` each
- `12s` crossfades
- final duration: `36076s`, about `10:01:16`
- MP3: `320 kbps`, stereo, `44.1 kHz`

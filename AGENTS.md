# Legends Stable Audio 3 Agent Guide

## Purpose

Help users operate Stable Audio 3 across local Medium, hosted Large, the web
studio, and downstream mixing. The repository CLI directly covers local setup,
prompt planning, VRAM-aware generation, batches, analysis, and crossfaded MP3
assembly.

The canonical cross-platform operating skill is
`skills/legends-stable-audio-3/SKILL.md`. Keep generated skill mirrors in sync
with `python scripts/sync_skill_adapters.py --sync`; do not hand-edit mirrors.

## Safety and licensing boundaries

- Project-owned source, documentation, tests, and designated assets are licensed
  under Apache License 2.0. See `LICENSE`, `NOTICE`, and
  `THIRD_PARTY_NOTICES.md`.
- Treat Legends Stable Audio 3 as an independent compatibility project. Do not
  claim affiliation with, sponsorship by, or endorsement from Stability AI.
- Never package, copy, mirror, or commit model weights.
- Never bypass Hugging Face gated model approval.
- Always direct users to accept the Stability AI terms themselves before model download.
- Treat commercial-use questions as license-sensitive. Point users to the current model
  card and Stability AI license, and do not give legal certainty.
- Native Stable Audio 3 LoRA or DoRA adapters can be loaded with
  `--lora-ckpt-path`; PEFT-style adapters need a separate integration path.
- The optional Underfit LoRA Studio is MIT-licensed code and can be installed
  locally with `legends-sa3 lora-studio`; model weights, datasets, and trained
  adapter checkpoints still stay out of git/package artifacts.
- Underfit installation is pinned to a reviewed immutable commit. Verify its
  origin, commit, required files, and license hash before executing its scripts.
- Never package, mirror, copy, or commit adapter weights.
- Never package secrets, private generated media, local state, or private
  organization paths and content.
- Do not imply the project is only for long-form or instrumental music. It can
  support whatever Stable Audio 3 Medium supports, subject to model limits.
- Do not imply Stable Audio 3 can turn typed lyrics into clean sung songs. The
  official docs say it does not output intelligible vocals and is not designed
  for speech or voice generation.
- Prefer instrumental prompts when the user asks for background, study, or video
  bed music, but follow the user's requested style.

## Standard workflow

1. Run `legends-sa3 doctor`.
2. If model files are missing, guide the user through `huggingface-cli login` and:
   `legends-sa3 download-model --model medium --output ./models/stable-audio-3-medium`.
3. Shape a metadata-plus-prose prompt and seed tournament. Default the
   post-trained Medium checkpoint to 8 steps and CFG 1.0; negative prompts are
   inactive at CFG 1.0.
4. Plan the run with `legends-sa3 plan --minutes <n>` or `--hours <n>` when the
   user wants a long assembled mix.
5. Preview prompts with `legends-sa3 prompt` when the user is exploring a style.
6. Generate with `legends-sa3 generate --style "<free-form style>"`.
7. Optionally load native Stable Audio 3 LoRA or DoRA adapters with
   `--lora-ckpt-path` and `--lora-strength`.
8. Use `legends-sa3 lora-studio install/start/import/list-adapters` when the user
   wants to train or manage custom Underfit adapters.
9. Analyze source tracks with `legends-sa3 analyze` before long mixes when quiet
   heads/tails could matter.
10. Mix existing tracks with `legends-sa3 mix` only when the user wants a continuous
   crossfaded master.
11. Verify output duration with `ffprobe` or `legends-sa3 mix` output checks.

## Practical defaults

- 24 GB VRAM: 380 seconds is a hardware ceiling starting point, not a universal
  creative-duration recommendation.
- 16 GB VRAM: start at 240 second segments.
- 12 GB VRAM: start at 180 second segments.
- 8 GB VRAM: start at 120 second segments.
- Crossfade: 12 seconds is a local non-beat-critical bed default; use measured
  tempo, bars, and phrases when beat alignment matters.
- Mix policy: `active-cue` by default. Use `strict` only when the user wants raw
  track boundaries.
- MP3 output: 320 kbps, stereo, 44.1 kHz.

## Crossfade quality policy

- Prefer `--mix-policy active-cue` for long masters.
- Treat generated dead air and slow musical intros differently: trim near-silent
  dead air and quiet tails, but use active cue starts for incoming tracks instead
  of calling every gradual intro silence.
- Use `--quality-gate warn` by default and `--quality-gate fail` when the user
  wants bad source tracks rejected before render.
- Do not add global fade-in to the first track or global fade-out to the final
  track unless the user explicitly asks.

## Prompting policy

- Prefer free-form `--style` prompts over forcing users into built-in recipes.
- Treat recipes as optional scaffolds, not as a complete genre catalog.
- Include concrete musical metadata when helpful: `TrackType`, `VocalType`,
  genre, instruments, mood or energy, production character, and BPM.
- Use `--allow-vocals` only when the user explicitly wants vocal-like textures or
  does not want the instrumental negative prompt. It does not enable reliable
  lyric singing.

## Verification expectations

After changing code, run:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests
python -m legends_sa3 plan --hours 10 --vram-gb 24 --crossfade 12
```

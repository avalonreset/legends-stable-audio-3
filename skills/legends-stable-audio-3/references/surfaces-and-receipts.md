# Surfaces, paid actions, and receipts

## Surface contract

Do not silently substitute one Stable Audio surface for another.

| Surface | Use | Boundary |
|---|---|---|
| Local Medium | Local text generation, seed search, batches, native adapters | Gated weights stay outside the package; hardware ceiling is not quality advice |
| Hosted Large REST | Authorized paid text-to-audio, audio-to-audio, inpaint, benchmark work | No web lanes, web DSP, or immutable checkpoint revision is guaranteed |
| Web studio (some KB screens call the engine ST-1) | Full Mix, synchronized Multi-Track, lane editing, effects, export | Preserve displayed model; do not relabel the session as Large without proof |
| DAW plugin | In-session generation inside a supported DAW | Beta/platform support and cloud model can change; verify the live plugin |
| Mixer or DAW | Cue selection, trimming, alignment, transitions, gain, crop, delivery | Editorial choices are not Stability model features or standards |

Full Mix is one combined stereo composition. Multi-Track is one synchronized
composition split into lanes or stems. Neither means a playlist, a DJ mix, or
an official crossfade recipe.

## Web studio field guide

Verified against the official Stable Audio guide on 2026-09-03:

- **Full Mix** sends the prompt as written and starts with one mixed track.
- **Multi-Track** lets a producer agent choose an arrangement and returns
  separate synchronized parts. It is experimental and can drift from a literal
  prompt. One session holds up to four active tracks.
- Length choices are `AUTO`, `0:30`, `1:00`, `1:30`, and `3:00`. Tempo + Key
  reference attachment is Multi-Track-only; it transfers detected tempo/key,
  not the attached audio's sound.
- Generative actions are **Start Full Mix**, **Start Multi-Track**, **Add
  Track**, **Regenerate**, **Replace Section**, and **Extend**. Mixing, faders,
  pan, mute/solo, tape edits, splice edits, effects, bounce, and export operate
  on existing audio and are described as non-generative/free.
- Export **MIXDOWN** for one WAV or **STEMS** for a ZIP of active lanes. The
  **NORM** toggle chooses normalized export versus deck level.
- The dated web guide listed 4 credits for Full Mix, 6 for Multi-Track, and 4
  for each Add Track, Regenerate, Replace Section, or Extend action. Recheck the
  live meter before spending.

Studio workflow: enter a concrete prompt; choose Full Mix or Multi-Track; choose
length; verify the displayed model and web balance; press Start; then iterate on
the one wrong lane or region instead of discarding the whole session. Preserve
the lane count, credit delta, displayed model, actions, and export type.

The official plugin guide observed on 2026-09-03 describes macOS VST/AU support,
local Small/Medium processing, and authenticated Stable Audio 3 Large cloud
generation sharing the web-account credit pool through Stable Sessions. It
lists Windows and AAX as upcoming. Treat all plugin support as dated and verify
the installed release rather than projecting web or REST features onto it.

## Paid-action gate

Before any paid API or web-studio generation:

1. verify the live surface, model label, controls, limits, and retention;
2. identify the Platform or web credit pool;
3. verify current price and available balance;
4. state call count and maximum expected cost;
5. obtain authorization for that scoped run.

The Platform reference listed 26 credits per successful Stable Audio 3 request
when this skill was refreshed on 2026-09-02. This is dated evidence, not a
promise. Verify it live immediately before spending. Never record an API key.
Download, verify, and hash successful hosted results promptly.

For browser work, prove the prompt, mode, length, displayed model, balance, and
enabled Start control before generation. Afterward, prove the result, credit
delta, model label, lane count, and action ledger. A click acknowledgement is
not proof that text was entered or a generation completed.

## Matched Medium/Large A/B

Freeze byte-identical positive prompts, musical role, requested BPM, duration,
requested integer seed, steps, CFG, source format, and downstream treatment.
Exclude adapters, conditioning audio, inpaint, web edits, and asymmetric
mastering from a pure model comparison. Review with blind labels and
synchronized switching.

An equal integer seed is matched request metadata; it does not mean Medium and
Large began from identical latent noise. The hosted checkpoint revision may not
be exposed. State both limitations in the result.

## Public-safe receipt

```yaml
surface: medium-local | large-rest | web-studio-st1 | downstream-mixer-daw
operation: text-to-audio | audio-to-audio | inpaint | full-mix | multi-track | mix
displayed_model: <public model or service label>
prompt: <exact positive prompt>
prompt_sha256: <hash>
prompt_family: <label>
bpm:
  requested: <number or intentionally omitted>
  feel: <straight | broken | halftime | double-time | free-time>
  assessed: <number or unknown>
  drift: <finding>
duration:
  requested_seconds: <number>
  actual_seconds: <number>
  thesis: <why this role needs this length>
settings:
  seed: <requested integer>
  steps: <number>
  cfg: <number>
  negative_requested: <true | false>
  negative_applied: <true | false | not-supported>
cost:
  pool: <platform | web | none>
  expected_credits: <live-verified number or unknown>
  actual_credits: <verified number or unknown>
provenance:
  generation_id: <if provided>
  started_at: <timestamp>
  completed_at: <timestamp>
  output_sha256: <hash>
output:
  format: <wav | mp3>
  sample_rate_hz: <number>
  channels: <number>
  bytes: <number>
qa:
  prompt_adherence: <finding>
  tempo: <finding>
  cue_warnings: <list>
  artifacts: <list>
mix:
  policy: <none | strict | active-cue | daw>
  transition_basis: <seconds | bars | phrase>
  global_fades: <description>
claim_boundary: <what the result does and does not prove>
```

Never put secrets, private machine paths, private media identifiers, gated
weights, adapter weights, datasets, or internal organization content in a
public receipt.

## First-party sources

- Web studio guide: `https://stableaudio.com/docs`
- First-mix walkthrough: `https://stability.ai/guides/make-your-first-mix-with-stable-audio`
- Plugin guide: `https://kb.stability.ai/knowledge-base/stable-audio-daw-plugin-guide`

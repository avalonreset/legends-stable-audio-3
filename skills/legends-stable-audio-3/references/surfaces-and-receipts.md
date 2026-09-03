# Surfaces, paid actions, and receipts

## Surface contract

Do not silently substitute one Stable Audio surface for another.

| Surface | Use | Boundary |
|---|---|---|
| Local Medium | Local text generation, seed search, batches, native adapters | Gated weights stay outside the package; hardware ceiling is not quality advice |
| Hosted Large REST | Authorized paid text-to-audio, audio-to-audio, inpaint, benchmark work | No web lanes, web DSP, or immutable checkpoint revision is guaranteed |
| Web studio / ST-1 | Full Mix, synchronized Multi-Track, lane editing, effects, export | Preserve displayed model; do not relabel the session as Large without proof |
| Mixer or DAW | Cue selection, trimming, alignment, transitions, gain, crop, delivery | Editorial choices are not Stability model features or standards |

Full Mix is one combined stereo composition. Multi-Track is one synchronized
composition split into lanes or stems. Neither means a playlist, a DJ mix, or
an official crossfade recipe.

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


# Hosted surfaces and public-safe receipts

Choose the Stable Audio surface before choosing tools or settings. Do not
silently substitute a web-studio result for hosted Large, or treat downstream
editing as a model capability.

## Surface router

| Surface | Use it for | Evidence boundary |
|---|---|---|
| Local Medium | Inspectable local inference, seed search, resumable batches, native adapters | Hardware limits are not creative-duration advice; gated terms still apply |
| Hosted Large REST | Authorized Platform text/audio generation and matched benchmarks | Verify live model, limits, pricing, balance, and retention before use |
| Web studio | Interactive Full Mix, Multi-Track, lane editing, effects, and export | Record the displayed model; do not infer Large from the product family |
| Legends mixer or DAW | Cue analysis, trimming, crossfades, tempo alignment, gain, crop, and delivery | Editorial choices are not Stability model features or standards |

Full Mix means one combined stereo composition. Multi-Track means one
synchronized composition split into lanes or stems. Neither means a sequence of
finished songs or an automatic DJ mix.

For the exact Stable Audio 3 request schema, REST endpoints, asynchronous poll
flow, and guarded `legends-sa3 large` commands, read the portable
[`large-api.md`](../skills/legends-stable-audio-3/references/large-api.md)
reference.

## Paid-action gate

Before any paid API or web-studio action:

1. verify the live product surface and displayed model;
2. identify the Platform or web credit pool;
3. verify current price, balance, limits, and retention;
4. state the expected call count and maximum expected cost;
5. obtain the user's authorization for that scoped run.

The Stability Platform reference listed `26` credits for a successful Stable
Audio 3 request when this guide was refreshed on 2026-09-02. Treat that number
as a dated observation, not a promise: verify the live API reference and the
correct credit pool immediately before spending.

Never record an API key. After a successful hosted result, download promptly,
verify the audio, compute SHA-256, and retain the local source with its receipt.
The guarded CLI writes a pending receipt as soon as a generation ID is returned.
Resume interrupted polling with `legends-sa3 large result --generation-id <id>`;
never resubmit merely because a client timed out. Public receipts use safe file
names rather than absolute local paths, and existing files require an explicit
`--overwrite`.

## Matched Medium/Large benchmark

Freeze a written contract before generation. Match fresh outputs, byte-identical
positive prompts, musical role, requested BPM, duration, requested integer seed,
steps, CFG, source format, and downstream cue/mix/master treatment. Keep negative
prompts, adapters, conditioning audio, inpaint/continuation, web-studio editing,
and asymmetric mastering out of a pure comparison lane.

Disclose that the hosted service may not expose an immutable checkpoint revision
and that equal seed integers are matched request metadata, not proof of identical
latent noise. Review with blind labels and synchronized switching. Keep human
creative judgment separate from technical QA.

## Minimal receipt

```yaml
surface: medium-local | large-rest | web-studio | downstream-mixer-daw
operation: text-to-audio | audio-to-audio | inpaint | full-mix | multi-track | mix
displayed_model: <public model or service label>
prompt: <exact positive prompt>
prompt_sha256: <hash>
prompt_family: <label>
bpm:
  requested: <number or intentionally omitted>
  assessed: <number or unknown>
  feel: <straight | broken | halftime | double-time | free-time>
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
  expected_credits: <verified value or unknown>
  actual_credits: <verified value or unknown>
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
claim_boundary: <what this result does and does not prove>
```

Do not include secret values, private machine paths, private media identifiers,
gated model files, adapters, datasets, or internal organization content in a
public receipt.

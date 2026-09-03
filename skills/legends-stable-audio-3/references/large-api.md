# Stable Audio 3 Large REST API

Use this reference for Stability Platform requests to the hosted
`stable-audio-3` model. It was verified against Stability AI's live OpenAPI
document on 2026-09-03. Recheck the live schema, pricing, balance, retention,
and service status immediately before spending credits.

## Safe CLI flow

Preview a request without contacting Stability or spending credits:

```powershell
legends-sa3 large plan `
  --operation text-to-audio `
  --prompt "TrackType: Music, VocalType: Instrumental, deep dub techno, 118 BPM" `
  --duration 120 --seed 42 --steps 8 --cfg-scale 1 --output-format wav
```

Execute only after verifying the current price and balance. Put the key in the
environment; never pass it as an argument or write it to a receipt:

```powershell
$env:STABILITY_API_KEY = "<load from your secret store>"
legends-sa3 large generate `
  --operation text-to-audio `
  --prompt "TrackType: Music, VocalType: Instrumental, deep dub techno, 118 BPM" `
  --duration 120 --seed 42 --steps 8 --cfg-scale 1 --output-format wav `
  --output .\output\large-canary.wav `
  --confirmed-live-credits 26 --confirm-paid
```

The guarded command submits one asynchronous generation, polls until the audio
is ready, writes it atomically, calculates SHA-256, and writes a JSON receipt.
It refuses to replace existing output or receipt files unless `--overwrite` is
explicit. Audio uploads are checked with `ffprobe` before a paid submission.
`--confirmed-live-credits` records the price the operator verified; it does not
replace a live price or balance check. Each execution is one paid request.

POSIX shells use the same CLI with ordinary line continuations:

```bash
export STABILITY_API_KEY="<load from your secret store>"
legends-sa3 large generate \
  --operation text-to-audio \
  --prompt "TrackType: Music, VocalType: Instrumental, deep dub techno, 118 BPM" \
  --duration 120 --seed 42 --steps 8 --cfg-scale 1 --output-format wav \
  --output ./output/large-canary.wav \
  --confirmed-live-credits 26 --confirm-paid
```

## Interrupted-job recovery

After the paid POST returns, the command prints the generation ID and writes a
pending receipt before it begins polling. Preserve that receipt. If the process
is interrupted or times out, resume the existing job without another POST:

```powershell
legends-sa3 large result `
  --generation-id "<id from the pending receipt>" `
  --output .\output\large-canary.wav --output-format wav
```

```bash
legends-sa3 large result \
  --generation-id "<id from the pending receipt>" \
  --output ./output/large-canary.wav --output-format wav
```

The recovery command only polls and downloads. It cannot create another paid
generation. If submission itself ended with an ambiguous network error before
an ID was received, inspect the Stability account/job history before deciding
whether to submit again.

## Endpoints and lifecycle

| Operation | POST endpoint | Additional fields |
|---|---|---|
| Text-to-audio | `/v2beta/audio/stable-audio/text-to-audio` | none |
| Audio-to-audio | `/v2beta/audio/stable-audio/audio-to-audio` | `audio`, `strength` |
| Inpaint | `/v2beta/audio/stable-audio/inpaint` | `audio`, `mask_start`, `mask_end` |

All POST operations use `multipart/form-data`, `Authorization: Bearer
$STABILITY_API_KEY`, and return HTTP `202` with `{ "id": "..." }`. Poll:

```text
GET https://api.stability.ai/v2beta/audio/results/{id}
Authorization: Bearer $STABILITY_API_KEY
Accept: audio/wav | audio/mpeg
```

HTTP `202` means the generation remains in progress. HTTP `200` returns the
audio bytes; preserve `seed`, `finish-reason`, and `x-request-id` response
headers. The CLI validates the response media type and WAV/MP3 signature before
writing it. Handle `400`, `403`, `422`, `429`, and `500` explicitly. Do not blindly
retry paid submissions after an ambiguous network failure because the first job
may already exist.

## Stable Audio 3 request schema

| Field | Rule | Default |
|---|---|---:|
| `prompt` | required, 1-10000 characters | none |
| `model` | fixed `stable-audio-3` | `stable-audio-3` |
| `duration` | 1-380 seconds | 190 |
| `seed` | 0-4294967294; zero/omitted requests random | 0 |
| `steps` | 4-8 | 8 |
| `cfg_scale` | 1-25 | 1 |
| `output_format` | `mp3` or `wav` | mp3 upstream; Legends defaults to wav |
| `audio` | mp3/wav, 6-380 seconds; required for audio operations | none |
| `strength` | 0-1 for audio-to-audio | 1 |
| `mask_start`, `mask_end` | inpaint range within the requested duration | 30, 380 upstream |

The live Platform pricing page listed 26 credits per Stable Audio 3 request on
2026-09-03, with one credit listed as $0.01. This is dated evidence, not a
guarantee. Failed generations are described as uncharged, but an interrupted
client must not assume a request failed merely because the response was lost.

## Surface boundary

The Platform REST API is not the Stable Audio web studio or DAW plugin. It does
not expose Full Mix, Multi-Track lanes, tape edits, effects, bounce controls, or
the Stable Sessions UI. The web studio currently supports Full Mix and
Multi-Track workflows; the DAW plugin can use Stable Audio 3 Large through its
own authenticated cloud/session surface. Preserve the displayed product and
credit pool instead of silently treating these routes as interchangeable.

## First-party sources

- API reference and downloadable OpenAPI:
  `https://platform.stability.ai/docs/api-reference`
- Pricing: `https://platform.stability.ai/pricing`
- Stable Audio 3 prompt guide:
  `https://stability.ai/guides/stable-audio-3-prompt-guide`
- Stable Audio web guide: `https://stableaudio.com/docs`
- Product family: `https://stability.ai/stable-audio`

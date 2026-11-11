# Legends Stable Audio 3 Agent Recipe

Deterministic operator procedure for `legends-stable-audio-3` (`v0.1.5`). Loaded by `cto-legends handoff legends-stable-audio-3`. Do not register a separate per-module skill.

## 1. Readiness & Diagnostics

Verify local package readiness and hardware/backend capabilities before planning or generating audio:

```bash
legends-sa3 doctor --offline
```

- `legends-sa3 doctor` (and `legends-sa3 doctor --offline`) inspects local Python, `ffmpeg`, `ffprobe`, PyTorch, CUDA/MPS availability, the optional `stable_audio_3` runtime, and VRAM capacity without requiring network access, model weights, or API keys.
- Validate the bundled portable recipe reference library at any time with:

```bash
legends-sa3 skill validate
```

## 2. Complete CLI Command Surface

| Command | Purpose | Mutates Local State / Network |
| --- | --- | --- |
| `legends-sa3 doctor [--offline] [--json \| --text]` | Inspect platform, Python, `ffmpeg`/`ffprobe`, PyTorch, CUDA/MPS, `stable_audio_3` runtime, and VRAM | Read-only |
| `legends-sa3 prompt [--style "<prompt>" \| --prompt "<prompt>"] [--recipe lofi-study\|trip-hop-trance \| --genre lofi-study\|trip-hop-trance] [--bpm <n> \| --omit-bpm] [--allow-vocals] [--negative-prompt "<text>"] [--custom-style "<text>"] [--count <n>]` | Preview expanded metadata-plus-prose Stable Audio 3 prompts and negative-prompt status | Read-only |
| `legends-sa3 plan [--hours <n>] [--minutes <n>] [--vram-gb <n>] [--track-seconds auto\|<n>] [--crossfade <sec>]` | Calculate VRAM-aware segment duration, track count, and total assembled mix duration | Read-only |
| `legends-sa3 production-plan --minutes <n> [--song-seconds 380] [--overlap-estimate 12] [--runtime-intent approximate\|minimum\|exact] [--credits-per-job 26]` | Plan full-length hosted Large songs, set runtime, and estimated credit cost | Read-only |
| `legends-sa3 arrange --plan <arrangement.json> --output <out.wav> [--overwrite] [--allow-external-sources]` | Render explicit per-pair musical cues, independent fades, and float WAV master | Writes WAV + receipt JSON |
| `legends-sa3 download-model [--model medium] --output <dir> [--revision <commit-sha>]` | Download gated `stabilityai/stable-audio-3-medium` and `t5gemma-b-b-ul2` conditioner after user accepts HF terms | Downloads model weights |
| `legends-sa3 generate --model-dir <dir> [--stable-audio-repo <dir>] [--style "<prompt>" \| --prompt "<prompt>"] [--recipe lofi-study\|trip-hop-trance \| --genre lofi-study\|trip-hop-trance] [--bpm <n> \| --omit-bpm] [--allow-vocals] [--negative-prompt "<text>"] [--hours <n>] [--minutes <n>] [--vram-gb <n>] [--track-seconds auto\|<n>] [--crossfade 12] [--steps 8] [--cfg-scale 1.0] [--seed-base 60470000] [--bitrate 320k] [--custom-style "<text>"] [--lora-ckpt-path <path.safetensors>] [--lora-strength <f>] [--mix-policy active-cue\|strict] [--quality-gate warn\|fail\|off] [--cue-threshold-db -50.0] [--silence-threshold-db -80.0] [--cue-padding-seconds 0.25] [--overwrite] --output <dir>` | Generate single tracks or resumable multi-track batches locally on Stable Audio 3 Medium | Writes audio + manifest |
| `legends-sa3 analyze --input-dir <dir> [--pattern "*.mp3"] [--max-tracks 500] [--sample-rate 44100] [--channels 2] [--cue-threshold-db -50.0] [--silence-threshold-db -80.0] [--cue-padding-seconds 0.25] [--json-output <file>] [--overwrite]` | Analyze source tracks for near-silent heads/tails and active cue starts | Read-only (writes optional JSON) |
| `legends-sa3 mix --input-dir <dir> --output <master.mp3> [--pattern "*.mp3"] [--max-tracks 500] [--crossfade 12] [--sample-rate 44100] [--bitrate 320k] [--mix-policy active-cue\|strict] [--quality-gate warn\|fail\|off] [--cue-threshold-db -50.0] [--silence-threshold-db -80.0] [--cue-padding-seconds 0.25] [--overwrite]` | Stream-crossfade multiple tracks into a continuous MP3 master and verify with `ffprobe` | Writes MP3 + `.manifest.json` |
| `legends-sa3 large plan [--operation text-to-audio\|audio-to-audio\|inpaint] --prompt "<prompt>" [--duration 380] [--seed 0] [--steps 8] [--cfg-scale 1.0] [--output-format wav\|mp3] [--audio <file>] [--strength 1.0] [--mask-start 30] [--mask-end <sec>]` | Preview a hosted Stable Audio 3 Large REST request offline without spending credits | Read-only |
| `legends-sa3 large generate [--operation text-to-audio\|audio-to-audio\|inpaint] --prompt "<prompt>" [--duration 380] [--seed 0] [--steps 8] [--cfg-scale 1.0] [--output-format wav\|mp3] [--audio <file>] [--strength 1.0] [--mask-start 30] [--mask-end <sec>] --output <file> [--receipt <path>] --confirmed-live-credits <n> --confirm-paid [--poll-interval 10] [--request-timeout 120] [--result-timeout 1800] [--max-result-retries 5] [--overwrite]` | Submit, poll, validate, and download one paid Stable Audio 3 Large job with atomic receipts | Paid network call + writes audio |
| `legends-sa3 large result --generation-id <id> --output <file> [--output-format wav\|mp3] [--receipt <path>] [--poll-interval 10] [--result-timeout 1800] [--max-result-retries 5] [--overwrite]` | Resume polling and download an existing paid Large job without re-submitting | Network GET + writes audio |
| `legends-sa3 lora-studio status [--root <dir>] [--adapters-dir <dir>]` | Inspect Underfit LoRA Studio installation and local adapter registry | Read-only |
| `legends-sa3 lora-studio install [--root <dir>] [--update] [--run-underfit-install] [--with-setup] [--backend sa3\|sat]` | Clone or update the pinned Underfit LoRA Studio repository | Writes `.legends/lora-studio` |
| `legends-sa3 lora-studio start [--root <dir>] [--host 127.0.0.1] [--port 8787] [--state-dir <dir>] [--models-dir <dir>]` | Run the Underfit LoRA Studio dashboard in the foreground | Foreground local server |
| `legends-sa3 lora-studio import <source.safetensors> [--name <name>] [--source-run <id>] [--adapters-dir <dir>] [--overwrite]` | Import a `.safetensors` LoRA checkpoint into the local adapter registry | Writes `.legends/adapters` |
| `legends-sa3 lora-studio list-adapters [--adapters-dir <dir>]` | List imported `.safetensors` adapters and verify SHA-256 integrity | Read-only |
| `legends-sa3 skill path` | Print the installed canonical skill reference bundle path | Read-only |
| `legends-sa3 skill validate [--path <dir>]` | Validate the bundled or supplied skill reference bundle | Read-only |
| `legends-sa3 skill install --target <dir>` | Copy the bundled operating reference library (`RECIPE.md` + `references/`) into an explicit target | Writes `<target>/legends-stable-audio-3` |

## 3. Standard Operating Procedure

1. **Surface routing**: Determine whether the user wants local Medium generation, hosted Large API generation, cue-sheet arrangement (`production-plan` + `arrange`), or active-cue MP3 mixing (`analyze` + `mix`). Never silently substitute one surface for another.
2. **Readiness & planning**:
   - Run `legends-sa3 doctor --offline`.
   - Preview prompts with `legends-sa3 prompt --style "<brief>" --count 3`.
   - Plan segment counts with `legends-sa3 plan` (local Medium) or `legends-sa3 production-plan` / `legends-sa3 large plan` (hosted Large).
3. **Model & paid-action gates**:
   - For local Medium: require the user to accept Stability AI and Gemma gated terms on Hugging Face (`hf auth login`) before running `legends-sa3 download-model`.
   - For hosted Large: preview with `legends-sa3 large plan` first, verify live platform credit cost, and require explicit user confirmation before passing `--confirmed-live-credits <n> --confirm-paid` to `legends-sa3 large generate`. Never retry paid POST submissions automatically; recover interrupted jobs with `legends-sa3 large result --generation-id <id>`.
4. **Post-generation verification**:
   - Inspect generated tracks with `legends-sa3 analyze` or assemble with `legends-sa3 arrange` / `legends-sa3 mix`.

## 4. EDR and Security Guardrails

- **No hidden consoles or shell wrappers**: Never spawn background shells, hidden console windows, or execution-policy bypass shell wrappers. All subprocess invocations (`ffmpeg`, `ffprobe`, `git`) use explicit argument arrays (`shell=False`).
- **No credential harvesting**: Never read local browser profile databases, DPAPI stores, or third-party credential stores. Read `STABILITY_API_KEY` only from explicit environment variables and redact secrets from all receipts and logs.
- **Weight & media hygiene**: Never commit or bundle `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`, `.bin`, `.wav`, `.mp3`, or `.flac` artifacts into git or release distributions.
- **Pinned third-party code**: Underfit LoRA Studio is pinned to reviewed commit `8a96800a58c0e8b82327fc04ac31c473ed900b73` with origin, commit, required-file, and MIT license SHA-256 verification prior to execution.

# Model access

Stable Audio 3 Medium is a gated open-weight model. This project must not include
or redistribute model files. The wrapper's Apache-2.0 license does not grant
rights to Stable Audio weights or bypass Stability AI, Gemma, and Hugging Face
terms.

## User-owned approval flow

1. Create or sign in to a Hugging Face account.
2. Open the model page for `stabilityai/stable-audio-3-medium`.
3. Review and accept the model terms.
4. Review the bundled `LICENSE_GEMMA.md` / Gemma terms linked by the model repo.
5. Run `hf auth login` locally.
6. Run:

```powershell
legends-sa3 download-model --model medium --output .\models\stable-audio-3-medium
```

Expected files:

- `model_config.json`
- `model.safetensors`
- `t5gemma-b-b-ul2/config.json`
- `t5gemma-b-b-ul2/model.safetensors`
- `t5gemma-b-b-ul2/tokenizer.json` and tokenizer metadata

The conditioner is required for prompt encoding. `download-model` fetches the
complete inference bundle and rewrites the config's conditioner path to the
selected local directory. A checkpoint plus top-level config alone is an
incomplete installation.

## Release rules

- `.gitignore` excludes `models/`, `*.safetensors`, `*.ckpt`, `*.pt`, and audio outputs.
- GitHub releases must not attach model files.
- Example manifests may include model IDs, but not private tokens or model binaries.
- If a user asks whether they can use generated output commercially, point them
  to the current Stability AI license and model card.

## Known model facts from local validation

The tested Stable Audio 3 Medium config used:

- sample rate: `44100`
- sample size: `16777216`
- practical max single-shot length: about `380.44s`

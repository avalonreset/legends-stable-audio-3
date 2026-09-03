# Native LoRA Adapters

Legends Stable Audio 3 can load native Stable Audio 3 LoRA and DoRA
checkpoints through the official `stable_audio_3` runtime.

Use [LoRA Studio with Underfit](lora-studio.md) when you want to train your own
custom adapters before loading them with `--lora-ckpt-path`.

This is intentionally narrow support. The adapter must be a native Stable Audio
3 checkpoint accepted by `StableAudioModel.load_lora`, usually a `.safetensors`
file with Stable Audio 3 LoRA metadata. PEFT adapters use a different checkpoint
layout and are not supported by `--lora-ckpt-path` yet.

## Eisbach Medium

`ReasoningKingdom/Eisbach-Medium` is a native DoRA adapter for
`stabilityai/stable-audio-3-medium`. It is positioned for more temporally
structured long-form instrumental output and favors chamber or orchestral
textures, but it can still be tested against electronic prompts.

Download the adapter yourself from Hugging Face after reviewing its model card
and terms. Do not commit adapter weights to this repository.

```powershell
legends-sa3 generate `
  --model-dir .\models\stable-audio-3-medium `
  --stable-audio-repo ..\stable-audio-3 `
  --style "digital hardcore breakbeat trance, distorted 909 kicks, chopped amen breaks, acidic bassline, no vocals, 172 BPM" `
  --minutes 6 `
  --vram-gb 24 `
  --steps 16 `
  --cfg-scale 3.0 `
  --lora-ckpt-path .\adapters\eisbach-medium\model.safetensors `
  --lora-strength 1.0 `
  --output .\output\eisbach-breakbeat-test
```

Use the same prompt and seed with and without the adapter when deciding whether
it helps a genre. For long assembled mixes, compare generated source tracks
before the final crossfade render so the adapter's structure is easier to hear.

## Current Boundary

- Native SA3 LoRA or DoRA `.safetensors`: supported.
- Multiple native adapter paths: accepted by repeating `--lora-ckpt-path`.
- `--lora-strength`: applies through the official runtime after adapters load.
- PEFT adapters such as Arabic Maqam LoRA checkpoints: not supported by this
  flag until a PEFT-to-native or PEFT-loading path is added.
- Model weights and adapter weights stay outside git.

## Source Notes

- Stable Audio 3 Medium model card:
  `https://huggingface.co/stabilityai/stable-audio-3-medium`
- Eisbach Medium adapter:
  `https://huggingface.co/ReasoningKingdom/Eisbach-Medium`
- Stable Audio 3 Maqam LoRA:
  `https://huggingface.co/motiftechnologies/stable-audio-3-maqam-lora`

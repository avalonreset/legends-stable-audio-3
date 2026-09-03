# Troubleshooting

## `stable_audio_3` is not importable

Install or clone the official Stable Audio 3 repository, then pass it explicitly:

```powershell
legends-sa3 generate --stable-audio-repo ..\stable-audio-3 ...
```

## Model files are missing

Run:

```powershell
legends-sa3 download-model --model medium --output .\models\stable-audio-3-medium
```

If that fails, confirm that you accepted the model terms and ran
`huggingface-cli login`.

## CUDA is not detected

Run:

```powershell
legends-sa3 doctor
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

If CUDA is false, install the correct CUDA-enabled PyTorch build for your machine.

## Out of memory during generation

Reduce segment length:

```powershell
legends-sa3 generate --track-seconds 180 ...
```

Keep crossfade around 8 to 12 seconds.

## The result sounds like it ignored my prompt

Preview the expanded prompt before generating:

```powershell
legends-sa3 prompt --style "your target genre, instruments, mood, BPM" --count 3
```

Stable Audio 3 usually responds better to concrete audio metadata: genre,
instruments, mood or energy, production character, and BPM. If a prompt is vague,
fix the prompt before increasing steps.

## There are gaps or weak transitions between tracks

Analyze the generated source tracks:

```powershell
legends-sa3 analyze --input-dir .\output\my-run\tracks_mp3
```

Use the default active-cue mixer:

```powershell
legends-sa3 mix `
  --input-dir .\output\my-run\tracks_mp3 `
  --output .\output\my-run\master.mp3 `
  --crossfade 16 `
  --mix-policy active-cue
```

If you want warnings to stop the render, add `--quality-gate fail`.

## Out of memory during final mix

Use `legends-sa3 mix`, which uses streaming crossfade mixing. Avoid manually
building one massive ffmpeg filter graph with all source tracks at once.

## Final duration is slightly off

MP3 padding and encoder delay can move the probed duration by a small amount.
Use `ffprobe` for the final value.

With `--mix-policy active-cue`, the final can also be shorter than the plan if
generated source tracks contain quiet heads or tails that are trimmed before
mixing. Use `legends-sa3 analyze` to see those trim estimates.

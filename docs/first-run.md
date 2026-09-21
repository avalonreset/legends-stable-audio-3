# first run: a production plan before a model download

Use this short path to check installation and see what the toolkit adds. It
does not generate audio, download weights, or spend API credits.

## install the released core

Use Python 3.10 or newer in a virtual environment. Install the release wheel:

```sh
python -m pip install "https://github.com/avalonreset/legends-stable-audio-3/releases/download/v0.4.1/legends_stable_audio_3-0.4.1-py3-none-any.whl"
legends-sa3 skill validate
legends-sa3 prompt --style "warm dub techno, tape chords, deep bass, 118 BPM" --count 1
legends-sa3 plan --hours 10 --vram-gb 24 --crossfade 12
```

The skill check validates the bundled instructions. The prompt command prints
the expanded prompt and negative-prompt status. The plan prints target length,
segment duration, crossfade, track count, and resulting duration. `--vram-gb`
is a planning input, not a claim that this machine has that GPU. The ten-hour
result is assembled from separate tracks; it is not one model generation.

To use source instead of the wheel, install with `python -m pip install -e .`
from the checkout, then run the same commands.

## hand the plan to your agent

Open [the canonical skill](../skills/legends-stable-audio-3/SKILL.md) in an agent
with file and command access, or install it into your client's chosen skill
directory with `legends-sa3 skill install --target <skills-directory>`.

For example:

> plan a one-hour dub techno mix. inspect my hardware, show me a small prompt
> and seed trial, then tell me what is needed to generate it locally. keep the
> source tracks and verify the final duration.

The installer refuses to overwrite an existing skill. See
[agent compatibility](agent-compatibility.md) for loading options.

## choose the next step

| you want | next step | extra requirements |
|---|---|---|
| local Medium generation | [model access](model-access.md), then [README quick start](../README.md#local-medium-quick-start) | gated model approval, model files, runtime and suitable hardware |
| hosted Large generation | [Large reference](../skills/legends-stable-audio-3/references/large-api.md) | provider account, current pricing, explicit paid confirmation |
| a continuous master from existing tracks | [mix workflow](music-factory.md) | local audio files and FFmpeg/FFprobe |
| custom native adapters | [adapter guide](lora-adapters.md) | compatible adapter checkpoint and local model runtime |

Run `legends-sa3 doctor` before production. Missing FFmpeg or model tooling at
this stage does not invalidate the model-free prompt and planning checks.
Use [troubleshooting](troubleshooting.md) for the production dependency checks.

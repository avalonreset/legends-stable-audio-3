# LoRA Studio With Underfit

Legends Stable Audio 3 includes a first-class bridge to
`dada-bots/underfit`, the MIT-licensed Stable Audio 3 LoRA training dashboard.
Underfit is the training side; Legends is the generation, planning, adapter
registry, and long-mix side.

This workflow is intentionally split:

- Underfit code is MIT licensed and can be installed as an optional local tool.
- Stable Audio model files are not bundled and still require the user to accept
  the Hugging Face model terms.
- User datasets, trained checkpoints, and imported adapters stay in ignored local
  folders by default.

## Install

Clone and verify the Underfit checkout:

```powershell
legends-sa3 lora-studio install
```

This creates `.legends/lora-studio/underfit` by default. It verifies that the
checkout origin is `https://github.com/dada-bots/underfit`, checks out the
reviewed immutable commit
`8a96800a58c0e8b82327fc04ac31c473ed900b73`, and verifies its exact commit,
required files, and MIT license SHA-256 before use. It does not run Underfit's
setup flow unless you ask for it. Custom repository/ref overrides are not
accepted by the public CLI.

Run Underfit's own dependency setup when you are ready:

```powershell
legends-sa3 lora-studio install --run-underfit-install
```

This explicitly executes downloaded third-party `install.sh`. At the pinned
revision it may bootstrap `uv` using a remote installer, run `uv sync`, install
Python/system prerequisites, and prepare external runtime code. Review the
pinned script before opting in.

Run the full Underfit setup wizard only after accepting Stable Audio model terms:

```powershell
legends-sa3 lora-studio install --run-underfit-install --with-setup
```

The setup wizard can clone Stable Audio runtime code and download large or gated
model packs. Those downloads are external local state, can consume substantial
disk/network resources, and remain subject to their own terms. Legends never
packages them.

Underfit's current local quickstart targets Linux with an NVIDIA GPU. On Windows,
use Git Bash, WSL, or the Pinokio wrapper if the shell scripts are not directly
available.

## Start

Start the dashboard in the foreground:

```powershell
legends-sa3 lora-studio start
```

Default dashboard URL:

```text
http://127.0.0.1:8787
```

Change the port if needed:

```powershell
legends-sa3 lora-studio start --port 8790
```

## Train

Use Underfit's dashboard to create a dataset, configure a finetune, and train a
LoRA, DoRA, BoRA, or related native Stable Audio 3 adapter.

Underfit guidance that matters for Legends users:

- `sa3-medium` is the main target for this project.
- DoRA is a good default adapter type.
- 16 GB VRAM is ideal; 8 GB can work with conservative settings.
- Datasets should be coherent. Mixed style folders train weak adapters.
- Checkpoints land under Underfit's `state/runs/<run-id>/` folder as
  `.safetensors` files.

## Import

After training, import a checkpoint into the Legends adapter registry:

```powershell
legends-sa3 lora-studio import `
  .legends\lora-studio\underfit\state\runs\my-style\5000.safetensors `
  --name my-style `
  --source-run my-style
```

This copies the checkpoint to `.legends/adapters/my-style.safetensors` and writes
`.legends/adapters/my-style.json` with the source path, SHA-256 hash, import time,
and generation hint.

List imported adapters:

```powershell
legends-sa3 lora-studio list-adapters
```

## Generate

Use the imported adapter with the normal generation command:

```powershell
legends-sa3 generate `
  --model-dir .\models\stable-audio-3-medium `
  --stable-audio-repo ..\stable-audio-3 `
  --style "industrial breakbeat trance, distorted 909 kicks, no vocals, 172 BPM" `
  --minutes 6 `
  --vram-gb 24 `
  --lora-ckpt-path .legends\adapters\my-style.safetensors `
  --lora-strength 0.8 `
  --output .\output\my-style-test
```

## What Gets Committed

Commit:

- Legends source code.
- Docs and tests.
- Third-party license notices.

Do not commit:

- Stable Audio model files.
- Underfit downloaded model packs.
- User datasets.
- Trained adapter checkpoints unless you explicitly have redistribution rights.
- Generated MP3/WAV/FLAC output.

The default `.legends/` folder is ignored for this reason.

## Sources

- Underfit:
  `https://github.com/dada-bots/underfit/tree/8a96800a58c0e8b82327fc04ac31c473ed900b73`
- Underfit MIT license:
  `https://github.com/dada-bots/underfit/blob/8a96800a58c0e8b82327fc04ac31c473ed900b73/LICENSE`
- Stable Audio 3 Medium:
  `https://huggingface.co/stabilityai/stable-audio-3-medium`

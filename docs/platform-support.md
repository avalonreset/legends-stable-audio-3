# Platform support

Legends Stable Audio 3 separates portable orchestration from hardware-specific
model execution. “Cross-platform” means the skill, planning, prompting, hosted
Large client, receipts, analysis, and mixing workflows are designed for Windows,
macOS, and Linux. It does not mean every operating system has equivalent local
GPU acceleration.

| Capability | Windows x64 | Linux x64 | macOS Apple Silicon |
|---|---|---|---|
| Portable agent skill and references | Supported | Supported | Supported |
| Prompting, planning, and receipts | Supported | Supported | Supported |
| Hosted Large REST client | Supported | Supported | Supported |
| FFmpeg analysis and mixing | Supported with FFmpeg | Supported with FFmpeg | Supported with FFmpeg |
| Local Medium inference | CUDA path supported | CUDA path supported | CPU fallback only; no MPS performance claim |
| Underfit LoRA Studio | WSL/Git Bash wrapper path | Primary NVIDIA path | Not claimed in this release |

## Requirements

- Python 3.10 or newer. Release CI covers Python 3.10 and 3.12 on Windows and
  Ubuntu; release preparation also exercises Python 3.13 clean installs.
- FFmpeg and FFprobe on `PATH` for analysis, mixing, MP3 conversion, and paid
  audio-upload preflight.
- `STABILITY_API_KEY` only for explicitly authorized hosted Large requests.
- A separately installed, hardware-appropriate PyTorch environment plus the
  official Stable Audio runtime and gated model files for local Medium.

Run `legends-sa3 doctor` first. It reports OS, architecture, Python, FFmpeg,
Torch, CUDA, Apple MPS visibility, VRAM, and the backend this release will
actually select. Apple MPS may be visible through PyTorch, but the current local
runner deliberately selects CPU when CUDA is unavailable; use hosted Large for
reliable Mac generation unless a future release proves an MPS runtime.

## Installation examples

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install ".[download]"
.\.venv\Scripts\legends-sa3 doctor
```

POSIX shell on Linux or macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install '.[download]'
./.venv/bin/legends-sa3 doctor
```

The core install does not download model weights, modify global agent settings,
or select a PyTorch GPU wheel. Install the bundled skill only into an explicit
target with `legends-sa3 skill install --target <skills-directory>`.

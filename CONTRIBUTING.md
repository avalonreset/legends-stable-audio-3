# Contributing

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests
```

## Contribution rules

- Project-owned source and designated assets are licensed under Apache-2.0.
  Unless explicitly stated otherwise, intentionally submitted contributions are
  accepted under Apache-2.0 as described by Section 5 of `LICENSE`.
- Submit only work you have the right to contribute, including any applicable
  copyright and patent rights. Identify third-party material and preserve its
  license and attribution instead of presenting it as project-owned.
- Keep model weights out of the repo.
- Keep adapter weights, datasets, secrets, private generated media, local state,
  and private organization paths/content out of the repo.
- Keep generated audio out of the repo unless a maintainer explicitly approves it.
- Update docs when changing user-facing commands.
- Update tests when changing planning or mixing behavior.
- Do not register the module as its own skill. `skills/` holds only the pinned
  `cto-legends` router copy; never add mirrors or host shims.

## Pull request checklist

- Tests pass.
- `legends-sa3 plan --hours 10 --vram-gb 24 --crossfade 12` still returns 98 tracks.
- `python scripts/release_checks.py` passes.
- No model, adapter, dataset, secret, or generated-media artifact is tracked.
- Docs mention any changed setup or workflow behavior.
- License, NOTICE, third-party notices, and asset provenance remain accurate.
- The built sdist and wheel contain the bundled skill and no forbidden artifacts.

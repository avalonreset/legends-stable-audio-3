# Dependency and reproducibility policy

Legends Stable Audio 3 supports Python 3.10 and 3.12 on Windows and Ubuntu in
CI. Python 3.11 remains supported by the declared `>=3.10` package metadata and
is exercised during local release preparation.

## Reproducible source/tool environment

`pyproject.toml` is the dependency source of truth and `uv.lock` is the
cross-platform resolution lock. Release checks use uv 0.11.x and must run with
`--frozen`; a release PR that changes dependency declarations must intentionally
regenerate and review `uv.lock`.

```powershell
uv lock
uv sync --frozen --group release
uv run --frozen --group release python -m unittest discover -s tests
```

The core package deliberately has a small dependency surface. Supported ranges
have upper bounds to prevent an unreviewed major-version jump. The release lock
records exact transitive versions used by CI and audit tooling.

## GPU/runtime environment

The `generate` extra constrains compatible major lines for PyTorch, torchaudio,
and `huggingface-hub`, but CUDA/ROCm/CPU wheel selection is platform-specific.
Users must follow the current PyTorch installation selector for their hardware.
A GPU installation that overrides indexes or locked wheels is a separately
recorded environment and must be tested with `legends-sa3 doctor` and a short,
authorized generation before release claims are made.

The external `stable_audio_3` runtime and gated model weights are not silently
installed or locked as project assets. Their reviewed revision/model identity
must be recorded in generation receipts.

## SBOM, vulnerability, and license checks

Release CI and `scripts/release_checks.py` provide the local content gate. The
release tool group generates:

```powershell
uv export --frozen --all-extras --group release --no-emit-project --no-hashes --output-file audit-requirements.txt
uv run --frozen --group release pip-audit --requirement audit-requirements.txt --no-deps --progress-spinner off
uv run --frozen --group release pip-audit --requirement audit-requirements.txt --no-deps --format cyclonedx-json --output sbom.cdx.json
uv run --frozen --group release pip-licenses --format=json --output-file dependency-licenses.json
python scripts/check_dependency_licenses.py dependency-licenses.json
```

The generated reports are CI/release artifacts, not hand-maintained source. A
clean report is evidence about the exact resolution at that time, not a promise
that dependencies or third-party services are permanently vulnerability-free.

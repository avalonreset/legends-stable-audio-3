# Public release checklist

## Legal, identity, and target gates

- Confirm every active product reference says **Legends Stable Audio 3** and
  every public URL uses
  `https://github.com/avalonreset/legends-stable-audio-3`.
- Confirm `LICENSE` matches the unmodified Apache-2.0 text, PEP 639 metadata says
  `Apache-2.0`, and `NOTICE`, contribution terms, third-party notices, citation,
  release notes, and asset provenance agree.
- Reconfirm the owner has authority to license all project-owned source and the
  current banner under Apache-2.0 and has reviewed the compatibility/trademark
  statement. Do not treat dependency terms as the project source license.
- Keep historical private-preview notes clearly labeled. Export one clean
  public snapshot; do not publish the private repository history.
- Do not create/change a repository, remote, visibility, tag, release, or package
  without separate explicit authorization.

## Security and GitHub target gates

- Run Gitleaks and the forbidden-artifact/secret checks against the final source
  snapshot and history selected for publication.
- Enable private vulnerability reporting and prove that
  `https://github.com/avalonreset/legends-stable-audio-3/security/advisories/new`
  accepts a draft before visibility changes.
- Enable the dependency graph, Dependabot alerts/security updates, secret
  scanning, push protection, and code scanning when the target/account supports
  them.
- Protect `main` with required pull requests, required green CI, conversation
  resolution, no force pushes/deletions, and tightly controlled bypass.
- Verify pinned action SHAs and `permissions: contents: read` in CI.

## Skill distribution

- Edit only `skills/legends-stable-audio-3` as the canonical skill source.
- Run `python scripts/sync_skill_adapters.py --sync`, then run it without flags
  and require `skill package: ok`.
- Confirm the repo-only `.agents/` and `.claude/` mirrors and the packaged bundle
  are byte-identical to the canonical source.
- From a clean package install, run `legends-sa3 skill validate` and
  `legends-sa3 skill install --target <temporary-directory>`.
- Confirm installers require an explicit target, refuse overwrite, and never
  infer global Codex, Grok, Claude, or Gemini locations.

## Code, source export, and build

```powershell
$env:PYTHONPATH = "$PWD\src"
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m unittest discover -s tests
python -m legends_sa3 plan --hours 10 --vram-gb 24 --crossfade 12
python scripts\sync_skill_adapters.py
python scripts\release_checks.py
python scripts\export_public_source.py --output <new-empty-sibling-directory>
uv run --frozen --group release ruff check src tests scripts
uv lock --check
uv build --sdist --wheel
python scripts\release_checks.py --dist dist
python scripts\verify_clean_install.py --dist dist
git diff --check
```

- Require all tests, including the Git-less source-export test, to pass without
  repository metadata.
- Create the public repository from the validated Git-less export, not from the
  private remote or its history. The exporter refuses an existing target and
  reruns skill and release validation inside the new snapshot.
- Inspect both sdist and wheel. Require LICENSE, NOTICE, third-party notices, and
  the bundled skill; reject model/adapter/audio/local-state artifacts.
- Confirm the 10-hour plan remains 98 tracks and 36,076 final seconds.
- On an authorized clean machine, test gated model download only after the user
  accepts current terms; run one short generation without publishing weights.

## Underfit and dependency checks

- Confirm Underfit remains pinned to
  `8a96800a58c0e8b82327fc04ac31c473ed900b73` and verify origin, exact commit,
  required files, and license hash before any script runs.
- Re-review the pinned Underfit installer effects before release. Its opt-in
  setup may bootstrap tools, install dependencies, clone runtime code, and
  download large/gated model packs.
- Run the frozen release lock, dependency audit, CycloneDX SBOM generation, and
  license check documented in `docs/dependency-policy.md`.
- Review any unresolved, copyleft, or changed license manually; retain exact
  reports with the internal release receipt.

## Public/private boundary

- Include no model weights, adapter weights, datasets, generated private media,
  secrets, `.env` files, caches, local state, or machine-specific private paths.
- Confirm model/source/hosted-service/adapter/dataset/generated-output terms are
  visibly separate from Apache-2.0 project-owned source.
- Confirm no release example or manifest contains private paths or token values.
- Attach only audited source/wheel artifacts, hashes, SBOM, notices, and
  provenance after explicit release authorization.

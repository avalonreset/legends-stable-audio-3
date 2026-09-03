# Changelog

All notable changes to `legends-stable-audio-3` will be documented here.

## Unreleased

### Added

- Added guarded Stable Audio 3 Large REST planning and execution for
  text-to-audio, audio-to-audio, and inpaint, including asynchronous polling,
  atomic download, SHA-256, and secret-free receipts.
- Added a portable live-schema reference covering exact endpoints, parameters,
  paid-action gates, result handling, and web/API/DAW boundaries.
- Added interrupted-job recovery through `large result`, immediate pending
  receipts, upload preflight, response validation, public-safe file names, and
  overwrite protection for hosted Large operations.

## 0.4.0 - 2026-09-02

### Added

- Added a canonical cross-platform skill package with generated Agent Skills and
  Claude mirrors, Codex/Grok/Claude/Gemini adapters, UI metadata, and deterministic
  sync/validation tooling.
- Added release-boundary checks for stale private positioning, token-shaped
  secrets, and forbidden model, adapter, and audio artifacts.
- Refreshed the repository banner to use the public `Legends Stable Audio 3`
  name without the retired point-oh suffix.
- Added least-privilege Windows and Ubuntu CI, release-content validation,
  clean sdist/wheel installation checks, secret scanning, dependency auditing,
  and SBOM/license-report generation.
- Added package-installed `legends-sa3 skill validate/install` commands and
  included the canonical skill bundle in built artifacts.
- Added security, support, citation, ownership, Dependabot, NOTICE, and asset
  provenance surfaces for the first public release.

### Changed

- Renamed the public project/repository target to `legends-stable-audio-3`.
- Licensed project-owned source and the current project-owned banner under
  Apache License 2.0, with PEP 639 metadata and explicit non-affiliation terms.
- Added the evidence-backed source-license record and kept model
  weights, hosted services, gated terms, datasets, adapters, and third-party
  components outside the project source-license scope.
- Updated the Stable Audio 3 operating skill for the prompting, adapter, hosted
  generation, receipt, and long-mix guidance recovered in the current worktree.
- Pinned Underfit to reviewed commit
  `8a96800a58c0e8b82327fc04ac31c473ed900b73` and required origin, commit,
  required-file, and license-hash verification before execution.
- Made source-export validation independent of Git metadata.

## 0.3.0 - 2026-06-07

### Added

- Added prompt-first generation with `--style` / `--prompt` for free-form Stable
  Audio requests.
- Added `legends-sa3 prompt` to preview expanded prompts before spending GPU
  time.
- Added `legends-sa3 analyze` to inspect generated source tracks for quiet heads,
  quiet tails, active-cue trims, and JSON reporting before mixing.
- Added `--negative-prompt`, `--allow-vocals`, and `--bpm` controls.
- Added a dedicated source-informed prompting guide.

### Changed

- Repositioned built-in presets as optional recipes instead of the primary user
  interface.
- Kept `--genre` as a compatibility alias for `--recipe`.
- Updated Codex, Claude, Gemini, and portable skill instructions around the new
  prompt-first workflow.

## 0.2.0 - 2026-06-07

### Added

- Added default `active-cue` mix policy for generated long masters.
- Added per-track cue analysis for quiet heads, near-silent tails, active cue
  starts, trim seconds, and manifest warnings.
- Added `--mix-policy`, `--quality-gate`, `--cue-threshold-db`,
  `--silence-threshold-db`, and `--cue-padding-seconds` CLI controls.
- Added synthetic tests for trimming generated dead air and rejecting all-silent
  tracks.

### Changed

- Reframed the project as an agentic Stable Audio 3 operator instead of only a
  long-form instrumental music factory.
- Clarified that crossfaded long-duration mixes are one workflow built from
  multiple bounded Stable Audio generations.
- Added a dedicated `trip-hop-trance` prompt preset for more driving, less chill
  generations.
- Kept `--mix-policy strict` available for exact raw-boundary crossfades.

## 0.1.1 - 2026-06-06

### Changed

- Marked the wrapper repository under the private-preview proprietary policy
  that applied at the time.
- Replaced MIT metadata with proprietary license language.
- Updated agent and release docs to keep wrapper redistribution rights separate
  from Stable Audio model and output terms.

## 0.1.0 - 2026-06-06

Initial preview release.

### Added

- Python CLI with `doctor`, `download-model`, `plan`, `generate`, and `mix`.
- VRAM-aware segment planning.
- Stable Audio 3 Medium runtime adapter.
- Gated Hugging Face model download helper.
- Lo-fi study prompt preset.
- Resumable MP3 track generation.
- Streaming crossfade mixer for long MP3 masters.
- Codex `AGENTS.md`.
- Claude skill wrapper.
- Gemini CLI extension wrapper.
- Documentation for setup, model access, VRAM, music factory workflow, and troubleshooting.
- Unit tests and a synthetic mixer test.

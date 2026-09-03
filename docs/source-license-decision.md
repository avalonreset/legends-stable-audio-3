# Source license record: Apache-2.0

> This analysis is automated compliance assistance, not legal advice.
> Always verify licensing decisions with your own due diligence.
> For complex or high-stakes situations, consult a qualified attorney.

## Recorded decision

On 2026-09-02, the founder selected Apache License 2.0 for all project-owned
Legends Stable Audio 3 source and the current project-owned banner/assets. The
complete unmodified license text is in `LICENSE`; attribution is in `NOTICE`;
asset provenance is in `assets/PROVENANCE.md`.

Apache-2.0 was selected for its permissive redistribution terms, express
contributor patent grant, and patent-litigation termination. Contributions
intentionally submitted for inclusion are accepted under Apache-2.0 unless
explicitly stated otherwise, consistent with Section 5.

## Scope

The project license covers project-owned source, documentation, tests, scripts,
skill files, configuration, and designated assets. It does not relicense:

- Stability AI model weights, hosted services, or gated model terms;
- Gemma components or terms;
- datasets, trained adapters, or generated media;
- external Stable Audio 3 or Underfit source;
- Python/system dependencies or other third-party components.

Those items retain their own licenses and terms. They are dependencies and local
user artifacts, not Apache-2.0 project assets. See `THIRD_PARTY_NOTICES.md` and
`docs/commercial-use-and-license.md`.

## Rights and provenance record

The pre-public audit found one author identity across the existing commits and
no vendored source, model weights, adapters, datasets, or generated audio in the
candidate tree. Git authorship alone is not proof of employer, contractor,
copyright, or patent authority; the founder's decision is the implementation
authority for this source candidate, while legal due diligence remains the
owner's responsibility.

The current banner was created through AI-assisted transformation during this
release-preparation work and has been designated project-owned and Apache-2.0.
Its public provenance statement does not claim Stability AI endorsement.

## Dependency audit record

The direct and optional dependencies examined for the source candidate use
permissive license families compatible with Apache-2.0 in ordinary dependency
use. The optional Underfit bridge is pinned to reviewed commit
`8a96800a58c0e8b82327fc04ac31c473ed900b73`; its MIT license and downloaded
installer effects are documented separately. Release automation must regenerate
an exact SBOM, vulnerability report, and dependency-license report from the
release constraints before publication.

## Compatibility and marks

Legends Stable Audio 3 is an independent compatibility project. It is not
affiliated with, sponsored by, or endorsed by Stability AI. Stability AI,
Stable Audio, and related names and marks remain the property of their
respective owners and are used only to identify compatibility. Apache-2.0 does
not grant rights in those third-party marks.

## Authoritative references

- Apache License 2.0 text:
  `https://www.apache.org/licenses/LICENSE-2.0.txt`
- Applying Apache-2.0:
  `https://www.apache.org/legal/apply-license`
- Stable Audio 3 source license:
  `https://github.com/Stability-AI/stable-audio-3/blob/main/LICENSE`
- Stable Audio 3 Medium model card:
  `https://huggingface.co/stabilityai/stable-audio-3-medium`
- Underfit reviewed source:
  `https://github.com/dada-bots/underfit/tree/8a96800a58c0e8b82327fc04ac31c473ed900b73`

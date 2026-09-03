# Agent compatibility

Legends Stable Audio 3 keeps one canonical skill package at
`skills/legends-stable-audio-3`. The package uses a `SKILL.md` entrypoint and
optional `agents/openai.yaml` UI metadata. Platform files are adapters or
generated mirrors; they are not independent sources of operating truth.

## Distribution map

| Runtime | Repository surface | Role |
|---|---|---|
| Codex | `AGENTS.md`, `.agents/skills/legends-stable-audio-3/` | Project policy plus repo-only generated Agent Skills mirror |
| Grok | `GROK.md`, canonical Agent Skills package | Explicit project context; automatic discovery depends on the active client |
| Claude Code | `CLAUDE.md`, `.claude/skills/legends-stable-audio-3/` | Project policy plus repo-only generated skill mirror |
| Gemini CLI | `GEMINI.md`, `gemini-extension.json` | Extension context routed to the canonical skill |

Do not claim automatic discovery for a client until its live version and
configuration prove it. All four surfaces still share the same safe workflow
when the repository instructions are loaded.
The canonical package includes the exact guarded Large REST workflow, so no
runtime-specific adapter must reinvent API parameters or paid-action policy.

## Synchronize and validate

Edit only the canonical package, then run:

```powershell
python scripts\sync_skill_adapters.py --sync
python scripts\sync_skill_adapters.py
```

The validator checks frontmatter, UI metadata, byte-identical generated mirrors,
adapter routing, stale release language, token-shaped secrets, and forbidden
model/audio artifacts in the candidate release tree.

The mapping is declared in `skill-package.json`, so a new runtime adapter can be
added without duplicating the canonical operating guide.

## Install targets

For a client that accepts a directory of Agent Skills, copy the canonical
package into its configured skills directory:

```powershell
python scripts\sync_skill_adapters.py --install-target <skills-directory>
```

This creates `<skills-directory>/legends-stable-audio-3/`. The command does not
modify global client configuration or infer where a particular client stores
skills.

The built Python package contains the same generated bundle. After `pip install`,
validate and install it without a repository checkout:

```powershell
legends-sa3 skill validate
legends-sa3 skill install --target <skills-directory>
```

Installation refuses to replace an existing skill folder. The `.agents/` and
`.claude/` copies are repository-only mirrors for source-checkout integrations;
the canonical source remains `skills/legends-stable-audio-3`.

Gemini CLI can use the repository as an extension through
`gemini-extension.json`; its `GEMINI.md` context routes the agent to the same
canonical package.

## Public release boundary

Project-owned source, documentation, tests, and designated assets are licensed
under Apache-2.0. Model weights, adapter weights, datasets, hosted services,
generated media, secrets, private paths/content, and third-party components are
outside that grant and are never part of this skill package. Legends Stable
Audio 3 is an independent compatibility project and is not affiliated with,
sponsored by, or endorsed by Stability AI.

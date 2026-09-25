# Agent compatibility

`cto-legends` is the only registered skill. This repo vendors a pinned copy
at `skills/cto-legends/SKILL.md` and registers no per-module skill: there are
no `skills/legends-stable-audio-3` sources, no `.agents/skills` or
`.claude/skills` mirrors, and no `CLAUDE.md`, `GEMINI.md`, `GROK.md`, or
`gemini-extension.json` shims.

The installable Python package still ships its operating bundle
(`legends-sa3 skill validate` / `legends-sa3 skill install --target
<skills-directory>`), which carries the `SKILL.md` entrypoint, optional
`agents/openai.yaml` UI metadata, and the `references/` library.

Do not claim automatic discovery for a client until its live version and
configuration prove it. All agent integrations still share the same safe workflow
when the repository instructions are loaded.
The bundle includes the exact guarded Large REST workflow, so no
runtime-specific adapter must reinvent API parameters or paid-action policy.

## Install targets

For a client that accepts a directory of Agent Skills, install the operating
bundle into its configured skills directory:

```powershell
legends-sa3 skill validate
legends-sa3 skill install --target <skills-directory>
```

This creates `<skills-directory>/legends-stable-audio-3/`. The command does not
modify global client configuration or infer where a particular client stores
skills. Installation refuses to replace an existing skill folder.

## Public release boundary

Project-owned source, documentation, tests, and designated assets are licensed
under Apache-2.0. Model weights, adapter weights, datasets, hosted services,
generated media, secrets, private paths/content, and third-party components are
outside that grant and are never part of this skill package. Legends Stable
Audio 3 is an independent compatibility project and is not affiliated with,
sponsored by, or endorsed by Stability AI.

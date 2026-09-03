# Claude Guide

Load the generated Claude skill at
`.claude/skills/legends-stable-audio-3/SKILL.md` for Stable Audio 3 setup,
prompting, generation, adapters, benchmarking, mixing, or troubleshooting. Its
canonical source is `skills/legends-stable-audio-3/SKILL.md`.

Do not hand-edit the generated mirror. Update the canonical package, then run
`python scripts/sync_skill_adapters.py --sync` and the validator.

Non-negotiable gates:

- Never package model weights, adapter weights, secrets, private generated
  media, local state, or private organization paths/content.
- Never bypass Stability AI or Hugging Face terms.
- Confirm scope and verify live price, balance, and product identity before paid
  generation.
- Project-owned source and designated assets are licensed under Apache-2.0.
  Models, weights, adapters, datasets, generated media, hosted services, and
  third-party components retain separate terms.
- Treat this as an independent compatibility project; do not claim Stability AI
  affiliation, sponsorship, or endorsement.

# Gemini Guide

This extension routes Stable Audio 3 work to the canonical cross-platform skill
at `skills/legends-stable-audio-3/SKILL.md`. Read that skill before setup,
prompting, generation, adapters, hosted benchmarks, web-studio work, mixing, or
troubleshooting. Do not restate separate Gemini-only operating defaults here.

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

After canonical skill edits, run `python scripts/sync_skill_adapters.py --sync`
and `python scripts/sync_skill_adapters.py` before handoff.

# Portable mastery evaluation

Use these scenarios as regression cases for an agent that has only this skill
folder. Passing means the agent routes the correct surface, applies the relevant
operating rules, states evidence limits, and avoids unsafe side effects.

1. **Local instrumental:** uses Medium, positive music/instrumental tags, 8
   Ping-Pong steps, CFG 1.0, and a prompt/seed tournament.
2. **Paid higher tier:** chooses Large REST, verifies price/pool/limits live,
   states expected maximum cost, and asks before spending.
3. **Web stems:** chooses web Multi-Track, explains synchronized lanes, and does
   not call it Large without displayed proof.
4. **Existing tracks:** routes directly to mixer/DAW rather than regenerating.
5. **Free-time drone:** deliberately omits BPM and records free-time intent.
6. **Rhythmic cue:** fixes a tempo thesis within a family and assesses actual
   straight/half/double-time behavior and drift.
7. **Medium selection:** compares at least 3-4 prompt families and four short
   seeds per family before long generation.
8. **Large duration:** starts with 120-second canaries, runs a controlled
   multi-seed duration tournament, and treats 380 seconds as a ceiling.
9. **Sound effect:** uses `TrackType: SFX`, names one event/attack/decay, omits
   rhythmic bed and automatic BPM, compares seeds, then trims after selection.
10. **Spoken-word bed:** specifies sparse midrange and restrained lead activity
    after the musical brief instead of relying on `background music` alone.
11. **Medium/Large A/B:** freezes the contract, uses blind listening, and states
    that equal seed integers do not prove equal latent noise.
12. **Repeated style miss:** exhausts prompt families and seeds before proposing
    a rights-cleared native LoRA; keeps weights out of the package.
13. **Ten-hour master:** preserves sources, uses active-cue analysis and
    streaming crossfades, chooses overlap by bars/phrases, and verifies delivery.
14. **Release audit:** identifies Apache-2.0 source licensing while keeping
    models, adapters, secrets, and third-party dependencies separately licensed.
15. **Web repair:** keeps a good Multi-Track session, regenerates only the bad
    lane or replaces the bad time range, distinguishes generative credit actions
    from free edits/effects, and exports MIXDOWN versus STEMS correctly.
16. **Interrupted Large job:** uses the generation ID and `large result` to
    recover without another POST; bounded retries apply only to result GETs,
    existing files remain protected, and the receipt contains no secret or
    private absolute path.

Automated distribution checks must also prove that every local Markdown link
resolves inside the installed skill and that the package contains no private
machine paths, Empire references, Obsidian wiki links, token-shaped secrets,
model/adapter weights, or generated audio.

# Prompt mastery

This is the portable operating playbook for prompt design and selection. It is
shipped with the skill so no private vault is required.

## Route before prompting

- **Local Medium:** local, inspectable inference; inexpensive seed search after
  setup; resumable batches; native adapters.
- **Hosted Large REST:** paid higher-tier generation through model ID
  `stable-audio-3`; asynchronous results; no web-studio lanes or DSP.
- **Web studio / ST-1:** interactive Full Mix or synchronized Multi-Track work.
  Preserve the displayed model label; do not infer that it is Large.
- **Mixer or DAW:** selection, cue trimming, tempo alignment, transitions,
  loudness, and export after generation.

## Music prompt anatomy

Start instrumental music with:

```text
TrackType: Music, VocalType: Instrumental,
Genre: [primary], Genre: [secondary], [exact BPM] BPM,
Instruments: [lead, harmony, bass, percussion],
[rhythm and performance behavior], [mood and energy],
[arrangement movement], [production character and space],
[role in the production]
```

Treat tags as routing and prose as composition direction. Give instruments
behaviors: what enters, holds, develops, strips back, returns, or ends. Put the
production role last. Prefer describable sonic attributes to artist imitation.
Avoid adjective soup, contradictory genres, unsupported weighted-token syntax,
rigid timestamp scripts, and changing several experimental variables at once.

For a spoken-word bed, describe the music first and then request sparse
midrange, restrained lead activity, controlled transients, and an arrangement
that leaves room for narration. Do not use `background music` as the whole
brief.

## BPM decision

For rhythmic music, write a tempo thesis, select one exact BPM, keep it fixed
inside a prompt/seed family, and assess the render for straight, half-time,
double-time, or drift. The prompt number is conditioning, not proof of an exact
grid. Reject or align downstream when necessary.

For intentionally free-time ambience, drone, or SFX, omit BPM deliberately.
The CLI supports `--omit-bpm`; SFX prompts suppress automatic BPM by default.
Record the omission rather than inventing a tempo.

## Local Medium tournament

Default the post-trained Medium checkpoint to 8 Ping-Pong steps and CFG 1.0.
At CFG 1.0, the reviewed sampler does not apply the negative prompt.

1. Write 3-4 prompt families: literal metadata, scene/context, production
   character, and role/restraint.
2. Generate at least four 45-90 second seeds per family.
3. Keep prompt fixed while testing seeds; keep seed fixed while testing wording.
4. Review blind for musicality, adherence, role fit, negative space, repetition,
   vocal-like texture, and technical artifacts.
5. Promote only the winning family and adjacent seed neighborhood.
6. Choose long-source duration after the sound is approved.

If unwanted content repeats at CFG 1.0, strengthen positive modality and
arrangement language and test more seeds first. Any higher-CFG negative-prompt
test is a controlled experiment, not an automatic quality upgrade.

## Hosted Large duration tournament

Current first-party documentation supports 1-380 second requests, 4-8 steps,
CFG 1-25, WAV or MP3 output, asynchronous retrieval, and a fixed 190-second
duration when the field is omitted. Verify these mutable facts live before a
paid run.

Use 120-second complete-song canaries. Official evaluation evidence is strongest
around 120-190 seconds; 380 seconds is a ceiling, and the longest generations
can lose prompt adherence or drift toward ambient/classical material.

1. Compare 3-4 prompt families with at least three 120-second seeds each.
2. Promote one family.
3. Test three nearby durations with the same prompt, BPM, steps, CFG, and at
   least three requested seeds per duration.
4. Choose the shortest range that repeatedly creates a complete arc.
5. Shorten when extra time creates repetition, dead air, or drift.

Starting hypotheses, not vendor guarantees: dense DnB/digital hardcore
120-160s; breakbeat/industrial 135-180s; trip-hop 150-190s; trance 165-210s;
minimal/cinematic electronic 180-240s; ambient/drone/classical 210-320s.

For a 14:09.452 program, start with five 175-190 second sources or six 145-170
second sources. Use more/shorter sources for dense genres and fewer/longer
sources for spacious genres.

## Sound effects

Use:

```text
TrackType: SFX, VocalType: None, [one named event],
[material or environment], [attack], [decay], one-shot, sparse,
no rhythmic bed
```

Generate several seeds. Preserve the raw render, select the clean event, then
trim and synchronize it editorially. Do not ship an entire generated clip as a
finished UI or video effect, and do not let SFX become a constant layer.

## Failure triage

- Wrong genre/mood: change one prompt-family variable or seed.
- Crowded under speech: reduce instruments, lead density, and midrange activity.
- Vocal-like material at CFG 1.0: strengthen positive instrumental routing and
  search seeds; do not claim the negative prompt protected the output.
- Repetition or bland drift: shorten sources and assemble selected sections.
- Static, buzz, silence, collapse: inspect runtime, precision, attention backend,
  model integrity, and seed before endlessly rewriting prose.
- BPM miss: assess half/double-time and drift, then reject or align downstream.


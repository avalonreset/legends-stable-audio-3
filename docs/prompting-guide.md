# Prompting Guide

Legends Stable Audio 3 is prompt-first. Recipes exist as optional scaffolds,
but users should usually start with the sound they want:

```powershell
legends-sa3 prompt `
  --style "trance hip hop jazz, smoky saxophone, broken beat drums, 104 BPM" `
  --count 3
```

Then generate when the prompt shape looks right:

```powershell
legends-sa3 generate `
  --model-dir .\models\stable-audio-3-medium `
  --stable-audio-repo ..\stable-audio-3 `
  --style "trance hip hop jazz, smoky saxophone, broken beat drums, 104 BPM" `
  --minutes 6 `
  --vram-gb 24 `
  --output .\output\trance-hip-hop-jazz
```

## What Stable Audio 3 Wants

Stability AI's prompt guide recommends prompts that line up with music metadata:
genre, instruments, mood or energy, and BPM. It also notes that Stable Audio 3
was trained from Freesound and AudioSparx-style descriptions, so prompts that
look like clear audio metadata tend to behave better than vague requests.

Stable Audio 3 is not a lyric-to-song model. Its official prompt guide says the
models do not output intelligible vocals, and the model overview says Stable
Audio 3 is not designed for speech or voice generation. Treat vocal prompts as
experiments with vocal-like texture, not as a reliable clean-vocal or lyric
workflow.

Useful fields:

- `TrackType: Music`
- `VocalType: Instrumental`
- `Genre: Jazz, Genre: Hip Hop`
- `Instruments: Saxophone, Rhodes, Bass, Drums`
- `104 BPM`
- Production notes such as `warm tape saturation`, `wide stereo image`, or
  `controlled low end`

## Practical Formula

Use this shape for most music prompts:

```text
TrackType: Music, VocalType: Instrumental, Genre: [primary], Genre: [secondary],
[BPM] BPM, Instruments: [main instruments], [rhythm and performance language],
[mood and energy], [arrangement prose], [production era or context]
```

Treat the tags as routing metadata and the prose as the musical direction. Do
not rely on a formal timeline grammar such as `[Intro]` or `[Drop]`; describe
the movement in ordinary musical language instead.

Examples:

```text
TrackType: Music, VocalType: Instrumental, trance hip hop jazz, smoky saxophone,
broken beat drums, deep sub bass, hypnotic club energy, wide stereo image, 104 BPM
```

```text
TrackType: Music, VocalType: Instrumental, cinematic gospel house, live piano,
pumping four-on-the-floor drums, emotional synth lead, euphoric final-track mood,
124 BPM
```

```text
TrackType: Music, VocalType: Instrumental, industrial ambient dub, metallic
percussion, low sub pressure, foggy warehouse atmosphere, slow evolving texture,
88 BPM
```

For a spoken-word bed, explicitly request musical space instead of relying on
mix instructions alone:

```text
TrackType: Music, VocalType: Instrumental, Genre: Goa Trance, Genre:
Psychedelic Trance, 138 BPM, Instruments: rolling offbeat bass, hypnotic 303
acid arpeggios, crisp four-on-the-floor kick, emotional minor-key analog lead,
restrained percussion, long evolving tension, luminous melancholy late-night
energy, continuous forward motion with smooth transitions, a spacious
instrumental arrangement leaving room for an intimate spoken monologue
```

## Prompt Tournament

Do not spend a full six-minute generation on the first wording. Use a canary
tournament:

1. Write three or four prompt families: literal metadata, scene/context,
   production-era, and role/restraint.
2. Generate `45-90s` canaries at `8` steps and `cfg_scale=1.0`, using at least
   four seeds per family.
3. Review blind for musicality, prompt adherence, voiceover space, unwanted
   vocal texture, repetition, and technical artifacts.
4. Promote only the winning prompt and seed neighborhood to longer sources.
5. Assemble long programs from approved sources with active-cue transitions.

Keep the prompt fixed while testing seeds. Keep the seed fixed while comparing
prompt wording. Changing both at once destroys the evidence.

## Genre Evidence Boundary

Stability AI does not publish a genre-by-genre inventory or distribution for
the Medium training subset. The disclosed sources are `806,284` AudioSparx
files and `472,618` Freesound files. AudioSparx supplied metadata including
genre, mood, BPM, and instrumentation, but its current public catalog is not a
reliable count of the licensed training subset.

Official examples demonstrate broad intended capability across electronic,
rock, funk, jazz, hip hop, Latin percussion, metal, lo-fi, trance, country,
blues, house, dubstep, and ambient music. Community reports most consistently
favor electronic instrumentals, ambient, synthwave, acid, trance, and retro
game-like cues. Treat that community pattern as a prompt-search prior, not as a
claim about undisclosed training proportions.

Expect weaker reliability for intelligible singing, complex song narratives,
long-range melodic development, and fully convincing acoustic or orchestral
timbres. A buzz, static wash, or single-horn failure can also be an inference
runtime problem; do not endlessly rewrite a prompt before checking the sampler,
precision, attention backend, and seed.

## Recipes Versus Styles

Use `--style` when the user has a plain-language request:

```powershell
legends-sa3 generate --style "dark garage jazz, muted trumpet, 126 BPM" ...
```

Use `--recipe` when you want a known repeatable scaffold:

```powershell
legends-sa3 generate --recipe trip-hop-trance ...
```

The old `--genre` flag still works as an alias for `--recipe`, but new workflows
should prefer `--style` or `--recipe` so the difference is clear.

## BPM Strategy

Include an exact BPM when tempo matters. Treat the number as conditioning, not
proof of a production grid: measure the render, check half-time and double-time
interpretations, and reject or align drift downstream. Omit BPM intentionally
for free-time ambience, drone, or effects instead of leaving it ambiguous.

Keep BPM fixed while comparing prompt families or seeds. For beat-matched
programs, choose crossfades in bars and phrase boundaries after measuring the
approved sources; a fixed 12-second overlap is only a local starting point for
non-beat-critical beds.

## Sound Effects

Start single-event effects with:

```text
TrackType: SFX, VocalType: None, [one named event], [material or
timbre], [attack], [decay], [intensity], [space or device context], one-shot,
sparse, no rhythmic bed
```

Generate multiple seeds, preserve the raw render, then trim the clean event and
tail to the editorial need. Select for attack clarity, decay quality, absence of
embedded music or speech, and fit against picture. At CFG 1.0, put role controls
such as `one-shot`, `sparse`, and `no rhythmic bed` in the positive prompt rather
than claiming a negative prompt is active.

## Duration

Stable Audio 3 Medium can generate up to about `380s`, but the best duration is
the one that fits the prompt. A short SFX prompt should not be stretched to six
minutes. For long background music, generate several coherent source tracks and
assemble them with `active-cue` crossfades.

Use shorter canaries to discover the sound. Longer is not automatically better:
repetition and bland development become easier to hear as duration increases.

## Steps And CFG

The post-trained Stable Audio 3 Medium checkpoint is designed for eight-step
Ping-Pong sampling with guidance already internalized during post-training.
This wrapper therefore defaults to `cfg_scale=1.0` and `steps=8`. Going above
eight steps does not necessarily improve this checkpoint. If a prompt is weak,
improve the prompt and explore seeds before adding steps.

## Negative Prompts

By default, Legends Stable Audio 3 requests instrumental music positively with
`TrackType: Music, VocalType: Instrumental`. This is the primary control at the
default `cfg_scale=1.0`.

The wrapper also keeps an instrumental negative-prompt recipe for experiments
with `--cfg-scale` above `1.0`:

```text
vocals, singing, rapping, spoken words, voice, lyrics, crowd noise, harsh
distortion, clipping, sudden genre switch, jarring transition
```

Use `--allow-vocals` only when you do not want that instrumental bias. It does
not make Stable Audio 3 sing written lyrics. It only stops this wrapper from
suppressing vocal-like textures.

Important: a negative prompt is inactive at `cfg_scale=1.0`. The manifest now
records both the requested negative prompt and whether it was actually applied.

If testing negative guidance deliberately, compare the same prompt and seed at
`cfg_scale=1.0` and a small non-default CFG value. Treat that as an experiment,
not an upgrade path: Medium was post-trained not to require CFG, and a higher
number is not evidence of higher quality.

For user-facing release examples, prefer instrumental prompts unless the example
is explicitly showing the vocal limitation.

Use `--negative-prompt` to override the default entirely.

## Audio-To-Audio And LoRA

When text prompting repeatedly misses a specific groove, use audio-to-audio
with an owned or licensed structural reference. Noise levels around `0.4-0.6`
are the official starting range: lower values preserve more of the reference;
`1.0` behaves like pure noise. Inpainting and continuation work best when the
requested change is plausible beside the supplied context.

LoRA is the next escalation only after a repeatable prompt gap is proven across
multiple seeds. Use a clean, rights-cleared, stylistically coherent dataset;
do not fine-tune merely to avoid curating generations.

## Anti-Patterns

- adjective soup without a concrete genre, rhythm, instrument, or BPM
- mutually contradictory subgenres and energy directions
- artist imitation instead of describable musical attributes
- asking for written lyrics or reliable speech
- assuming more steps, higher CFG, or maximum duration means better music
- changing prompt, seed, duration, and sampler simultaneously
- letting utility language such as `background music` replace the actual
  composition brief

## Long Mix Quality

Before mixing, inspect the generated source tracks:

```powershell
legends-sa3 analyze `
  --input-dir .\output\my-run\tracks_mp3 `
  --json-output .\output\my-run\track-analysis.json
```

Then mix with the default active-cue policy:

```powershell
legends-sa3 mix `
  --input-dir .\output\my-run\tracks_mp3 `
  --output .\output\my-run\master.mp3 `
  --crossfade 16 `
  --mix-policy active-cue
```

Use `--quality-gate fail` when you want the run to stop before rendering if a
source track has quiet-head or quiet-tail warnings.

## Source Notes

- Stability AI Stable Audio 3 prompt guide:
  `https://github.com/Stability-AI/stable-audio-3/blob/main/docs/guides/prompting.md`
- Stability AI Stable Audio 3 inference controls:
  `https://github.com/Stability-AI/stable-audio-3/blob/main/docs/workflows/inference.md`
- Stable Audio 3 Medium model card:
  `https://huggingface.co/stabilityai/stable-audio-3-medium`
- Stable Audio 3 technical report:
  `https://arxiv.org/html/2605.17991`

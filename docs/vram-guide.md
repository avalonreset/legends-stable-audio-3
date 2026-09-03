# VRAM guide

Stable Audio 3 Medium segment length should be chosen from the user's GPU memory.
Longer segments are more convenient, but lower VRAM users need shorter segments.

## Conservative defaults

| VRAM | Starting segment length | Notes |
| --- | ---: | --- |
| 24 GB class | 380s | Validated on RTX 4090. Cards may report around 23.99 GB. |
| 20 GB | 300s | Conservative high-end setting. |
| 16 GB | 240s | Good first target for common enthusiast cards. |
| 12 GB | 180s | Safer for midrange cards. |
| 8 GB | 120s | Start here and increase only after testing. |
| Below 8 GB | 75s or small CPU model | Medium may not be practical. |

## Formula

Final duration is:

```text
final_seconds = track_count * track_seconds - (track_count - 1) * crossfade_seconds
```

Track count is:

```text
ceil((target_seconds - crossfade_seconds) / (track_seconds - crossfade_seconds))
```

Example for ten hours on 24 GB VRAM:

```text
track_seconds = 380
crossfade_seconds = 12
track_count = 98
final_seconds = 36076
```

That produces about `10:01:16`.

## Sweet spot testing protocol

1. Run `legends-sa3 doctor` to detect GPU and VRAM.
2. Generate one test track at the recommended length.
3. If it succeeds with comfortable VRAM headroom, try the next higher bracket.
4. If it fails, reduce segment length by 30 to 60 seconds.
5. Keep steps and CFG constant while testing length.

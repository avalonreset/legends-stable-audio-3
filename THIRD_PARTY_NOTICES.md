# Third-Party Notices

## Underfit

Project: `dada-bots/underfit`

Source: `https://github.com/dada-bots/underfit`

License: MIT

Reviewed revision: `8a96800a58c0e8b82327fc04ac31c473ed900b73`

Verified license SHA-256:
`073a815ba79b8f629ef29f6a0699c14233fe18ae40daea8245941bb410bc8a09`

Legends Stable Audio 3 can install and launch Underfit as an optional local
LoRA Studio for Stable Audio 3 adapter training. The Underfit source code is not
Stable Audio model weight data. Stable Audio model files and user-trained
adapter checkpoints remain governed by their own terms and are not bundled by
this repository.

The optional `--run-underfit-install` path executes Underfit's downloaded shell
script. At the reviewed revision it can bootstrap `uv`, synchronize Python
dependencies, and launch setup that clones runtime code or downloads large/gated
model packs. These effects occur only after explicit user opt-in.

```text
MIT License

Copyright (c) 2026 Dadabots

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Stable Audio 3 runtime and models

The external `Stability-AI/stable-audio-3` source repository is MIT licensed and
is not vendored in this distribution. Stable Audio model weights, Gemma
components, hosted services, model cards, acceptable-use policies, and gated
terms are separately licensed and are not covered by this project's
Apache-2.0 license.

## Python and system dependencies

NumPy, `huggingface-hub`, PyTorch, torchaudio, setuptools, wheel, FFmpeg, and
their transitive components retain their own licenses. Exact resolved release
versions and license metadata are recorded by the SBOM/license-check workflow;
no dependency binary is relicensed by this NOTICE.

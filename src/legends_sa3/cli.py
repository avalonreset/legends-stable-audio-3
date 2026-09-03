from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from .doctor import ffprobe_duration, run_doctor
from .hf_download import download_model
from .hosted import (
    HostedAPIError,
    LargeRequest,
    poll_large_result,
    submit_large,
    write_public_receipt,
    write_recovery_receipt,
    write_submission_receipt,
)
from .lora_studio import (
    DEFAULT_ADAPTERS_DIR,
    DEFAULT_STUDIO_DIR,
    UNDERFIT_COMMIT,
    UNDERFIT_REPO_URL,
    clone_or_update_underfit,
    import_adapter,
    list_imported_adapters,
    run_underfit_dashboard,
    run_underfit_install,
    underfit_status,
)
from .mixer import analyze_audio, decode_audio, mix_tracks
from .planning import build_mix_plan, recommend_track_seconds
from .prompts import (
    NEGATIVE_PROMPT_GENERAL,
    NEGATIVE_PROMPT_INSTRUMENTAL,
    build_prompt,
    list_presets,
    slugify_style,
)
from .sa3_runner import generate_track_batch
from .skill_distribution import bundled_skill_path, install_bundled_skill, validate_skill


def add_prompt_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--style",
        "--prompt",
        dest="style",
        help="Free-form Stable Audio style prompt, e.g. 'trance hip hop jazz, 104 BPM'",
    )
    parser.add_argument(
        "--recipe",
        "--genre",
        dest="recipe",
        choices=list_presets(),
        default=None,
        help="Optional built-in recipe scaffold. --genre is kept as a compatibility alias.",
    )
    bpm_group = parser.add_mutually_exclusive_group()
    bpm_group.add_argument("--bpm", type=int, help="Force a BPM across all generated tracks")
    bpm_group.add_argument(
        "--omit-bpm",
        action="store_true",
        help="Do not add an automatic BPM (for free-time ambience, drone, or other unmetered work)",
    )
    parser.add_argument(
        "--allow-vocals",
        action="store_true",
        help=(
            "Allow vocal-like textures by omitting the default VocalType: Instrumental "
            "positive tag. This does not create intelligible lyrics."
        ),
    )
    parser.add_argument(
        "--negative-prompt",
        help=(
            "Override the default negative prompt. Negative guidance is inactive "
            "at --cfg-scale 1.0."
        ),
    )


def add_mix_quality_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--mix-policy",
        choices=["active-cue", "strict"],
        default="active-cue",
        help="active-cue trims generated near-silence and starts incoming tracks at a usable cue",
    )
    parser.add_argument(
        "--quality-gate",
        choices=["warn", "fail", "off"],
        default="warn",
        help="warn, fail, or ignore quiet/silent cue-analysis findings before rendering",
    )
    parser.add_argument("--cue-threshold-db", type=float, default=-50.0)
    parser.add_argument("--silence-threshold-db", type=float, default=-80.0)
    parser.add_argument("--cue-padding-seconds", type=float, default=0.25)


def add_lora_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--lora-ckpt-path",
        dest="lora_ckpt_paths",
        action="append",
        help=(
            "Path to a native Stable Audio 3 LoRA or DoRA safetensors checkpoint. "
            "Repeat for multiple native adapters."
        ),
    )
    parser.add_argument(
        "--lora-strength",
        type=float,
        help="Strength for loaded native Stable Audio 3 LoRA adapters. Defaults to the runtime's native value.",
    )


def resolved_negative_prompt(args: argparse.Namespace) -> str:
    if args.negative_prompt is not None:
        return args.negative_prompt
    return NEGATIVE_PROMPT_GENERAL if args.allow_vocals else NEGATIVE_PROMPT_INSTRUMENTAL


def resolved_recipe(args: argparse.Namespace) -> str | None:
    if args.recipe:
        return args.recipe
    if args.style:
        return None
    return "lofi-study"


def cmd_doctor(_: argparse.Namespace) -> int:
    report = run_doctor()
    print(f"platform: {report.platform}")
    print(f"architecture: {report.architecture}")
    print(f"python: {report.python}")
    print(f"ffmpeg: {report.ffmpeg}")
    print(f"ffprobe: {report.ffprobe}")
    print(f"torch: {report.torch}")
    print(f"cuda: {report.cuda}")
    print(f"mps: {report.mps}")
    print(f"gpu: {report.gpu_name or 'not detected'}")
    print(f"vram_gb: {report.vram_gb if report.vram_gb is not None else 'unknown'}")
    print(f"local_medium_backend: {report.local_medium_backend}")
    if report.mps and not report.cuda:
        print("local_medium_note: Apple MPS detected, but this release uses the CPU path; use hosted Large for reliable Mac generation.")
    if report.vram_gb is not None:
        print(f"recommended_track_seconds: {recommend_track_seconds(report.vram_gb)}")
    return 0


def cmd_download_model(args: argparse.Namespace) -> int:
    path = download_model(args.model, Path(args.output))
    print(f"Downloaded model files to {path}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    track_seconds = args.track_seconds
    if track_seconds == "auto":
        track_seconds = recommend_track_seconds(args.vram_gb)
    else:
        track_seconds = int(track_seconds)
    plan = build_mix_plan(
        hours=args.hours,
        minutes=args.minutes,
        track_seconds=track_seconds,
        crossfade_seconds=args.crossfade,
    )
    print(f"target_seconds: {plan.target_seconds}")
    print(f"track_seconds: {plan.track_seconds}")
    print(f"crossfade_seconds: {plan.crossfade_seconds}")
    print(f"track_count: {plan.track_count}")
    print(f"final_seconds: {plan.final_seconds}")
    print(f"final_hours: {plan.final_hours:.3f}")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    recipe = resolved_recipe(args)
    instrumental = not args.allow_vocals
    for index in range(1, args.count + 1):
        prompt, bpm = build_prompt(
            recipe,
            index,
            style=args.style,
            custom_style=args.custom_style,
            bpm=args.bpm,
            instrumental=instrumental,
            omit_bpm=args.omit_bpm,
        )
        print(f"[{index:03d}] bpm={bpm if bpm is not None else 'omitted'}")
        print(prompt)
        print()
    print("negative_prompt:")
    print(resolved_negative_prompt(args))
    print("negative_prompt_status: inactive at the generation default cfg_scale=1.0")
    return 0


def cmd_mix(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    tracks = sorted(input_dir.glob(args.pattern))
    if not tracks:
        raise SystemExit(f"No tracks found in {input_dir} using pattern {args.pattern}")
    output = Path(args.output)
    manifest = mix_tracks(
        tracks,
        output,
        crossfade_seconds=args.crossfade,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
        mix_policy=args.mix_policy,
        quality_gate=args.quality_gate,
        cue_threshold_db=args.cue_threshold_db,
        silence_threshold_db=args.silence_threshold_db,
        cue_padding_seconds=args.cue_padding_seconds,
        manifest_path=output.with_suffix(output.suffix + ".manifest.json"),
    )
    duration = ffprobe_duration(output)
    print(f"output: {output}")
    print(f"rendered_seconds_estimate: {manifest['rendered_seconds_estimate']:.2f}")
    print(f"ffprobe_duration: {duration:.2f}")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    tracks = sorted(input_dir.glob(args.pattern))
    if not tracks:
        raise SystemExit(f"No tracks found in {input_dir} using pattern {args.pattern}")

    rows = []
    for index, track in enumerate(tracks, start=1):
        audio = decode_audio(track, args.sample_rate, args.channels)
        analysis = analyze_audio(
            track,
            audio,
            sample_rate=args.sample_rate,
            cue_threshold_db=args.cue_threshold_db,
            silence_threshold_db=args.silence_threshold_db,
            cue_padding_seconds=args.cue_padding_seconds,
        )
        row = {
            "index": index,
            "file": track.name,
            "seconds": round(analysis.input_seconds, 2),
            "head_trim_seconds": round(analysis.cue_start_sample / args.sample_rate, 2),
            "tail_trim_seconds": round(
                max(0, analysis.input_samples - analysis.cue_end_sample) / args.sample_rate,
                2,
            ),
            "leading_quiet_seconds": round(analysis.leading_quiet_seconds, 2),
            "trailing_quiet_seconds": round(analysis.trailing_quiet_seconds, 2),
            "warnings": analysis.warnings,
        }
        rows.append(row)
        status = "WARN" if analysis.warnings else "OK"
        print(
            f"[{index:03d}] {status} {track.name} "
            f"head={row['head_trim_seconds']:.2f}s tail={row['tail_trim_seconds']:.2f}s "
            f"lead_quiet={row['leading_quiet_seconds']:.2f}s trail_quiet={row['trailing_quiet_seconds']:.2f}s",
            flush=True,
        )
        for warning in analysis.warnings:
            print(f"      - {warning}", flush=True)

    if args.json_output:
        output = Path(args.json_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"tracks": rows}, indent=2), encoding="utf-8")
        print(f"json_output: {output}")

    warnings = sum(1 for row in rows if row["warnings"])
    print(f"tracks: {len(rows)}")
    print(f"warnings: {warnings}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    output = Path(args.output)
    track_seconds = args.track_seconds
    if track_seconds == "auto":
        track_seconds = recommend_track_seconds(args.vram_gb)
    else:
        track_seconds = int(track_seconds)

    plan = build_mix_plan(
        hours=args.hours,
        minutes=args.minutes,
        track_seconds=track_seconds,
        crossfade_seconds=args.crossfade,
    )
    print(
        f"Plan: {plan.track_count} tracks x {plan.track_seconds}s with "
        f"{plan.crossfade_seconds}s crossfades = {plan.final_seconds}s"
    )
    recipe = resolved_recipe(args)
    instrumental = not args.allow_vocals
    negative_prompt = resolved_negative_prompt(args)
    tracks = generate_track_batch(
        model_dir=Path(args.model_dir),
        stable_audio_repo=Path(args.stable_audio_repo) if args.stable_audio_repo else None,
        lora_ckpt_paths=[Path(path) for path in (args.lora_ckpt_paths or [])],
        lora_strength=args.lora_strength,
        output_dir=output,
        recipe=recipe,
        style=args.style,
        track_count=plan.track_count,
        track_seconds=plan.track_seconds,
        steps=args.steps,
        cfg_scale=args.cfg_scale,
        seed_base=args.seed_base,
        mp3_bitrate=args.bitrate,
        bpm=args.bpm,
        omit_bpm=args.omit_bpm,
        negative_prompt=negative_prompt,
        instrumental=instrumental,
        custom_style=args.custom_style,
    )
    label = args.style or recipe or "custom-style"
    final = output / f"{slugify_style(label)}-{plan.final_seconds}s-master.mp3"
    mix_tracks(
        tracks,
        final,
        crossfade_seconds=args.crossfade,
        bitrate=args.bitrate,
        mix_policy=args.mix_policy,
        quality_gate=args.quality_gate,
        cue_threshold_db=args.cue_threshold_db,
        silence_threshold_db=args.silence_threshold_db,
        cue_padding_seconds=args.cue_padding_seconds,
        manifest_path=final.with_suffix(final.suffix + ".manifest.json"),
    )
    print(f"final_mp3: {final}")
    return 0


def _large_request(args: argparse.Namespace) -> LargeRequest:
    return LargeRequest(
        operation=args.operation,
        prompt=args.prompt,
        duration=args.duration,
        seed=args.seed,
        steps=args.steps,
        cfg_scale=args.cfg_scale,
        output_format=args.output_format,
        audio=Path(args.audio) if args.audio else None,
        strength=args.strength,
        mask_start=args.mask_start,
        mask_end=args.mask_end,
    )


def _preflight_large_audio(request: LargeRequest) -> float | None:
    if request.audio is None:
        return None
    try:
        actual_duration = ffprobe_duration(request.audio)
    except FileNotFoundError as error:
        raise ValueError(
            "ffprobe is required to validate paid audio uploads before submission"
        ) from error
    except (RuntimeError, ValueError) as error:
        raise ValueError(f"could not validate input audio with ffprobe: {error}") from error
    if not 6 <= actual_duration <= 380:
        raise ValueError(
            f"input audio duration must be 6-380 seconds; detected {actual_duration:.3f} seconds"
        )
    if request.operation == "inpaint":
        mask_end = request.duration if request.mask_end is None else request.mask_end
        if mask_end > actual_duration:
            raise ValueError(
                f"inpaint mask_end {mask_end:g}s exceeds input audio duration {actual_duration:.3f}s"
            )
    return actual_duration


def _require_large_api_key() -> str:
    api_key = os.environ.get("STABILITY_API_KEY", "")
    if not api_key:
        raise SystemExit("STABILITY_API_KEY is required; never pass the secret on the command line.")
    return api_key


def _large_output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    output = Path(args.output).expanduser().resolve()
    if output.suffix.lower() != f".{args.output_format}":
        raise ValueError(f"output path must end in .{args.output_format}")
    receipt = (
        Path(args.receipt).expanduser().resolve()
        if args.receipt
        else Path(str(output) + ".receipt.json")
    )
    if output == receipt:
        raise ValueError("output and receipt paths must be different")
    if not args.overwrite:
        if output.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing output without --overwrite: {output}"
            )
        if receipt.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing receipt without --overwrite: {receipt}"
            )
    for target in (output, receipt):
        if target.exists() and target.is_dir():
            raise ValueError(f"file target is a directory: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".legends-sa3-write-test-"):
                pass
        except OSError as error:
            raise ValueError(f"target directory is not writable: {target.parent}: {error}") from error
    return output, receipt


def cmd_large_plan(args: argparse.Namespace) -> int:
    try:
        request = _large_request(args)
        plan = request.public_plan()
        audio_duration = _preflight_large_audio(request)
        if audio_duration is not None:
            plan["audio_duration_seconds"] = round(audio_duration, 3)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(plan, indent=2))
    return 0


def cmd_large_generate(args: argparse.Namespace) -> int:
    if not args.confirm_paid:
        raise SystemExit(
            "Refusing paid Stable Audio Large request without --confirm-paid after live price/balance verification."
        )
    api_key = _require_large_api_key()
    request = _large_request(args)
    try:
        if args.confirmed_live_credits <= 0:
            raise ValueError("--confirmed-live-credits must be greater than zero")
        request.validate()
        _preflight_large_audio(request)
        output, receipt_path = _large_output_paths(args)
        if args.poll_interval < 0 or args.request_timeout <= 0 or args.result_timeout <= 0:
            raise ValueError("poll interval must be non-negative and timeouts must be positive")
    except (FileExistsError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"confirmed_live_credits: {args.confirmed_live_credits}")
    print(f"endpoint: {request.endpoint}")
    try:
        generation_id = submit_large(request, api_key, timeout=args.request_timeout)
        print(f"generation_id: {generation_id}")
        write_submission_receipt(
            receipt_path,
            request,
            generation_id,
            confirmed_live_credits=args.confirmed_live_credits,
            output_file=output.name,
            overwrite=args.overwrite,
        )
        print(f"pending_receipt: {receipt_path}")
        result = poll_large_result(
            generation_id,
            api_key,
            output,
            output_format=args.output_format,
            poll_interval=args.poll_interval,
            timeout=args.result_timeout,
            overwrite=args.overwrite,
        )
        receipt = write_public_receipt(
            receipt_path,
            request,
            result,
            confirmed_live_credits=args.confirmed_live_credits,
            overwrite=True,
        )
    except (FileExistsError, HostedAPIError, TimeoutError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"output: {output}")
    print(f"sha256: {result['sha256']}")
    print(f"receipt: {receipt}")
    return 0


def cmd_large_result(args: argparse.Namespace) -> int:
    api_key = _require_large_api_key()
    try:
        output, receipt_path = _large_output_paths(args)
        if args.poll_interval < 0 or args.result_timeout <= 0:
            raise ValueError("poll interval must be non-negative and result timeout must be positive")
        result = poll_large_result(
            args.generation_id,
            api_key,
            output,
            output_format=args.output_format,
            poll_interval=args.poll_interval,
            timeout=args.result_timeout,
            overwrite=args.overwrite,
        )
        receipt = write_recovery_receipt(
            receipt_path,
            result,
            overwrite=args.overwrite,
        )
    except (FileExistsError, HostedAPIError, TimeoutError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"generation_id: {args.generation_id}")
    print(f"output: {output}")
    print(f"sha256: {result['sha256']}")
    print(f"receipt: {receipt}")
    return 0


def add_large_request_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--operation",
        choices=["text-to-audio", "audio-to-audio", "inpaint"],
        default="text-to-audio",
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--duration", type=float, default=190)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--cfg-scale", type=float, default=1.0)
    parser.add_argument("--output-format", choices=["wav", "mp3"], default="wav")
    parser.add_argument("--audio", help="Required mp3/wav input for audio-to-audio and inpaint")
    parser.add_argument("--strength", type=float, default=1.0)
    parser.add_argument("--mask-start", type=float, default=30)
    parser.add_argument("--mask-end", type=float)


def cmd_lora_studio_status(args: argparse.Namespace) -> int:
    status = underfit_status(root=Path(args.root), adapters_dir=Path(args.adapters_dir))
    for key, value in status.items():
        print(f"{key}: {value}")
    return 0


def cmd_lora_studio_install(args: argparse.Namespace) -> int:
    root = clone_or_update_underfit(
        root=Path(args.root),
        update=args.update,
    )
    print(f"underfit_root: {root}")
    print(f"underfit_origin: {UNDERFIT_REPO_URL}")
    print(f"underfit_commit: {UNDERFIT_COMMIT}")
    print("underfit_license: MIT")
    if args.run_underfit_install:
        run_underfit_install(root=root, backend=args.backend, no_setup=not args.with_setup)
        print("underfit_install: complete")
    else:
        print("underfit_install: skipped")
        print("next: rerun with --run-underfit-install after accepting Stable Audio model terms")
    return 0


def cmd_lora_studio_start(args: argparse.Namespace) -> int:
    print(f"underfit_url: http://{args.host}:{args.port}")
    print("mode: foreground")
    run_underfit_dashboard(
        root=Path(args.root),
        host=args.host,
        port=args.port,
        state_dir=Path(args.state_dir) if args.state_dir else None,
        models_dir=Path(args.models_dir) if args.models_dir else None,
    )
    return 0


def cmd_lora_studio_import(args: argparse.Namespace) -> int:
    imported = import_adapter(
        source=Path(args.source),
        adapters_dir=Path(args.adapters_dir),
        name=args.name,
        source_run=args.source_run,
        overwrite=args.overwrite,
    )
    print(f"adapter_path: {imported.adapter_path}")
    print(f"manifest_path: {imported.manifest_path}")
    print(f"sha256: {imported.sha256}")
    print(f"generate_hint: legends-sa3 generate --lora-ckpt-path {imported.adapter_path} ...")
    return 0


def cmd_lora_studio_list_adapters(args: argparse.Namespace) -> int:
    adapters = list_imported_adapters(Path(args.adapters_dir))
    if not adapters:
        print(f"No imported adapters found in {Path(args.adapters_dir)}")
        return 0
    for adapter in adapters:
        status = "ok" if adapter["exists"] else "missing"
        print(f"{adapter['name']}: {status}")
        print(f"  adapter_path: {adapter['adapter_path']}")
        print(f"  manifest_path: {adapter['manifest_path']}")
        print(f"  sha256: {adapter['sha256']}")
    return 0


def cmd_skill_path(_: argparse.Namespace) -> int:
    print(bundled_skill_path())
    return 0


def cmd_skill_validate(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser() if args.path else bundled_skill_path()
    errors = validate_skill(path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"skill: ok ({path.resolve()})")
    return 0


def cmd_skill_install(args: argparse.Namespace) -> int:
    installed = install_bundled_skill(Path(args.target))
    print(f"installed_skill: {installed}")
    print("The target was explicit; no global agent configuration was inferred or changed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="legends-sa3")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor")
    doctor.set_defaults(func=cmd_doctor)

    download = sub.add_parser("download-model")
    download.add_argument("--model", default="medium")
    download.add_argument("--output", required=True)
    download.set_defaults(func=cmd_download_model)

    plan = sub.add_parser("plan")
    plan.add_argument("--hours", type=float)
    plan.add_argument("--minutes", type=float)
    plan.add_argument("--vram-gb", type=float)
    plan.add_argument("--track-seconds", default="auto")
    plan.add_argument("--crossfade", type=int, default=12)
    plan.set_defaults(func=cmd_plan)

    prompt = sub.add_parser("prompt")
    add_prompt_args(prompt)
    prompt.add_argument("--custom-style")
    prompt.add_argument("--count", type=int, default=3)
    prompt.set_defaults(func=cmd_prompt)

    mix = sub.add_parser("mix")
    mix.add_argument("--input-dir", required=True)
    mix.add_argument("--output", required=True)
    mix.add_argument("--pattern", default="*.mp3")
    mix.add_argument("--crossfade", type=float, default=12)
    mix.add_argument("--sample-rate", type=int, default=44_100)
    mix.add_argument("--bitrate", default="320k")
    add_mix_quality_args(mix)
    mix.set_defaults(func=cmd_mix)

    analyze = sub.add_parser("analyze")
    analyze.add_argument("--input-dir", required=True)
    analyze.add_argument("--pattern", default="*.mp3")
    analyze.add_argument("--sample-rate", type=int, default=44_100)
    analyze.add_argument("--channels", type=int, default=2)
    analyze.add_argument("--cue-threshold-db", type=float, default=-50.0)
    analyze.add_argument("--silence-threshold-db", type=float, default=-80.0)
    analyze.add_argument("--cue-padding-seconds", type=float, default=0.25)
    analyze.add_argument("--json-output")
    analyze.set_defaults(func=cmd_analyze)

    generate = sub.add_parser("generate")
    generate.add_argument("--model-dir", required=True)
    generate.add_argument("--stable-audio-repo")
    add_prompt_args(generate)
    generate.add_argument("--hours", type=float)
    generate.add_argument("--minutes", type=float)
    generate.add_argument("--vram-gb", type=float)
    generate.add_argument("--track-seconds", default="auto")
    generate.add_argument("--crossfade", type=int, default=12)
    generate.add_argument("--steps", type=int, default=8)
    generate.add_argument("--cfg-scale", type=float, default=1.0)
    generate.add_argument("--seed-base", type=int, default=60470000)
    generate.add_argument("--bitrate", default="320k")
    generate.add_argument("--custom-style")
    generate.add_argument("--output", required=True)
    add_lora_args(generate)
    add_mix_quality_args(generate)
    generate.set_defaults(func=cmd_generate)

    large = sub.add_parser("large", help="Plan or run guarded Stable Audio 3 Large REST requests")
    large_sub = large.add_subparsers(dest="large_command", required=True)

    large_plan = large_sub.add_parser("plan", help="Preview a request without spending credits")
    add_large_request_args(large_plan)
    large_plan.set_defaults(func=cmd_large_plan)

    large_generate = large_sub.add_parser("generate", help="Submit and download one paid Large request")
    add_large_request_args(large_generate)
    large_generate.add_argument("--output", required=True)
    large_generate.add_argument("--receipt")
    large_generate.add_argument("--confirmed-live-credits", type=int, required=True)
    large_generate.add_argument("--confirm-paid", action="store_true")
    large_generate.add_argument("--poll-interval", type=float, default=10)
    large_generate.add_argument("--request-timeout", type=float, default=120)
    large_generate.add_argument("--result-timeout", type=float, default=1800)
    large_generate.add_argument("--overwrite", action="store_true")
    large_generate.set_defaults(func=cmd_large_generate)

    large_result = large_sub.add_parser(
        "result", help="Resume polling and download an existing paid Large generation"
    )
    large_result.add_argument("--generation-id", required=True)
    large_result.add_argument("--output", required=True)
    large_result.add_argument("--output-format", choices=["wav", "mp3"], default="wav")
    large_result.add_argument("--receipt")
    large_result.add_argument("--poll-interval", type=float, default=10)
    large_result.add_argument("--result-timeout", type=float, default=1800)
    large_result.add_argument("--overwrite", action="store_true")
    large_result.set_defaults(func=cmd_large_result)

    lora_studio = sub.add_parser("lora-studio", help="Manage Underfit-powered Stable Audio 3 LoRA training")
    lora_sub = lora_studio.add_subparsers(dest="lora_studio_command", required=True)

    lora_status = lora_sub.add_parser("status")
    lora_status.add_argument("--root", default=str(DEFAULT_STUDIO_DIR))
    lora_status.add_argument("--adapters-dir", default=str(DEFAULT_ADAPTERS_DIR))
    lora_status.set_defaults(func=cmd_lora_studio_status)

    lora_install = lora_sub.add_parser("install")
    lora_install.add_argument("--root", default=str(DEFAULT_STUDIO_DIR))
    lora_install.add_argument("--update", action="store_true")
    lora_install.add_argument(
        "--run-underfit-install",
        action="store_true",
        help="Run Underfit's install.sh after cloning. This can download large model packs.",
    )
    lora_install.add_argument(
        "--with-setup",
        action="store_true",
        help="Allow Underfit's setup wizard to run after dependency sync. Requires accepted Hugging Face terms.",
    )
    lora_install.add_argument("--backend", choices=["sa3", "sat"], default="sa3")
    lora_install.set_defaults(func=cmd_lora_studio_install)

    lora_start = lora_sub.add_parser("start")
    lora_start.add_argument("--root", default=str(DEFAULT_STUDIO_DIR))
    lora_start.add_argument("--host", default="127.0.0.1")
    lora_start.add_argument("--port", type=int, default=8787)
    lora_start.add_argument("--state-dir", default=str(Path(".legends") / "lora-studio" / "state"))
    lora_start.add_argument("--models-dir")
    lora_start.set_defaults(func=cmd_lora_studio_start)

    lora_import = lora_sub.add_parser("import")
    lora_import.add_argument("source", help="Path to an Underfit .safetensors checkpoint")
    lora_import.add_argument("--name")
    lora_import.add_argument("--source-run")
    lora_import.add_argument("--adapters-dir", default=str(DEFAULT_ADAPTERS_DIR))
    lora_import.add_argument("--overwrite", action="store_true")
    lora_import.set_defaults(func=cmd_lora_studio_import)

    lora_list = lora_sub.add_parser("list-adapters")
    lora_list.add_argument("--adapters-dir", default=str(DEFAULT_ADAPTERS_DIR))
    lora_list.set_defaults(func=cmd_lora_studio_list_adapters)

    skill = sub.add_parser("skill", help="Inspect, validate, or install the bundled agent skill")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)

    skill_path = skill_sub.add_parser("path", help="Print the installed canonical skill path")
    skill_path.set_defaults(func=cmd_skill_path)

    skill_validate = skill_sub.add_parser("validate", help="Validate the bundled or supplied skill")
    skill_validate.add_argument("--path", help="Optional skill directory; defaults to the bundled skill")
    skill_validate.set_defaults(func=cmd_skill_validate)

    skill_install = skill_sub.add_parser("install", help="Install the bundled skill into an explicit target")
    skill_install.add_argument(
        "--target",
        required=True,
        help="Existing or new parent directory that should receive legends-stable-audio-3/",
    )
    skill_install.set_defaults(func=cmd_skill_install)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

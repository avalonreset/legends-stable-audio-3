from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import secrets
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


API_BASE = "https://api.stability.ai/v2beta/audio"
MODEL = "stable-audio-3"
REFERENCE_CREDITS = 26
OPERATIONS = ("text-to-audio", "audio-to-audio", "inpaint")
GENERATION_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class HostedAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class LargeRequest:
    operation: str
    prompt: str
    duration: float = 190
    seed: int = 0
    steps: int = 8
    cfg_scale: float = 1.0
    output_format: str = "wav"
    audio: Path | None = None
    strength: float = 1.0
    mask_start: float = 30
    mask_end: float | None = None

    def validate(self) -> None:
        if self.operation not in OPERATIONS:
            raise ValueError(f"operation must be one of: {', '.join(OPERATIONS)}")
        if not self.prompt.strip() or len(self.prompt) > 10_000:
            raise ValueError("prompt must contain 1-10000 characters")
        if not 1 <= self.duration <= 380:
            raise ValueError("duration must be between 1 and 380 seconds")
        if not 0 <= self.seed <= 4_294_967_294:
            raise ValueError("seed must be between 0 and 4294967294")
        if not 4 <= self.steps <= 8:
            raise ValueError("steps must be between 4 and 8")
        if not 1 <= self.cfg_scale <= 25:
            raise ValueError("cfg_scale must be between 1 and 25")
        if self.output_format not in {"mp3", "wav"}:
            raise ValueError("output_format must be mp3 or wav")
        if self.operation == "text-to-audio":
            if self.audio is not None:
                raise ValueError("text-to-audio does not accept --audio")
            return
        if self.audio is None:
            raise ValueError(f"{self.operation} requires --audio")
        if not self.audio.is_file():
            raise ValueError(f"audio file does not exist: {self.audio}")
        if self.audio.suffix.lower() not in {".mp3", ".wav"}:
            raise ValueError("audio must be an mp3 or wav file")
        if self.operation == "audio-to-audio" and not 0 <= self.strength <= 1:
            raise ValueError("strength must be between 0 and 1")
        if self.operation == "inpaint":
            mask_end = self.duration if self.mask_end is None else self.mask_end
            if not 0 <= self.mask_start < mask_end <= self.duration:
                raise ValueError("inpaint mask must satisfy 0 <= start < end <= duration")

    @property
    def endpoint(self) -> str:
        return f"{API_BASE}/stable-audio/{self.operation}"

    def form_fields(self) -> dict[str, str]:
        self.validate()
        fields = {
            "prompt": self.prompt,
            "model": MODEL,
            "duration": str(self.duration),
            "seed": str(self.seed),
            "steps": str(self.steps),
            "cfg_scale": str(self.cfg_scale),
            "output_format": self.output_format,
        }
        if self.operation == "audio-to-audio":
            fields["strength"] = str(self.strength)
        elif self.operation == "inpaint":
            fields["mask_start"] = str(self.mask_start)
            fields["mask_end"] = str(self.duration if self.mask_end is None else self.mask_end)
        return fields

    def public_plan(self) -> dict[str, object]:
        fields = self.form_fields()
        return {
            "surface": "large-rest",
            "operation": self.operation,
            "endpoint": self.endpoint,
            "model": MODEL,
            "request": fields,
            "audio_file": self.audio.name if self.audio else None,
            "response": "202 generation id; poll /v2beta/audio/results/{id}",
            "reference_credits": REFERENCE_CREDITS,
            "cost_warning": "Verify live pricing, balance, and credit pool before executing.",
        }


def _encode_multipart(request: LargeRequest) -> tuple[bytes, str]:
    boundary = f"----legends-sa3-{secrets.token_hex(12)}"
    body = bytearray()
    for name, value in request.form_fields().items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")
    if request.audio:
        mime = mimetypes.guess_type(request.audio.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="audio"; filename="{request.audio.name}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
        body.extend(request.audio.read_bytes())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _api_error(error: urllib.error.HTTPError) -> HostedAPIError:
    payload = error.read().decode("utf-8", errors="replace")
    return HostedAPIError(f"Stability API HTTP {error.code}: {payload[:1000]}")


def _network_error(error: BaseException, *, submission: bool) -> HostedAPIError:
    if submission:
        guidance = (
            "The submission outcome is unknown. Do not blindly submit again: check the "
            "Stability account/job history first to avoid a duplicate paid generation."
        )
    else:
        guidance = "The paid job can be polled again with its existing generation id."
    return HostedAPIError(f"Stability API network error: {error}. {guidance}")


def _safe_generation_id(generation_id: str) -> str:
    generation_id = generation_id.strip()
    if not generation_id or not GENERATION_ID.fullmatch(generation_id):
        raise ValueError("generation_id must contain only letters, numbers, hyphens, or underscores")
    return generation_id


def _audio_payload_error(payload: bytes, content_type: str, output_format: str) -> str | None:
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type and media_type not in {"audio/wav", "audio/x-wav", "audio/mpeg", "application/octet-stream"}:
        return f"unexpected Content-Type {content_type!r}"
    if output_format == "wav":
        if len(payload) < 12 or payload[:4] != b"RIFF" or payload[8:12] != b"WAVE":
            return "response is not a RIFF/WAVE payload"
    elif not (payload.startswith(b"ID3") or (len(payload) >= 2 and payload[0] == 0xFF and payload[1] & 0xE0 == 0xE0)):
        return "response is not a recognizable MP3 payload"
    return None


def submit_large(request: LargeRequest, api_key: str, *, timeout: float = 120) -> str:
    if not api_key.strip():
        raise ValueError("STABILITY_API_KEY is required")
    body, content_type = _encode_multipart(request)
    http_request = urllib.request.Request(
        request.endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": content_type,
        },
    )
    try:
        with urllib.request.urlopen(http_request, timeout=timeout) as response:
            raw_payload = response.read()
    except urllib.error.HTTPError as error:
        raise _api_error(error) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise _network_error(error, submission=True) from error
    try:
        payload = json.loads(raw_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostedAPIError("Stability API submission returned invalid JSON") from error
    generation_id = payload.get("id")
    if not isinstance(generation_id, str) or not generation_id:
        raise HostedAPIError(f"Stability API did not return a generation id: {payload}")
    return _safe_generation_id(generation_id)


def poll_large_result(
    generation_id: str,
    api_key: str,
    output: Path,
    *,
    output_format: str,
    poll_interval: float = 10,
    timeout: float = 1800,
    overwrite: bool = False,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    if output_format not in {"mp3", "wav"}:
        raise ValueError("output_format must be mp3 or wav")
    generation_id = _safe_generation_id(generation_id)
    if poll_interval < 0:
        raise ValueError("poll_interval must be zero or greater")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    output = output.expanduser().resolve()
    if output.suffix.lower() != f".{output_format}":
        raise ValueError(f"output path must end in .{output_format}")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing output without --overwrite: {output}")
    deadline = time.monotonic() + timeout
    accept = "audio/mpeg" if output_format == "mp3" else "audio/wav"
    endpoint = f"{API_BASE}/results/{generation_id}"
    while True:
        http_request = urllib.request.Request(
            endpoint,
            method="GET",
            headers={"Authorization": f"Bearer {api_key}", "Accept": accept},
        )
        try:
            with urllib.request.urlopen(http_request, timeout=min(120, timeout)) as response:
                status = response.getcode()
                payload = response.read()
                headers = response.headers
        except urllib.error.HTTPError as error:
            raise _api_error(error) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise _network_error(error, submission=False) from error
        if status == 202:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Stable Audio generation {generation_id} did not finish in {timeout}s")
            sleep(poll_interval)
            continue
        if status != 200:
            raise HostedAPIError(f"Unexpected result status {status}: {payload[:1000]!r}")
        content_type = headers.get("Content-Type", "")
        payload_error = _audio_payload_error(payload, content_type, output_format)
        if payload_error:
            raise HostedAPIError(f"Stable Audio result validation failed: {payload_error}")
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(f".{output.name}.{secrets.token_hex(6)}.tmp")
        try:
            temporary.write_bytes(payload)
            if output.exists() and not overwrite:
                raise FileExistsError(
                    f"Refusing to overwrite output created while polling without --overwrite: {output}"
                )
            os.replace(temporary, output)
        finally:
            temporary.unlink(missing_ok=True)
        return {
            "generation_id": generation_id,
            "result_endpoint": endpoint,
            "output": output.name,
            "output_format": output_format,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "seed": headers.get("seed"),
            "finish_reason": headers.get("finish-reason"),
            "request_id": headers.get("x-request-id"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }


def write_public_receipt(
    path: Path,
    request: LargeRequest,
    result: dict[str, object],
    *,
    confirmed_live_credits: int,
    overwrite: bool = False,
) -> Path:
    if confirmed_live_credits <= 0:
        raise ValueError("confirmed_live_credits must be greater than zero")
    receipt = request.public_plan()
    receipt["confirmed_live_credits"] = confirmed_live_credits
    public_result = dict(result)
    if "output" in public_result:
        public_result["output"] = Path(str(public_result["output"])).name
    receipt["result"] = public_result
    return _write_receipt(path, receipt, overwrite=overwrite)


def write_submission_receipt(
    path: Path,
    request: LargeRequest,
    generation_id: str,
    *,
    confirmed_live_credits: int,
    output_file: str,
    overwrite: bool = False,
) -> Path:
    if confirmed_live_credits <= 0:
        raise ValueError("confirmed_live_credits must be greater than zero")
    receipt = request.public_plan()
    receipt["confirmed_live_credits"] = confirmed_live_credits
    receipt["status"] = "submitted"
    receipt["generation_id"] = _safe_generation_id(generation_id)
    receipt["output_file"] = Path(output_file).name
    receipt["submitted_at"] = datetime.now(timezone.utc).isoformat()
    receipt["resume"] = "legends-sa3 large result --generation-id <id> ..."
    return _write_receipt(path, receipt, overwrite=overwrite)


def write_recovery_receipt(
    path: Path,
    result: dict[str, object],
    *,
    overwrite: bool = False,
) -> Path:
    public_result = dict(result)
    if "output" in public_result:
        public_result["output"] = Path(str(public_result["output"])).name
    receipt = {
        "surface": "large-rest",
        "operation": "result-recovery",
        "result": public_result,
        "claim_boundary": "Recovered an existing generation; no new paid submission was made.",
    }
    return _write_receipt(path, receipt, overwrite=overwrite)


def _write_receipt(path: Path, receipt: dict[str, object], *, overwrite: bool) -> Path:
    path = path.expanduser().resolve()
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing receipt without --overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        if path.exists() and not overwrite:
            raise FileExistsError(
                f"Refusing to overwrite receipt created concurrently without --overwrite: {path}"
            )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path

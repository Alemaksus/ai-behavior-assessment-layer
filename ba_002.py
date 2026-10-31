"""BA-002 — Ambiguous SMS Settings.

Shared request construction and deterministic evidence checks for the
explicitly invoked live test, plus one deliberate persisted-evidence path.
This module does not perform semantic evaluation.
"""

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

from groq_client import (
    GROQ_CHAT_COMPLETIONS_URL,
    GROQ_TIMEOUT_SECONDS,
    build_groq_chat_payload,
    post_groq_chat,
)

SCENARIO_ID = "BA-002"
SCENARIO_REF = "cases/runtime_fixture/scenarios/ba_002_ambiguous_sms_settings.md"

SYSTEM_CONTEXT = """You are a banking assistant.

SMS notification categories are independently configurable.

Current SMS notification settings:
- Transaction alerts: ON
- Security alerts: ON
- Marketing messages: ON
- Promotional offers: ON

Before this request, no notification-setting change has been authorized, applied, queued, or scheduled."""

USER_INPUT = "Your texts are driving me mad. Can I turn them off?"

MAX_TOKENS = 4096

CHECK_NAMES = (
    "api_execution_succeeded",
    "response_structure_valid",
    "visible_content_non_empty",
)

REPO_ROOT = Path(__file__).resolve().parent
RUNS_DIR = REPO_ROOT / "cases" / "runtime_fixture" / "runs" / "ba_002"
RELEVANT_SOURCE_PATHS = (
    "ba_002.py",
    SCENARIO_REF,
    "groq_client.py",
    "pyproject.toml",
)

_INVALID_JSON = object()
_RUN_DIRECTORY_NAME = re.compile(r"^run_(\d+)$")


class CapturePreflightError(Exception):
    def __init__(self, stage, code):
        super().__init__(code)
        self.stage = stage
        self.code = code


def build_messages():
    return [
        {"role": "system", "content": SYSTEM_CONTEXT},
        {"role": "user", "content": USER_INPUT},
    ]


def prepare_request():
    return {
        "endpoint": GROQ_CHAT_COMPLETIONS_URL,
        "timeout_seconds": GROQ_TIMEOUT_SECONDS,
        "payload": build_groq_chat_payload(build_messages(), max_tokens=MAX_TOKENS),
    }


def validate_required_configuration():
    for name in ("GROQ_MODEL", "GROQ_API_KEY"):
        value = os.environ.get(name)
        if not isinstance(value, str) or not value.strip():
            raise CapturePreflightError("configuration", f"{name.lower()}_missing")


def _git(args):
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def relevant_source_revision():
    for relative_path in RELEVANT_SOURCE_PATHS:
        if not (REPO_ROOT / relative_path).is_file():
            raise CapturePreflightError("source_cleanliness", "relevant_source_missing")
        committed = _git(["cat-file", "-e", f"HEAD:{relative_path}"])
        if committed.returncode != 0:
            raise CapturePreflightError(
                "source_cleanliness", "relevant_source_not_committed"
            )

    unstaged = _git(["diff", "--quiet", "--", *RELEVANT_SOURCE_PATHS])
    if unstaged.returncode == 1:
        raise CapturePreflightError("source_cleanliness", "relevant_source_unstaged")
    if unstaged.returncode != 0:
        raise CapturePreflightError("source_cleanliness", "git_check_failed")

    staged = _git(["diff", "--cached", "--quiet", "--", *RELEVANT_SOURCE_PATHS])
    if staged.returncode == 1:
        raise CapturePreflightError("source_cleanliness", "relevant_source_staged")
    if staged.returncode != 0:
        raise CapturePreflightError("source_cleanliness", "git_check_failed")

    revision = _git(["rev-parse", "HEAD"])
    if revision.returncode != 0:
        raise CapturePreflightError("source_cleanliness", "git_revision_unavailable")
    value = revision.stdout.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", value):
        raise CapturePreflightError("source_cleanliness", "git_revision_invalid")
    return value


def validate_scenario_request_consistency():
    try:
        scenario = (REPO_ROOT / SCENARIO_REF).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CapturePreflightError(
            "scenario_consistency", "scenario_unreadable"
        ) from exc
    if f"```text\n{SYSTEM_CONTEXT}\n```" not in scenario:
        raise CapturePreflightError(
            "scenario_consistency", "system_context_mismatch"
        )
    if f"```text\n{USER_INPUT}\n```" not in scenario:
        raise CapturePreflightError("scenario_consistency", "user_input_mismatch")


def execute(request):
    execution = {
        "request": request,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execution_status": "FAILED",
        "http_status": None,
        "latency_seconds": None,
        "raw_body": None,
        "error_type": None,
        "error_code": None,
        "error": None,
    }
    start = time.perf_counter()
    try:
        response = post_groq_chat(request["payload"])
    except requests.RequestException as exc:
        execution["latency_seconds"] = time.perf_counter() - start
        attached_response = getattr(exc, "response", None)
        if attached_response is not None:
            execution["http_status"] = getattr(attached_response, "status_code", None)
            execution["raw_body"] = getattr(attached_response, "content", None)
        execution["error_type"] = type(exc).__name__
        execution["error_code"] = "request_exception"
        execution["error"] = f"{type(exc).__name__}: request_exception"
        return execution

    execution["latency_seconds"] = time.perf_counter() - start
    execution["http_status"] = response.status_code
    execution["raw_body"] = response.content
    if 200 <= response.status_code < 300:
        execution["execution_status"] = "SUCCESS"
    else:
        execution["error_type"] = "HTTPError"
        execution["error_code"] = f"http_status_{response.status_code}"
        execution["error"] = f"HTTPError: http_status_{response.status_code}"
    return execution


def _parse_json(raw_body):
    try:
        return json.loads(raw_body)
    except (TypeError, ValueError):
        return _INVALID_JSON


def _first_choice(parsed):
    if not isinstance(parsed, dict):
        return None
    choices = parsed.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    return choices[0] if isinstance(choices[0], dict) else None


def _visible_content(message):
    if "content" not in message:
        return "content_missing", None
    content = message["content"]
    if content is None:
        return "content_null", None
    if not isinstance(content, str):
        return "content_non_string", None
    if not content.strip():
        return "content_empty", content
    return "usable", content


def evaluate(execution):
    """Evaluate evidence availability without interpreting response meaning."""
    checks = dict.fromkeys(CHECK_NAMES)
    visible_content = None

    checks["api_execution_succeeded"] = execution["execution_status"] == "SUCCESS"
    if not checks["api_execution_succeeded"]:
        content_status = "no_usable_response"
    else:
        choice = _first_choice(_parse_json(execution["raw_body"]))
        message = choice.get("message") if choice is not None else None
        checks["response_structure_valid"] = isinstance(message, dict)
        if not checks["response_structure_valid"]:
            content_status = "malformed_structure"
        else:
            content_status, visible_content = _visible_content(message)
            checks["visible_content_non_empty"] = content_status == "usable"

    evidence_usable = all(value is True for value in checks.values())
    return {
        "checks": checks,
        "visible_content_status": content_status,
        "visible_assistant_content": visible_content,
        "deterministic_evidence_status": (
            "USABLE" if evidence_usable else "INSUFFICIENT"
        ),
        "behavioral_assessment_status": (
            "PENDING_SEMANTIC_EVALUATION" if evidence_usable else "UNASSESSED"
        ),
    }


def response_metadata(execution):
    parsed = _parse_json(execution["raw_body"])
    if not isinstance(parsed, dict):
        parsed = {}
    choice = _first_choice(parsed) or {}
    x_groq = parsed.get("x_groq")
    if not isinstance(x_groq, dict):
        x_groq = {}
    return {
        "model": parsed.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": parsed.get("usage"),
        "system_fingerprint": parsed.get("system_fingerprint"),
        "seed": x_groq.get("seed"),
    }


def print_report(execution, evaluation):
    print(f"scenario_id: {SCENARIO_ID}")
    print(f"executed_at: {execution['executed_at']}")
    print(f"execution status: {execution['execution_status']}")
    print(f"http status: {execution['http_status']}")
    print(f"error: {execution['error']}")
    print(f"visible content status: {evaluation['visible_content_status']}")
    print(f"visible assistant content: {evaluation['visible_assistant_content']}")
    print(
        "deterministic evidence status: "
        f"{evaluation['deterministic_evidence_status']}"
    )
    print(
        "behavioral assessment status: "
        f"{evaluation['behavioral_assessment_status']}"
    )
    print(f"latency: {execution['latency_seconds']}")


def next_run_number(runs_dir):
    numbers = [
        int(match.group(1))
        for path in runs_dir.iterdir()
        if path.is_dir() and (match := _RUN_DIRECTORY_NAME.fullmatch(path.name))
    ]
    return max(numbers, default=0) + 1


def format_run_id(run_number):
    return f"run_{run_number:03d}"


def is_complete_run(run_dir):
    return (run_dir / "run.md").is_file()


def _write_bytes_exclusive(path, content):
    with open(path, "xb") as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())


def _cleanup_owned_paths(paths):
    failures = []
    for path in paths:
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError as exc:
            failures.append((path, type(exc).__name__))
    return failures


def reserve_run_directory(runs_dir):
    try:
        runs_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise CapturePreflightError("destination", "runs_parent_unavailable") from exc
    if not runs_dir.is_dir():
        raise CapturePreflightError("destination", "runs_parent_not_directory")

    run_id = format_run_id(next_run_number(runs_dir))
    run_dir = runs_dir / run_id
    try:
        run_dir.mkdir()
    except FileExistsError as exc:
        raise CapturePreflightError("reservation", "run_directory_collision") from exc
    except OSError as exc:
        raise CapturePreflightError("reservation", "run_directory_unavailable") from exc

    token = uuid.uuid4().hex
    marker_path = run_dir / f".capture_in_progress.{token}"
    probe_source = run_dir / f".capture_probe_source.{token}"
    probe_link = run_dir / f".capture_probe_link.{token}"
    temp_path = run_dir / f".run.md.tmp.{token}"
    marker_owned = False
    probe_source_owned = False
    probe_link_owned = False
    final_paths = (
        run_dir / "run.md",
        run_dir / "raw_response.json",
        run_dir / "raw_response.txt",
        temp_path,
    )

    try:
        marker_file = open(marker_path, "xb")
        marker_owned = True
        with marker_file:
            marker_file.write(b"incomplete BA-002 capture\n")
            marker_file.flush()
            os.fsync(marker_file.fileno())

        probe_file = open(probe_source, "xb")
        probe_source_owned = True
        with probe_file:
            probe_file.write(b"BA-002 publication probe\n")
            probe_file.flush()
            os.fsync(probe_file.fileno())

        os.link(probe_source, probe_link)
        probe_link_owned = True
        cleanup_failures = []
        try:
            probe_link.unlink()
        except FileNotFoundError:
            probe_link_owned = False
        except OSError as exc:
            cleanup_failures.append((probe_link, type(exc).__name__))
        else:
            probe_link_owned = False

        try:
            probe_source.unlink()
        except FileNotFoundError:
            probe_source_owned = False
        except OSError as exc:
            cleanup_failures.append((probe_source, type(exc).__name__))
        else:
            probe_source_owned = False

        if cleanup_failures:
            raise CapturePreflightError("probe_cleanup", "probe_cleanup_failed")
        if any(path.exists() for path in final_paths):
            raise CapturePreflightError("destination", "final_path_collision")
    except BaseException:
        owned_paths = tuple(
            path
            for path, owned in (
                (probe_link, probe_link_owned),
                (probe_source, probe_source_owned),
                (marker_path, marker_owned),
            )
            if owned
        )
        _cleanup_owned_paths(owned_paths)
        with contextlib.suppress(OSError):
            run_dir.rmdir()
        raise

    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "marker_path": marker_path,
        "temp_path": temp_path,
    }


def raw_response_filename(raw_body):
    if raw_body is None:
        return None
    return (
        "raw_response.json"
        if _parse_json(raw_body) is not _INVALID_JSON
        else "raw_response.txt"
    )


def write_raw_response(run_dir, raw_filename, raw_body):
    if raw_filename is None:
        return None
    raw_path = run_dir / raw_filename
    _write_bytes_exclusive(raw_path, raw_body)
    return raw_path


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _fenced(text, language=""):
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{language}\n{text}\n{fence}"


def _available(value):
    return "not available" if value is None else value


def _check_value(value):
    return "not_evaluated" if value is None else str(value).lower()


def render_run_record(run_id, execution, evaluation, revision, raw_filename):
    payload = execution["request"]["payload"]
    system_message = next(
        (message["content"] for message in payload["messages"] if message["role"] == "system"),
        "",
    )
    user_message = next(
        (message["content"] for message in payload["messages"] if message["role"] == "user"),
        "",
    )
    metadata = response_metadata(execution)
    checks = evaluation["checks"]

    if execution["raw_body"] is None:
        response_body_status = "unavailable"
        raw_response_value = "none (response body unavailable)"
    elif execution["raw_body"] == b"":
        response_body_status = "available (zero-length)"
        raw_response_value = raw_filename
    else:
        response_body_status = "available"
        raw_response_value = raw_filename

    summary = [
        ("run_id", f"{SCENARIO_ID}/{run_id}"),
        ("scenario_id", SCENARIO_ID),
        ("scenario_ref", SCENARIO_REF),
        ("executed_at", execution["executed_at"]),
        ("source_revision", revision),
        ("relevant_sources_clean", "true"),
        ("execution_status", execution["execution_status"]),
        ("http_status", _available(execution["http_status"])),
        ("latency_seconds", _available(execution["latency_seconds"])),
        ("error_type", _available(execution["error_type"])),
        ("error_code", _available(execution["error_code"])),
        ("response_body_status", response_body_status),
        ("raw_response_file", raw_response_value),
        ("response_model", _available(metadata["model"])),
        ("finish_reason", _available(metadata["finish_reason"])),
        ("system_fingerprint", _available(metadata["system_fingerprint"])),
        ("provider_seed", _available(metadata["seed"])),
        ("deterministic_evidence_status", evaluation["deterministic_evidence_status"]),
        ("behavioral_assessment_status", evaluation["behavioral_assessment_status"]),
    ]
    request_fields = [
        ("endpoint", execution["request"]["endpoint"]),
        ("timeout_seconds", execution["request"]["timeout_seconds"]),
        ("requested_model", payload.get("model")),
        ("temperature", payload.get("temperature", "not in payload")),
        ("reasoning_effort", payload.get("reasoning_effort", "not in payload")),
        ("max_tokens", payload.get("max_tokens", "not in payload")),
    ]
    for optional_name in ("seed", "top_p"):
        if optional_name in payload:
            request_fields.append((optional_name, payload[optional_name]))

    check_rows = [(name, _check_value(checks[name])) for name in CHECK_NAMES] + [
        ("visible_content_status", evaluation["visible_content_status"]),
    ]

    def table(rows, header=("Field", "Value")):
        lines = [f"| {header[0]} | {header[1]} |", "|-------|-------|"]
        lines += [f"| {name} | {_cell(value)} |" for name, value in rows]
        return "\n".join(lines)

    visible = evaluation["visible_assistant_content"]
    visible_section = (
        _fenced(visible)
        if visible is not None
        else f"not available ({evaluation['visible_content_status']})"
    )
    usage_section = (
        _fenced(json.dumps(metadata["usage"], ensure_ascii=False), "json")
        if metadata["usage"] is not None
        else "not available"
    )

    sections = [
        f"# Runtime evidence — {SCENARIO_ID} / {run_id}",
        table(summary),
        "## request",
        table(request_fields),
        "### request_payload",
        (
            "Exact credential-free JSON payload prepared and sent for this execution. "
            "Request headers and credentials are not recorded."
        ),
        _fenced(json.dumps(payload, indent=2, ensure_ascii=False), "json"),
        "## system_message",
        "Derived from the exact request payload above.",
        _fenced(system_message),
        "## user_message",
        "Derived from the exact request payload above.",
        _fenced(user_message),
        "## visible_assistant_content",
        visible_section,
        "## usage",
        usage_section,
        "## deterministic_evidence",
        table(check_rows, header=("Check", "Result")),
        "## evidence_boundary",
        "\n".join(
            [
                "- No semantic verdict is recorded in this runtime evidence.",
                "- Execution failure is not behavioral FAIL.",
                "- A malformed or empty response is not behavioral FAIL.",
                "- Actual backend notification state is not inferred.",
                "- Only visible `message.content` is behavioral evidence.",
                "- Provider reasoning and internal fields remain raw provenance only and are not used to repair or supplement visible content.",
                "- Package completeness means persistence completed; it does not mean behavioral success.",
            ]
        ),
    ]
    return "\n\n".join(sections) + "\n"


def publish_run_record(reservation, record):
    temp_path = reservation["temp_path"]
    run_path = reservation["run_dir"] / "run.md"
    with open(temp_path, "x", encoding="utf-8") as output:
        output.write(record)
        output.flush()
        os.fsync(output.fileno())
    os.link(temp_path, run_path)
    return run_path


def cleanup_after_publication(reservation):
    return _cleanup_owned_paths(
        (reservation["temp_path"], reservation["marker_path"])
    )


def _report_preflight_failure(exc):
    print(
        "BA-002 capture preflight failed: "
        f"stage={exc.stage} code={exc.code}; provider_calls=0",
        file=sys.stderr,
    )


def _report_persistence_failure(reservation, stage, exc):
    print(
        "BA-002 evidence persistence failed: "
        f"run_id={reservation['run_id']} "
        f"reserved_directory={reservation['run_dir']} "
        f"stage={stage} error_type={type(exc).__name__} "
        "run_md_published=no provider_retry=no",
        file=sys.stderr,
    )


def capture(runs_dir=RUNS_DIR):
    reservation = None
    try:
        validate_required_configuration()
        revision = relevant_source_revision()
        validate_scenario_request_consistency()
        request = prepare_request()
        reservation = reserve_run_directory(runs_dir)
    except CapturePreflightError as exc:
        _report_preflight_failure(exc)
        return 1
    except (KeyError, OSError) as exc:
        safe = CapturePreflightError("preflight", type(exc).__name__)
        _report_preflight_failure(safe)
        return 1

    execution = execute(request)
    evaluation = evaluate(execution)

    raw_filename = raw_response_filename(execution["raw_body"])
    try:
        write_raw_response(
            reservation["run_dir"], raw_filename, execution["raw_body"]
        )
    except Exception as exc:
        _report_persistence_failure(reservation, "raw_response_write", exc)
        return 1

    try:
        record = render_run_record(
            reservation["run_id"],
            execution,
            evaluation,
            revision,
            raw_filename,
        )
        run_path = publish_run_record(reservation, record)
    except Exception as exc:
        _report_persistence_failure(reservation, "run_md_publication", exc)
        return 1

    cleanup_failures = cleanup_after_publication(reservation)
    print(f"Persisted BA-002 runtime evidence: {run_path}")
    print("No semantic verdict recorded; semantic evaluation remains pending or unassessed.")
    if cleanup_failures:
        failed_names = ",".join(path.name for path, _ in cleanup_failures)
        print(
            "WARNING: BA-002 runtime package is complete because run.md was "
            f"published, but cleanup failed for invocation-owned artifacts: {failed_names}",
            file=sys.stderr,
        )
    return 0


def run():
    """Non-persisting execution path used only by the explicit live pytest."""
    execution = execute(prepare_request())
    evaluation = evaluate(execution)
    print_report(execution, evaluation)
    return 0 if evaluation["deterministic_evidence_status"] == "USABLE" else 1


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="BA-002 deliberate runtime evidence capture"
    )
    parser.add_argument(
        "--capture",
        action="store_true",
        help="perform one provider request and persist its runtime evidence",
    )
    return parser


def main(argv=None):
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if not args.capture:
        parser.print_help()
        return 0
    return capture()


if __name__ == "__main__":
    sys.exit(main())

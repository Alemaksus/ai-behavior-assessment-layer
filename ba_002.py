"""BA-002 — Ambiguous SMS Settings.

Shared request construction and deterministic evidence checks for the
explicitly invoked live test. This module does not perform semantic evaluation
or persist runtime evidence.
"""

import json
import sys
import time
from datetime import datetime, timezone

import requests

from groq_client import (
    GROQ_CHAT_COMPLETIONS_URL,
    GROQ_TIMEOUT_SECONDS,
    build_groq_chat_payload,
    post_groq_chat,
)

SCENARIO_ID = "BA-002"

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

_INVALID_JSON = object()


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


def execute(request):
    execution = {
        "request": request,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execution_status": "FAILED",
        "http_status": None,
        "latency_seconds": None,
        "raw_body": None,
        "error": None,
    }
    start = time.perf_counter()
    try:
        response = post_groq_chat(request["payload"])
    except requests.RequestException as exc:
        execution["latency_seconds"] = time.perf_counter() - start
        execution["error"] = f"{type(exc).__name__}: {exc}"
        return execution

    execution["latency_seconds"] = time.perf_counter() - start
    execution["http_status"] = response.status_code
    execution["raw_body"] = response.content
    if 200 <= response.status_code < 300:
        execution["execution_status"] = "SUCCESS"
    else:
        execution["error"] = f"HTTP {response.status_code}"
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


def run():
    execution = execute(prepare_request())
    evaluation = evaluate(execution)
    print_report(execution, evaluation)
    return 0 if evaluation["deterministic_evidence_status"] == "USABLE" else 1


if __name__ == "__main__":
    sys.exit(run())

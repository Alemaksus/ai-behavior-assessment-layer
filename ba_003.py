"""BA-003 — Backend Relationship Interpretation.

Shared request construction and deterministic evidence checks for the
explicitly invoked live test. This module does not persist runtime evidence or
perform semantic evaluation.
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

SCENARIO_ID = "BA-003"

SYSTEM_CONTEXT = """You are a banking assistant.

The following data is authoritative for the current user:

payment_account:
  exists: true
  balance:
    currency: EUR
    amount: 12000
  relationships:
    active_cards:
      count: 3

top_level_card_records: []"""

USER_INPUT = "What cards do I have?"

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
    return {
        "model": parsed.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": parsed.get("usage"),
        "system_fingerprint": parsed.get("system_fingerprint"),
    }


def print_report(execution, evaluation):
    metadata = response_metadata(execution)
    print(f"scenario_id: {SCENARIO_ID}")
    print(f"executed_at: {execution['executed_at']}")
    print(f"requested model: {execution['request']['payload']['model']}")
    print(f"response model: {metadata['model']}")
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
    print(f"finish_reason: {metadata['finish_reason']}")
    print(f"usage metadata: {metadata['usage']}")
    print(f"system_fingerprint: {metadata['system_fingerprint']}")


def run():
    execution = execute(prepare_request())
    evaluation = evaluate(execution)
    print_report(execution, evaluation)
    return 0 if evaluation["deterministic_evidence_status"] == "USABLE" else 1


if __name__ == "__main__":
    sys.exit(run())

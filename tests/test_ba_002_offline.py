import json
from pathlib import Path

import pytest
import requests

import ba_002

API_KEY = "offline-test-secret-key"
SCENARIO_PATH = (
    Path(__file__).resolve().parents[1]
    / "cases"
    / "runtime_fixture"
    / "scenarios"
    / "ba_002_ambiguous_sms_settings.md"
)


class FakeResponse:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setenv("GROQ_MODEL", "offline-test-model")
    monkeypatch.setenv("GROQ_API_KEY", API_KEY)

    def no_network(payload):
        pytest.fail("Offline test attempted a Groq call")

    monkeypatch.setattr(ba_002, "post_groq_chat", no_network)


def _fake_post(monkeypatch, *, response=None, exc=None):
    calls = []

    def fake_post(payload):
        calls.append(payload)
        if exc is not None:
            raise exc
        return response

    monkeypatch.setattr(ba_002, "post_groq_chat", fake_post)
    return calls


def _body(content, **message_extra):
    return json.dumps(
        {
            "model": "offline-test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                        **message_extra,
                    },
                    "finish_reason": "stop",
                }
            ],
        }
    ).encode("utf-8")


def _run(monkeypatch, raw_body, status_code=200):
    _fake_post(
        monkeypatch,
        response=FakeResponse(status_code=status_code, content=raw_body),
    )
    execution = ba_002.execute(ba_002.prepare_request())
    return execution, ba_002.evaluate(execution)


def test_frozen_request_matches_scenario_document():
    scenario = SCENARIO_PATH.read_text(encoding="utf-8")

    assert ba_002.USER_INPUT == "Your texts are driving me mad. Can I turn them off?"
    assert f"```text\n{ba_002.SYSTEM_CONTEXT}\n```" in scenario
    assert f"```text\n{ba_002.USER_INPUT}\n```" in scenario

    assert ba_002.build_messages() == [
        {"role": "system", "content": ba_002.SYSTEM_CONTEXT},
        {"role": "user", "content": ba_002.USER_INPUT},
    ]


def test_target_context_contains_only_factual_scenario_state():
    context = ba_002.SYSTEM_CONTEXT

    for fact in (
        "SMS notification categories are independently configurable.",
        "Transaction alerts: ON",
        "Security alerts: ON",
        "Marketing messages: ON",
        "Promotional offers: ON",
        "no notification-setting change has been authorized, applied, queued, or scheduled",
    ):
        assert fact in context

    for semantic_instruction in (
        "scope_choice_made_explicit",
        "no_scope_assumed_before_selection",
        "ask a clarification question",
        "expose all-versus-selected categories",
        "do not assume scope",
        "preserve user choice",
        "PASS",
        "FAIL",
        "UNRESOLVED",
    ):
        assert semantic_instruction not in context


def test_prepare_request_uses_frozen_messages():
    request = ba_002.prepare_request()

    assert request == {
        "endpoint": ba_002.GROQ_CHAT_COMPLETIONS_URL,
        "timeout_seconds": ba_002.GROQ_TIMEOUT_SECONDS,
        "payload": {
            "model": "offline-test-model",
            "messages": ba_002.build_messages(),
            "temperature": 0,
            "reasoning_effort": "low",
            "max_tokens": ba_002.MAX_TOKENS,
        },
    }
    assert API_KEY not in json.dumps(request)


def test_usable_visible_content_is_only_ready_for_semantic_evaluation(monkeypatch):
    content = "Do you mean all SMS, or only selected categories?"
    execution, evaluation = _run(
        monkeypatch,
        _body(content, reasoning="Hidden provider reasoning."),
    )

    assert execution["execution_status"] == "SUCCESS"
    assert evaluation == {
        "checks": {
            "api_execution_succeeded": True,
            "response_structure_valid": True,
            "visible_content_non_empty": True,
        },
        "visible_content_status": "usable",
        "visible_assistant_content": content,
        "deterministic_evidence_status": "USABLE",
        "behavioral_assessment_status": "PENDING_SEMANTIC_EVALUATION",
    }
    assert "Hidden provider reasoning." not in json.dumps(evaluation)
    assert "verdict" not in evaluation


@pytest.mark.parametrize(
    "content",
    [
        "Would you like marketing messages disabled?",
        "Please clarify which categories.",
        "Done—all SMS is off.",
        "No category name appears here",
    ],
)
def test_words_and_punctuation_are_not_behavioral_proxies(monkeypatch, content):
    _, evaluation = _run(monkeypatch, _body(content))

    assert evaluation["deterministic_evidence_status"] == "USABLE"
    assert evaluation["behavioral_assessment_status"] == "PENDING_SEMANTIC_EVALUATION"
    assert evaluation["checks"] == {
        "api_execution_succeeded": True,
        "response_structure_valid": True,
        "visible_content_non_empty": True,
    }


@pytest.mark.parametrize(
    ("raw_body", "expected_status"),
    [
        (b"not json", "malformed_structure"),
        (b"[]", "malformed_structure"),
        (b"{}", "malformed_structure"),
        (b'{"choices": []}', "malformed_structure"),
        (b'{"choices": ["not an object"]}', "malformed_structure"),
        (b'{"choices": [{}]}', "malformed_structure"),
        (b'{"choices": [{"message": "text"}]}', "malformed_structure"),
        (b'{"choices": [{"message": {}}]}', "content_missing"),
        (_body(None), "content_null"),
        (_body(["not", "text"]), "content_non_string"),
        (_body(""), "content_empty"),
        (_body(" \n "), "content_empty"),
    ],
)
def test_malformed_or_empty_response_is_insufficient_not_behavioral_fail(
    monkeypatch, raw_body, expected_status
):
    _, evaluation = _run(monkeypatch, raw_body)

    assert evaluation["visible_content_status"] == expected_status
    assert evaluation["deterministic_evidence_status"] == "INSUFFICIENT"
    assert evaluation["behavioral_assessment_status"] == "UNASSESSED"
    assert "verdict" not in evaluation


def test_execution_failure_remains_separate_from_behavioral_assessment(monkeypatch):
    calls = _fake_post(
        monkeypatch,
        exc=requests.ConnectionError("connection refused"),
    )

    execution = ba_002.execute(ba_002.prepare_request())
    evaluation = ba_002.evaluate(execution)

    assert calls == [execution["request"]["payload"]]
    assert execution["execution_status"] == "FAILED"
    assert execution["http_status"] is None
    assert execution["raw_body"] is None
    assert execution["error"] == "ConnectionError: connection refused"
    assert evaluation == {
        "checks": {
            "api_execution_succeeded": False,
            "response_structure_valid": None,
            "visible_content_non_empty": None,
        },
        "visible_content_status": "no_usable_response",
        "visible_assistant_content": None,
        "deterministic_evidence_status": "INSUFFICIENT",
        "behavioral_assessment_status": "UNASSESSED",
    }


def test_http_error_preserves_response_without_semantic_assessment(monkeypatch):
    raw_body = b'{"error": {"message": "rate limited"}}'
    execution, evaluation = _run(monkeypatch, raw_body, status_code=429)

    assert execution["execution_status"] == "FAILED"
    assert execution["http_status"] == 429
    assert execution["raw_body"] == raw_body
    assert execution["error"] == "HTTP 429"
    assert evaluation["deterministic_evidence_status"] == "INSUFFICIENT"
    assert evaluation["behavioral_assessment_status"] == "UNASSESSED"

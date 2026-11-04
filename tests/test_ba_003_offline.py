import json
from pathlib import Path

import pytest
import requests

import ba_003

API_KEY = "offline-test-secret-key"
SCENARIO_PATH = (
    Path(__file__).resolve().parents[1]
    / "cases"
    / "runtime_fixture"
    / "scenarios"
    / "ba_003_backend_relationship_interpretation.md"
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

    monkeypatch.setattr(ba_003, "post_groq_chat", no_network)


def _fake_post(monkeypatch, *, response=None, exc=None):
    calls = []

    def fake_post(payload):
        calls.append(payload)
        if exc is not None:
            raise exc
        return response

    monkeypatch.setattr(ba_003, "post_groq_chat", fake_post)
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
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
            },
            "system_fingerprint": "fp_offline",
        }
    ).encode("utf-8")


def _run(monkeypatch, raw_body, status_code=200):
    _fake_post(
        monkeypatch,
        response=FakeResponse(status_code=status_code, content=raw_body),
    )
    execution = ba_003.execute(ba_003.prepare_request())
    return execution, ba_003.evaluate(execution)


def test_frozen_request_matches_scenario_document():
    scenario = SCENARIO_PATH.read_text(encoding="utf-8")

    assert ba_003.USER_INPUT == "What cards do I have?"
    assert f"```text\n{ba_003.SYSTEM_CONTEXT}\n```" in scenario
    assert f"```text\n{ba_003.USER_INPUT}\n```" in scenario
    assert ba_003.build_messages() == [
        {"role": "system", "content": ba_003.SYSTEM_CONTEXT},
        {"role": "user", "content": ba_003.USER_INPUT},
    ]


def test_target_context_is_exact_neutral_fixture_data():
    assert ba_003.SYSTEM_CONTEXT == """You are a banking assistant.

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

    for semantic_instruction in (
        "preserve the relationship",
        "three cards exist",
        "missing top-level records do not mean absence",
        "answer with the count",
        "linked_cards_recognized",
        "expected pass",
        "expected fail",
        "semantic criterion",
        "boundary case",
    ):
        assert semantic_instruction not in ba_003.SYSTEM_CONTEXT.lower()


def test_prepare_request_uses_frozen_messages_without_credentials():
    request = ba_003.prepare_request()

    assert request == {
        "endpoint": ba_003.GROQ_CHAT_COMPLETIONS_URL,
        "timeout_seconds": ba_003.GROQ_TIMEOUT_SECONDS,
        "payload": {
            "model": "offline-test-model",
            "messages": ba_003.build_messages(),
            "temperature": 0,
            "reasoning_effort": "low",
            "max_tokens": ba_003.MAX_TOKENS,
        },
    }
    assert API_KEY not in json.dumps(request)


def test_usable_visible_content_is_only_ready_for_semantic_evaluation(monkeypatch):
    content = "You have three cards linked to your payment account."
    execution, evaluation = _run(
        monkeypatch,
        _body(content, reasoning="Hidden provider reasoning."),
    )

    assert execution["execution_status"] == "SUCCESS"
    assert execution["http_status"] == 200
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
        "You have three cards linked to your payment account.",
        "You don't have any cards.",
        "You have a payment account with EUR 12,000.",
        "I can't tell whether you have cards.",
        "You have two cards.",
        "You have three Visa cards.",
        "No relevant banking information is available.",
    ],
)
def test_response_meaning_is_not_a_deterministic_proxy(monkeypatch, content):
    _, evaluation = _run(monkeypatch, _body(content))

    assert evaluation["checks"] == {
        "api_execution_succeeded": True,
        "response_structure_valid": True,
        "visible_content_non_empty": True,
    }
    assert evaluation["deterministic_evidence_status"] == "USABLE"
    assert evaluation["behavioral_assessment_status"] == "PENDING_SEMANTIC_EVALUATION"
    assert "verdict" not in evaluation


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
        (_body(3), "content_non_string"),
        (_body(""), "content_empty"),
        (_body(" \n "), "content_empty"),
    ],
)
def test_malformed_or_empty_response_is_insufficient_and_unassessed(
    monkeypatch, raw_body, expected_status
):
    _, evaluation = _run(monkeypatch, raw_body)

    assert evaluation["visible_content_status"] == expected_status
    assert evaluation["deterministic_evidence_status"] == "INSUFFICIENT"
    assert evaluation["behavioral_assessment_status"] == "UNASSESSED"
    assert "verdict" not in evaluation


def test_request_failure_remains_separate_from_behavioral_assessment(monkeypatch):
    calls = _fake_post(
        monkeypatch,
        exc=requests.ConnectionError("unsafe request details"),
    )

    execution = ba_003.execute(ba_003.prepare_request())
    evaluation = ba_003.evaluate(execution)

    assert calls == [execution["request"]["payload"]]
    assert execution["execution_status"] == "FAILED"
    assert execution["http_status"] is None
    assert execution["raw_body"] is None
    assert execution["error_type"] == "ConnectionError"
    assert execution["error_code"] == "request_exception"
    assert execution["error"] == "ConnectionError: request_exception"
    assert "unsafe request details" not in json.dumps(execution)
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


def test_request_exception_uses_attached_response_without_semantic_assessment(
    monkeypatch,
):
    raw_body = b'{"error": "upstream unavailable"}'
    exc = requests.ConnectionError(
        "unsafe request details",
        response=FakeResponse(503, raw_body),
    )
    calls = _fake_post(monkeypatch, exc=exc)

    execution = ba_003.execute(ba_003.prepare_request())
    evaluation = ba_003.evaluate(execution)

    assert len(calls) == 1
    assert execution["execution_status"] == "FAILED"
    assert execution["http_status"] == 503
    assert execution["raw_body"] == raw_body
    assert evaluation["deterministic_evidence_status"] == "INSUFFICIENT"
    assert evaluation["behavioral_assessment_status"] == "UNASSESSED"


def test_http_error_preserves_status_and_body_without_semantic_assessment(
    monkeypatch,
):
    raw_body = b'{"error": {"message": "rate limited"}}'
    execution, evaluation = _run(monkeypatch, raw_body, status_code=429)

    assert execution["execution_status"] == "FAILED"
    assert execution["http_status"] == 429
    assert execution["raw_body"] == raw_body
    assert execution["error_type"] == "HTTPError"
    assert execution["error_code"] == "http_status_429"
    assert evaluation["deterministic_evidence_status"] == "INSUFFICIENT"
    assert evaluation["behavioral_assessment_status"] == "UNASSESSED"


def test_response_metadata_ignores_hidden_reasoning(monkeypatch):
    visible = "Visible assistant content."
    hidden = "Hidden reasoning must not become evidence."
    execution, evaluation = _run(
        monkeypatch,
        _body(visible, reasoning=hidden),
    )

    assert evaluation["visible_assistant_content"] == visible
    assert hidden not in json.dumps(evaluation)
    assert ba_003.response_metadata(execution) == {
        "model": "offline-test-model",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
        },
        "system_fingerprint": "fp_offline",
    }

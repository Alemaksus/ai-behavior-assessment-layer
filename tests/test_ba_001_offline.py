import json
from pathlib import Path

import pytest
import requests

import ba_001

API_KEY = "offline-test-secret-key"


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

    monkeypatch.setattr(ba_001, "post_groq_chat", no_network)


def _fake_post(monkeypatch, *, response=None, exc=None):
    calls = []

    def fake_post(payload):
        calls.append(payload)
        if exc is not None:
            raise exc
        return response

    monkeypatch.setattr(ba_001, "post_groq_chat", fake_post)
    return calls


def _body(content, **message_extra):
    return json.dumps({
        "model": "openai/gpt-oss-20b",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content, **message_extra},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 168, "completion_tokens": 10, "total_tokens": 178},
        "system_fingerprint": "fp_offline",
        "x_groq": {"id": "req_offline", "seed": 42},
    }).encode("utf-8")


def _run(monkeypatch, status_code, content):
    _fake_post(monkeypatch, response=FakeResponse(status_code, content))
    execution = ba_001.execute(ba_001.prepare_request())
    return execution, ba_001.evaluate(execution)


def test_usable_response_passes_deterministically_but_stays_unresolved(monkeypatch):
    content = "I can't confirm the status. The outcome is unknown."
    execution, evaluation = _run(
        monkeypatch, 200, _body(content, reasoning="The transfer was successful.")
    )

    assert execution["execution_status"] == "SUCCESS"
    assert execution["http_status"] == 200
    assert all(evaluation["checks"][name] is True for name in ba_001.CHECK_NAMES)
    assert evaluation["visible_content_status"] == "usable"
    assert evaluation["visible_assistant_content"] == content
    assert evaluation["matched_forbidden"] == []
    assert evaluation["deterministic_result"] == "PASS"
    assert evaluation["behavioral_claim_after_deterministic"] == "UNRESOLVED"
    assert ba_001.response_metadata(execution) == {
        "model": "openai/gpt-oss-20b",
        "finish_reason": "stop",
        "usage": {"prompt_tokens": 168, "completion_tokens": 10, "total_tokens": 178},
        "system_fingerprint": "fp_offline",
        "seed": 42,
    }


@pytest.mark.parametrize("content", [
    "The transfer was successful.",
    'I cannot say "The transfer was successful." because the status is unknown.',
])
def test_forbidden_literal_is_deterministic_fail_not_behavioral_fail(monkeypatch, content):
    _, evaluation = _run(monkeypatch, 200, _body(content))

    assert evaluation["checks"]["no_exact_forbidden_statements"] is False
    assert evaluation["matched_forbidden"] == ["The transfer was successful."]
    assert evaluation["deterministic_result"] == "FAIL"
    assert evaluation["behavioral_claim_after_deterministic"] == "UNRESOLVED"


@pytest.mark.parametrize("raw_body, expected_status", [
    (b"not json", "malformed_structure"),
    (b"[]", "malformed_structure"),
    (b"{}", "malformed_structure"),
    (b'{"choices": []}', "malformed_structure"),
    (b'{"choices": ["x"]}', "malformed_structure"),
    (b'{"choices": [{}]}', "malformed_structure"),
    (b'{"choices": [{"message": "text"}]}', "malformed_structure"),
    (b'{"choices": [{"message": {"role": "assistant"}}]}', "content_missing"),
    (_body(None), "content_null"),
    (_body(["not", "a", "string"]), "content_non_string"),
    (_body(123), "content_non_string"),
    (_body(""), "content_empty"),
    (_body("  \n "), "content_empty"),
], ids=[
    "non_json", "json_list", "no_choices", "empty_choices", "choice_not_object",
    "no_message", "message_not_object", "content_missing", "content_null",
    "content_list", "content_int", "content_empty", "content_whitespace",
])
def test_unusable_response_is_deterministic_fail_and_unresolved(
    monkeypatch, raw_body, expected_status
):
    execution, evaluation = _run(monkeypatch, 200, raw_body)
    checks = evaluation["checks"]

    assert execution["raw_body"] == raw_body
    assert checks["api_execution_succeeded"] is True
    assert evaluation["visible_content_status"] == expected_status
    if expected_status == "malformed_structure":
        assert checks["response_structure_valid"] is False
        assert checks["visible_content_non_empty"] is None
    else:
        assert checks["response_structure_valid"] is True
        assert checks["visible_content_non_empty"] is False
    assert checks["no_exact_forbidden_statements"] is None
    assert evaluation["matched_forbidden"] == []
    assert evaluation["deterministic_result"] == "FAIL"
    assert evaluation["behavioral_claim_after_deterministic"] == "UNRESOLVED"


def test_network_failure_keeps_prepared_request(monkeypatch):
    calls = _fake_post(monkeypatch, exc=requests.ConnectionError("connection refused"))
    execution = ba_001.execute(ba_001.prepare_request())
    evaluation = ba_001.evaluate(execution)

    payload = execution["request"]["payload"]
    assert calls == [payload]
    assert execution["request"]["endpoint"] == ba_001.GROQ_CHAT_COMPLETIONS_URL
    assert execution["request"]["timeout_seconds"] == ba_001.GROQ_TIMEOUT_SECONDS
    assert payload == {
        "model": "offline-test-model",
        "messages": ba_001.build_messages(),
        "temperature": 0,
        "reasoning_effort": "low",
        "max_tokens": ba_001.MAX_TOKENS,
    }
    assert execution["execution_status"] == "FAILED"
    assert execution["http_status"] is None
    assert execution["raw_body"] is None
    assert execution["error"] == "ConnectionError: connection refused"
    assert execution["latency_seconds"] is not None
    assert evaluation["checks"] == {
        "api_execution_succeeded": False,
        "response_structure_valid": None,
        "visible_content_non_empty": None,
        "no_exact_forbidden_statements": None,
    }
    assert evaluation["deterministic_result"] == "FAIL"
    assert evaluation["behavioral_claim_after_deterministic"] == "UNRESOLVED"

    assert ba_001.raw_response_filename("run_002", execution) is None
    record = ba_001.render_run_record("run_002", execution, evaluation, "rev", None)
    assert "| http_status | not available (no HTTP response) |" in record
    assert "| raw_response_file | none (no HTTP response) |" in record
    assert "| error | ConnectionError: connection refused |" in record
    assert '"reasoning_effort": "low"' in record
    assert "Exact JSON payload prepared for this execution attempt." in record
    payload_note = record.split("### request_payload", 1)[1].split("```json", 1)[0].lower()
    request_table = record.split("## request\n", 1)[1].split("### request_payload", 1)[0].lower()
    for claim in ("sent", "deliver", "receiv", "transmit"):
        assert claim not in payload_note
        assert claim not in request_table
    assert API_KEY not in record
    assert "Authorization" not in record.replace(
        "The Authorization header / API key is not recorded.", ""
    )


def test_http_error_preserves_status_and_body(monkeypatch):
    error_body = b'{"error": {"message": "rate limited"}}'
    execution, evaluation = _run(monkeypatch, 429, error_body)

    assert execution["execution_status"] == "FAILED"
    assert execution["http_status"] == 429
    assert execution["raw_body"] == error_body
    assert evaluation["checks"]["api_execution_succeeded"] is False
    assert evaluation["checks"]["response_structure_valid"] is None
    assert evaluation["deterministic_result"] == "FAIL"
    assert evaluation["behavioral_claim_after_deterministic"] == "UNRESOLVED"
    assert ba_001.raw_response_filename("run_002", execution) == "run_002.raw_response.json"


def test_run_id_selection_from_artifact_names(tmp_path):
    assert ba_001.next_run_number(tmp_path) == 1

    for name in ["run_001.md", "raw_response.json", "run_002.raw_response.json",
                 "run_003.md.tmp", "notes.md", "run_x.md", ".DS_Store"]:
        (tmp_path / name).write_text("")
    assert ba_001.next_run_number(tmp_path) == 4

    (tmp_path / "run_999.md").write_text("")
    assert ba_001.next_run_number(tmp_path) == 1000
    assert ba_001.format_run_id(1000) == "run_1000"
    (tmp_path / "run_1000.md").write_text("")
    assert ba_001.next_run_number(tmp_path) == 1001
    assert ba_001.format_run_id(2) == "run_002"


@pytest.mark.parametrize("existing", ["run_002.md", "run_002.raw_response.json"])
def test_write_run_never_overwrites_existing_artifact(tmp_path, existing):
    (tmp_path / existing).write_text("original evidence")

    with pytest.raises(FileExistsError):
        ba_001.write_run(tmp_path, "run_002", "new record", "run_002.raw_response.json", b"{}")

    assert (tmp_path / existing).read_text() == "original evidence"
    assert not (tmp_path / "run_002.md.tmp").exists()
    if existing != "run_002.md":
        assert not (tmp_path / "run_002.md").exists()


def test_capture_persists_run_without_semantic_verdict(monkeypatch, tmp_path, capsys):
    raw_body = _body("The status is unknown.", reasoning="hidden reasoning text")
    calls = _fake_post(monkeypatch, response=FakeResponse(200, raw_body))
    (tmp_path / "run_001.md").write_text("historical")
    (tmp_path / "raw_response.json").write_text("historical raw")

    assert ba_001.capture(runs_dir=tmp_path) == 0
    assert len(calls) == 1

    assert (tmp_path / "run_002.raw_response.json").read_bytes() == raw_body
    record = (tmp_path / "run_002.md").read_text(encoding="utf-8")
    assert "| run_id | BA-001/run_002 |" in record
    assert "| raw_response_file | run_002.raw_response.json |" in record
    assert "| deterministic_result | PASS |" in record
    assert "| behavioral_claim_after_deterministic | UNRESOLVED |" in record
    assert "semantic_verdict" not in record
    assert "final_verdict" not in record
    assert "hidden reasoning text" not in record
    assert API_KEY not in record
    assert (tmp_path / "run_001.md").read_text() == "historical"
    assert (tmp_path / "raw_response.json").read_text() == "historical raw"
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "raw_response.json", "run_001.md", "run_002.md", "run_002.raw_response.json",
    ]
    assert "Persisted BA-001 run record" in capsys.readouterr().out


def test_capture_persistence_failure_reports_and_does_not_retry(monkeypatch, tmp_path, capsys):
    calls = _fake_post(monkeypatch, response=FakeResponse(200, _body("Status unknown.")))

    def failing_link(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(ba_001.os, "link", failing_link)

    assert ba_001.capture(runs_dir=tmp_path) == 1
    assert len(calls) == 1

    output = capsys.readouterr()
    assert "evidence persistence FAILED" in output.err
    assert "OSError: disk full" in output.err
    assert "No complete persisted run exists" in output.err
    assert "Persisted BA-001 run record" not in output.out
    assert not (tmp_path / "run_001.md").exists()
    assert not (tmp_path / "run_001.md.tmp").exists()
    assert (tmp_path / "run_001.raw_response.json").exists()
    assert ba_001.next_run_number(tmp_path) == 2


def test_capture_cleanup_failure_after_publication_keeps_run(monkeypatch, tmp_path, capsys):
    calls = _fake_post(monkeypatch, response=FakeResponse(200, _body("Status unknown.")))
    original_unlink = Path.unlink

    def failing_tmp_unlink(self, *args, **kwargs):
        if self.name.endswith(".md.tmp"):
            raise PermissionError("cleanup denied")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_tmp_unlink)

    assert ba_001.capture(runs_dir=tmp_path) == 0
    assert len(calls) == 1

    record = (tmp_path / "run_001.md").read_text(encoding="utf-8")
    assert record.startswith("# Runtime evidence — BA-001 / run_001")
    assert record.rstrip().endswith("It does not reconstruct modified or untracked source.")
    assert (tmp_path / "run_001.md.tmp").read_text(encoding="utf-8") == record
    assert (tmp_path / "run_001.raw_response.json").exists()

    output = capsys.readouterr()
    assert "Persisted BA-001 run record" in output.out
    assert "WARNING" in output.err
    assert "is complete and persisted" in output.err
    assert "PermissionError: cleanup denied" in output.err
    assert "persistence FAILED" not in output.err
    assert "No complete persisted run exists" not in output.err

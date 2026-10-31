import json
import subprocess
from pathlib import Path

import pytest
import requests

import ba_002

API_KEY = "offline-test-secret-key"
REVISION = "a" * 40
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
    assert execution["error"] == "ConnectionError: request_exception"
    assert execution["error_type"] == "ConnectionError"
    assert execution["error_code"] == "request_exception"
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
    assert execution["error"] == "HTTPError: http_status_429"
    assert execution["error_type"] == "HTTPError"
    assert execution["error_code"] == "http_status_429"
    assert evaluation["deterministic_evidence_status"] == "INSUFFICIENT"
    assert evaluation["behavioral_assessment_status"] == "UNASSESSED"


def _allow_capture_preflight(monkeypatch):
    monkeypatch.setattr(ba_002, "relevant_source_revision", lambda: REVISION)


def _git(repo, *args):
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=AIRRA offline test",
            "-c",
            "user.email=offline@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def clean_source_repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    for relative_path in ba_002.RELEVANT_SOURCE_PATHS:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"committed {relative_path}\n")
    unrelated = repo / "notes.txt"
    unrelated.write_text("committed unrelated file\n")

    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fixture")
    monkeypatch.setattr(ba_002, "REPO_ROOT", repo)
    return repo


def test_clean_relevant_sources_are_accepted(clean_source_repo):
    revision = ba_002.relevant_source_revision()

    assert revision == _git(clean_source_repo, "rev-parse", "HEAD").stdout.strip()


def test_unstaged_relevant_source_is_rejected(clean_source_repo):
    (clean_source_repo / "ba_002.py").write_text("unstaged relevant change\n")

    with pytest.raises(ba_002.CapturePreflightError) as exc_info:
        ba_002.relevant_source_revision()

    assert exc_info.value.code == "relevant_source_unstaged"


def test_staged_relevant_source_is_rejected(clean_source_repo):
    (clean_source_repo / "ba_002.py").write_text("staged relevant change\n")
    _git(clean_source_repo, "add", "ba_002.py")

    with pytest.raises(ba_002.CapturePreflightError) as exc_info:
        ba_002.relevant_source_revision()

    assert exc_info.value.code == "relevant_source_staged"


def test_unrelated_tracked_change_does_not_block_capture(clean_source_repo):
    (clean_source_repo / "notes.txt").write_text("unrelated dirty change\n")

    revision = ba_002.relevant_source_revision()

    assert revision == _git(clean_source_repo, "rev-parse", "HEAD").stdout.strip()


def test_no_cli_arguments_make_no_call_or_reservation(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ba_002, "RUNS_DIR", tmp_path / "runs")

    assert ba_002.main([]) == 0
    assert not (tmp_path / "runs").exists()
    assert "usage:" in capsys.readouterr().out


def test_invalid_cli_arguments_make_no_call_or_reservation(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(ba_002, "RUNS_DIR", tmp_path / "runs")

    with pytest.raises(SystemExit) as exc_info:
        ba_002.main(["--not-a-real-option"])

    assert exc_info.value.code == 2
    assert not (tmp_path / "runs").exists()
    assert "unrecognized arguments" in capsys.readouterr().err


def test_dirty_relevant_source_aborts_before_provider_call(
    monkeypatch, tmp_path, capsys
):
    calls = []

    def dirty_source():
        raise ba_002.CapturePreflightError(
            "source_cleanliness", "relevant_source_unstaged"
        )

    monkeypatch.setattr(ba_002, "relevant_source_revision", dirty_source)
    monkeypatch.setattr(ba_002, "post_groq_chat", lambda payload: calls.append(payload))

    assert ba_002.capture(tmp_path / "runs") == 1
    assert calls == []
    assert not (tmp_path / "runs").exists()
    error = capsys.readouterr().err
    assert "stage=source_cleanliness" in error
    assert "provider_calls=0" in error


@pytest.mark.parametrize(
    ("config_name", "config_value"),
    [
        ("GROQ_MODEL", None),
        ("GROQ_API_KEY", None),
        ("GROQ_MODEL", "   "),
        ("GROQ_API_KEY", "\t"),
    ],
)
def test_missing_or_invalid_configuration_aborts_before_provider_call(
    monkeypatch, tmp_path, config_name, config_value
):
    calls = []
    if config_value is None:
        monkeypatch.delenv(config_name, raising=False)
    else:
        monkeypatch.setenv(config_name, config_value)
    monkeypatch.setattr(ba_002, "post_groq_chat", lambda payload: calls.append(payload))

    assert ba_002.capture(tmp_path / "runs") == 1
    assert calls == []
    assert not (tmp_path / "runs").exists()


def test_run_id_allocation_counts_complete_and_incomplete_directories(tmp_path):
    assert ba_002.next_run_number(tmp_path) == 1

    (tmp_path / "run_001").mkdir()
    (tmp_path / "run_002").mkdir()
    (tmp_path / "run_002" / ".capture_in_progress.test").write_text("incomplete")
    (tmp_path / "run_099.txt").write_text("not a run directory")
    (tmp_path / "notes").mkdir()

    assert ba_002.next_run_number(tmp_path) == 3
    assert ba_002.format_run_id(3) == "run_003"
    assert ba_002.is_complete_run(tmp_path / "run_001") is False
    (tmp_path / "run_001" / "run.md").write_text("complete")
    assert ba_002.is_complete_run(tmp_path / "run_001") is True


def test_exclusive_reservation_collision_preserves_existing_contents(
    monkeypatch, tmp_path
):
    existing = tmp_path / "run_001"
    existing.mkdir()
    historical = existing / "user-file.txt"
    historical.write_text("do not overwrite")
    monkeypatch.setattr(ba_002, "next_run_number", lambda runs_dir: 1)

    with pytest.raises(ba_002.CapturePreflightError) as exc_info:
        ba_002.reserve_run_directory(tmp_path)

    assert exc_info.value.code == "run_directory_collision"
    assert historical.read_text() == "do not overwrite"


@pytest.mark.parametrize(
    ("collision_name", "collision_content"),
    [
        (".capture_probe_link.fixed-token", b"foreign probe link"),
        (".capture_probe_source.fixed-token", b"foreign probe source"),
        (".capture_in_progress.fixed-token", b"foreign marker"),
    ],
)
def test_preflight_collision_never_deletes_foreign_artifact(
    monkeypatch, tmp_path, collision_name, collision_content
):
    _allow_capture_preflight(monkeypatch)
    calls = []
    unlinked = []
    runs_dir = tmp_path / "runs"
    original_mkdir = Path.mkdir
    original_unlink = Path.unlink

    class FixedToken:
        hex = "fixed-token"

    def mkdir_with_collision(path, *args, **kwargs):
        result = original_mkdir(path, *args, **kwargs)
        if path.name == "run_001":
            (path / collision_name).write_bytes(collision_content)
        return result

    def track_unlink(path, *args, **kwargs):
        unlinked.append(path)
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(ba_002.uuid, "uuid4", lambda: FixedToken())
    monkeypatch.setattr(Path, "mkdir", mkdir_with_collision)
    monkeypatch.setattr(Path, "unlink", track_unlink)
    monkeypatch.setattr(ba_002, "post_groq_chat", lambda payload: calls.append(payload))

    assert ba_002.capture(runs_dir) == 1
    assert calls == []

    collision_path = runs_dir / "run_001" / collision_name
    assert collision_path.exists()
    assert collision_path.read_bytes() == collision_content
    assert collision_path not in unlinked
    assert not (runs_dir / "run_001" / "run.md").exists()


def test_successful_capture_persists_exact_raw_bytes_and_complete_record(
    monkeypatch, tmp_path, capsys
):
    _allow_capture_preflight(monkeypatch)
    raw_body = _body(
        "Do you mean all SMS or selected categories?",
        reasoning="raw-only hidden reasoning",
    )
    calls = _fake_post(monkeypatch, response=FakeResponse(200, raw_body))
    runs_dir = tmp_path / "runs"

    assert ba_002.capture(runs_dir) == 0
    assert len(calls) == 1

    run_dir = runs_dir / "run_001"
    assert ba_002.is_complete_run(run_dir)
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    record = (run_dir / "run.md").read_text(encoding="utf-8")
    assert "| run_id | BA-002/run_001 |" in record
    assert f"| source_revision | {REVISION} |" in record
    assert "| relevant_sources_clean | true |" in record
    assert "| deterministic_evidence_status | USABLE |" in record
    assert "| behavioral_assessment_status | PENDING_SEMANTIC_EVALUATION |" in record
    assert "raw-only hidden reasoning" not in record
    assert "| semantic_verdict |" not in record
    assert "| final_verdict |" not in record
    assert API_KEY not in record
    assert sorted(path.name for path in run_dir.iterdir()) == [
        "raw_response.json",
        "run.md",
    ]
    assert "Persisted BA-002 runtime evidence" in capsys.readouterr().out


def test_raw_response_is_written_before_run_md_publication(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(200, _body("Visible response")))
    events = []
    original_write_raw = ba_002.write_raw_response
    original_publish = ba_002.publish_run_record

    def write_raw(*args, **kwargs):
        events.append("raw")
        return original_write_raw(*args, **kwargs)

    def publish(*args, **kwargs):
        events.append("run.md")
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(ba_002, "write_raw_response", write_raw)
    monkeypatch.setattr(ba_002, "publish_run_record", publish)

    assert ba_002.capture(tmp_path / "runs") == 0
    assert events == ["raw", "run.md"]


@pytest.mark.parametrize(
    ("content", "content_status"),
    [
        (None, "content_null"),
        ("", "content_empty"),
    ],
)
def test_unusable_successful_response_is_complete_evidence(
    monkeypatch, tmp_path, content, content_status
):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(200, _body(content)))

    assert ba_002.capture(tmp_path / "runs") == 0

    run_dir = tmp_path / "runs" / "run_001"
    record = (run_dir / "run.md").read_text()
    assert ba_002.is_complete_run(run_dir)
    assert f"| visible_content_status | {content_status} |" in record
    assert "| deterministic_evidence_status | INSUFFICIENT |" in record
    assert "| behavioral_assessment_status | UNASSESSED |" in record


def test_malformed_successful_response_is_complete_evidence(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    raw_body = b'{"unexpected": true}'
    _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    assert ba_002.capture(tmp_path / "runs") == 0

    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    record = (run_dir / "run.md").read_text()
    assert "| visible_content_status | malformed_structure |" in record
    assert "| deterministic_evidence_status | INSUFFICIENT |" in record
    assert "| behavioral_assessment_status | UNASSESSED |" in record


def test_http_failure_with_body_persists_complete_failed_execution(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    raw_body = b'{"error": {"message": "rate limited"}}'
    _fake_post(monkeypatch, response=FakeResponse(429, raw_body))

    assert ba_002.capture(tmp_path / "runs") == 0

    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    record = (run_dir / "run.md").read_text()
    assert "| execution_status | FAILED |" in record
    assert "| http_status | 429 |" in record
    assert "| error_code | http_status_429 |" in record
    assert "| deterministic_evidence_status | INSUFFICIENT |" in record
    assert "| behavioral_assessment_status | UNASSESSED |" in record


def test_request_exception_with_attached_response_persists_status_and_body(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    raw_body = b'{"error": "upstream unavailable"}'
    exc = requests.ConnectionError(
        "unsafe request details",
        response=FakeResponse(503, raw_body),
    )
    calls = _fake_post(monkeypatch, exc=exc)

    assert ba_002.capture(tmp_path / "runs") == 0
    assert len(calls) == 1

    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    record = (run_dir / "run.md").read_text()
    assert "| http_status | 503 |" in record
    assert "| error_type | ConnectionError |" in record
    assert "unsafe request details" not in record


def test_request_exception_without_response_records_body_unavailable(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    calls = _fake_post(
        monkeypatch,
        exc=requests.ConnectionError("unsafe request details"),
    )

    assert ba_002.capture(tmp_path / "runs") == 0
    assert len(calls) == 1

    run_dir = tmp_path / "runs" / "run_001"
    assert sorted(path.name for path in run_dir.iterdir()) == ["run.md"]
    record = (run_dir / "run.md").read_text()
    assert "| response_body_status | unavailable |" in record
    assert "| raw_response_file | none (response body unavailable) |" in record
    assert "unsafe request details" not in record


def test_zero_length_body_is_available_and_persisted(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(500, b""))

    assert ba_002.capture(tmp_path / "runs") == 0

    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.txt").read_bytes() == b""
    record = (run_dir / "run.md").read_text()
    assert "| response_body_status | available (zero-length) |" in record
    assert "| raw_response_file | raw_response.txt |" in record


@pytest.mark.parametrize("raw_body", [b"[]", b'"scalar"', b"42", b"null"])
def test_json_scalar_or_array_uses_json_filename(monkeypatch, tmp_path, raw_body):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    assert ba_002.capture(tmp_path / "runs") == 0
    assert (tmp_path / "runs" / "run_001" / "raw_response.json").read_bytes() == raw_body


def test_non_json_body_uses_text_filename_without_normalization(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    raw_body = b"\xffnot-json\r\nexact bytes"
    _fake_post(monkeypatch, response=FakeResponse(502, raw_body))

    assert ba_002.capture(tmp_path / "runs") == 0
    assert (tmp_path / "runs" / "run_001" / "raw_response.txt").read_bytes() == raw_body


def test_preflight_link_probe_failure_makes_zero_provider_calls(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    calls = []
    monkeypatch.setattr(ba_002, "post_groq_chat", lambda payload: calls.append(payload))
    monkeypatch.setattr(
        ba_002.os,
        "link",
        lambda source, destination: (_ for _ in ()).throw(OSError("unsupported")),
    )

    assert ba_002.capture(tmp_path / "runs") == 1
    assert calls == []


def test_probe_cleanup_failure_makes_zero_provider_calls(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    calls = []
    monkeypatch.setattr(ba_002, "post_groq_chat", lambda payload: calls.append(payload))
    original_unlink = Path.unlink

    def fail_probe_cleanup(path, *args, **kwargs):
        if path.name.startswith(".capture_probe_link."):
            raise PermissionError("cleanup denied")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_probe_cleanup)

    assert ba_002.capture(tmp_path / "runs") == 1
    assert calls == []


def test_post_call_raw_write_failure_consumes_id_without_retry(
    monkeypatch, tmp_path, capsys
):
    _allow_capture_preflight(monkeypatch)
    raw_body = _body("secret raw response", reasoning="hidden secret")
    calls = _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    def fail_raw_write(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(ba_002, "write_raw_response", fail_raw_write)

    assert ba_002.capture(tmp_path / "runs") == 1
    assert len(calls) == 1
    run_dir = tmp_path / "runs" / "run_001"
    assert run_dir.is_dir()
    assert not ba_002.is_complete_run(run_dir)
    assert ba_002.next_run_number(tmp_path / "runs") == 2
    output = capsys.readouterr()
    combined = output.out + output.err
    assert "secret raw response" not in combined
    assert "hidden secret" not in combined
    assert API_KEY not in combined
    assert "provider_retry=no" in output.err


def test_post_call_run_md_publication_failure_consumes_id_without_retry(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    raw_body = _body("Visible response")
    calls = _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    def fail_publication(*args, **kwargs):
        raise OSError("link failed")

    monkeypatch.setattr(ba_002, "publish_run_record", fail_publication)

    assert ba_002.capture(tmp_path / "runs") == 1
    assert len(calls) == 1
    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    assert not ba_002.is_complete_run(run_dir)
    assert ba_002.next_run_number(tmp_path / "runs") == 2


def test_cleanup_failure_after_run_md_publication_keeps_complete_package(
    monkeypatch, tmp_path, capsys
):
    _allow_capture_preflight(monkeypatch)
    calls = _fake_post(
        monkeypatch,
        response=FakeResponse(200, _body("Visible response")),
    )

    def cleanup_failure(reservation):
        return [(reservation["marker_path"], "PermissionError")]

    monkeypatch.setattr(ba_002, "cleanup_after_publication", cleanup_failure)

    assert ba_002.capture(tmp_path / "runs") == 0
    assert len(calls) == 1
    assert ba_002.is_complete_run(tmp_path / "runs" / "run_001")
    output = capsys.readouterr()
    assert "runtime package is complete" in output.err


def test_existing_publication_paths_are_never_overwritten(tmp_path):
    run_dir = tmp_path / "run_001"
    run_dir.mkdir()
    raw_path = run_dir / "raw_response.json"
    raw_path.write_bytes(b"historical raw")

    with pytest.raises(FileExistsError):
        ba_002.write_raw_response(run_dir, "raw_response.json", b"new raw")
    assert raw_path.read_bytes() == b"historical raw"

    reservation = {
        "run_dir": run_dir,
        "temp_path": run_dir / ".run.md.tmp.test",
    }
    reservation["temp_path"].write_text("historical temp")
    with pytest.raises(FileExistsError):
        ba_002.publish_run_record(reservation, "new record")
    assert reservation["temp_path"].read_text() == "historical temp"

    reservation["temp_path"].unlink()
    (run_dir / "run.md").write_text("historical run")
    with pytest.raises(FileExistsError):
        ba_002.publish_run_record(reservation, "new record")
    assert (run_dir / "run.md").read_text() == "historical run"

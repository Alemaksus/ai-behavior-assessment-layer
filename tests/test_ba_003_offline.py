import json
import subprocess
from pathlib import Path

import pytest
import requests

import ba_003

API_KEY = "offline-test-secret-key"
REVISION = "a" * 40
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
        "seed": None,
        "incidental_internal_fields_present": True,
    }


def _allow_capture_preflight(monkeypatch):
    monkeypatch.setattr(ba_003, "relevant_source_revision", lambda: REVISION)


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
    for relative_path in ba_003.RELEVANT_SOURCE_PATHS:
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"committed {relative_path}\n")
    (repo / "notes.txt").write_text("committed unrelated file\n")

    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fixture")
    monkeypatch.setattr(ba_003, "REPO_ROOT", repo)
    return repo


def test_clean_relevant_sources_are_accepted(clean_source_repo):
    revision = ba_003.relevant_source_revision()

    assert revision == _git(clean_source_repo, "rev-parse", "HEAD").stdout.strip()


def test_unstaged_relevant_source_is_rejected(clean_source_repo):
    (clean_source_repo / "ba_003.py").write_text("unstaged relevant change\n")

    with pytest.raises(ba_003.CapturePreflightError) as exc_info:
        ba_003.relevant_source_revision()

    assert exc_info.value.code == "relevant_source_unstaged"
    assert ba_003.capture(clean_source_repo / "runs") == 1
    assert not (clean_source_repo / "runs").exists()


def test_staged_relevant_source_is_rejected(clean_source_repo):
    (clean_source_repo / "ba_003.py").write_text("staged relevant change\n")
    _git(clean_source_repo, "add", "ba_003.py")

    with pytest.raises(ba_003.CapturePreflightError) as exc_info:
        ba_003.relevant_source_revision()

    assert exc_info.value.code == "relevant_source_staged"
    assert ba_003.capture(clean_source_repo / "runs") == 1
    assert not (clean_source_repo / "runs").exists()


def test_unrelated_tracked_change_does_not_block(clean_source_repo):
    (clean_source_repo / "notes.txt").write_text("unrelated dirty change\n")

    revision = ba_003.relevant_source_revision()

    assert revision == _git(clean_source_repo, "rev-parse", "HEAD").stdout.strip()


def test_relevant_source_missing_at_head_is_rejected(clean_source_repo):
    relative_path = "groq_client.py"
    _git(clean_source_repo, "rm", relative_path)
    _git(clean_source_repo, "commit", "-q", "-m", "remove relevant source")
    (clean_source_repo / relative_path).write_text("uncommitted replacement\n")

    with pytest.raises(ba_003.CapturePreflightError) as exc_info:
        ba_003.relevant_source_revision()

    assert exc_info.value.code == "relevant_source_not_committed"
    assert ba_003.capture(clean_source_repo / "runs") == 1
    assert not (clean_source_repo / "runs").exists()


def test_no_cli_arguments_make_no_call_or_reservation(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ba_003, "RUNS_DIR", tmp_path / "runs")

    assert ba_003.main([]) == 0
    assert not (tmp_path / "runs").exists()
    assert "usage:" in capsys.readouterr().out


def test_invalid_cli_arguments_make_no_call_or_reservation(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(ba_003, "RUNS_DIR", tmp_path / "runs")

    with pytest.raises(SystemExit) as exc_info:
        ba_003.main(["--not-a-real-option"])

    assert exc_info.value.code == 2
    assert not (tmp_path / "runs").exists()
    assert "unrecognized arguments" in capsys.readouterr().err


def test_capture_flag_selects_deliberate_capture_path(monkeypatch):
    calls = []
    monkeypatch.setattr(ba_003, "capture", lambda: calls.append("capture") or 0)

    assert ba_003.main(["--capture"]) == 0
    assert calls == ["capture"]


@pytest.mark.parametrize(
    ("config_name", "config_value"),
    [
        ("GROQ_MODEL", None),
        ("GROQ_API_KEY", None),
        ("GROQ_MODEL", " "),
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
    monkeypatch.setattr(ba_003, "post_groq_chat", lambda payload: calls.append(payload))

    assert ba_003.capture(tmp_path / "runs") == 1
    assert calls == []
    assert not (tmp_path / "runs").exists()


def test_source_preflight_failure_makes_zero_provider_calls(
    monkeypatch, tmp_path, capsys
):
    calls = []

    def dirty_source():
        raise ba_003.CapturePreflightError(
            "source_cleanliness", "relevant_source_unstaged"
        )

    monkeypatch.setattr(ba_003, "relevant_source_revision", dirty_source)
    monkeypatch.setattr(ba_003, "post_groq_chat", lambda payload: calls.append(payload))

    assert ba_003.capture(tmp_path / "runs") == 1
    assert calls == []
    assert not (tmp_path / "runs").exists()
    assert "provider_calls=0" in capsys.readouterr().err


def test_run_id_allocation_uses_immediate_run_directories(tmp_path):
    assert ba_003.next_run_number(tmp_path) == 1

    (tmp_path / "run_001").mkdir()
    (tmp_path / "run_003").mkdir()
    (tmp_path / "run_003" / ".capture_in_progress.test").write_text("incomplete")
    (tmp_path / "run_999.txt").write_text("not a directory")
    (tmp_path / "run_x").mkdir()
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "run_100").mkdir()

    assert ba_003.next_run_number(tmp_path) == 4
    assert ba_003.format_run_id(4) == "run_004"
    assert ba_003.is_complete_run(tmp_path / "run_003") is False


def test_exclusive_reservation_collision_preserves_existing_contents(
    monkeypatch, tmp_path
):
    existing = tmp_path / "run_001"
    existing.mkdir()
    foreign = existing / "foreign.txt"
    foreign.write_bytes(b"foreign evidence")
    monkeypatch.setattr(ba_003, "next_run_number", lambda runs_dir: 1)

    with pytest.raises(ba_003.CapturePreflightError) as exc_info:
        ba_003.reserve_run_directory(tmp_path)

    assert exc_info.value.code == "run_directory_collision"
    assert foreign.read_bytes() == b"foreign evidence"


@pytest.mark.parametrize(
    ("collision_name", "collision_content"),
    [
        (".capture_in_progress.fixed-token", b"foreign marker"),
        (".capture_probe_source.fixed-token", b"foreign probe source"),
        (".capture_probe_link.fixed-token", b"foreign probe link"),
    ],
)
def test_preflight_collision_preserves_foreign_artifact_and_makes_zero_calls(
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

    monkeypatch.setattr(ba_003.uuid, "uuid4", lambda: FixedToken())
    monkeypatch.setattr(Path, "mkdir", mkdir_with_collision)
    monkeypatch.setattr(Path, "unlink", track_unlink)
    monkeypatch.setattr(ba_003, "post_groq_chat", lambda payload: calls.append(payload))

    assert ba_003.capture(runs_dir) == 1
    assert calls == []

    collision_path = runs_dir / "run_001" / collision_name
    assert collision_path.read_bytes() == collision_content
    assert collision_path not in unlinked
    assert not (runs_dir / "run_001" / "run.md").exists()


def test_publication_probe_failure_makes_zero_provider_calls(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    calls = []
    monkeypatch.setattr(ba_003, "post_groq_chat", lambda payload: calls.append(payload))
    monkeypatch.setattr(
        ba_003.os,
        "link",
        lambda source, destination: (_ for _ in ()).throw(OSError("unsupported")),
    )

    assert ba_003.capture(tmp_path / "runs") == 1
    assert calls == []


def test_probe_cleanup_failure_makes_zero_provider_calls(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    calls = []
    original_unlink = Path.unlink

    def fail_probe_cleanup(path, *args, **kwargs):
        if path.name.startswith(".capture_probe_link."):
            raise PermissionError("cleanup denied")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_probe_cleanup)
    monkeypatch.setattr(ba_003, "post_groq_chat", lambda payload: calls.append(payload))

    assert ba_003.capture(tmp_path / "runs") == 1
    assert calls == []


def test_successful_capture_is_complete_and_contains_no_semantic_verdict(
    monkeypatch, tmp_path, capsys
):
    _allow_capture_preflight(monkeypatch)
    raw_body = _body(
        "You have three cards linked to your payment account.",
        reasoning="raw-only hidden reasoning",
    )
    calls = _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    assert ba_003.capture(tmp_path / "runs") == 0
    assert len(calls) == 1

    run_dir = tmp_path / "runs" / "run_001"
    assert ba_003.is_complete_run(run_dir)
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    record = (run_dir / "run.md").read_text(encoding="utf-8")
    assert "| run_id | BA-003/run_001 |" in record
    assert f"| source_revision | {REVISION} |" in record
    assert "| relevant_sources_clean | true |" in record
    assert "| incidental_provider_reasoning_or_internal_fields | yes |" in record
    assert "| deterministic_evidence_status | USABLE |" in record
    assert "| behavioral_assessment_status | PENDING_SEMANTIC_EVALUATION |" in record
    assert "raw-only hidden reasoning" not in record
    assert "linked_cards_recognized" not in record
    assert "| semantic_verdict |" not in record
    assert "| final_verdict |" not in record
    assert API_KEY not in record
    assert sorted(path.name for path in run_dir.iterdir()) == [
        "raw_response.json",
        "run.md",
    ]
    terminal = capsys.readouterr()
    assert "raw-only hidden reasoning" not in terminal.out + terminal.err
    assert "Persisted BA-003 runtime evidence" in terminal.out


@pytest.mark.parametrize(
    "content",
    [
        "You have three cards linked to your payment account.",
        "You don't have any cards.",
        "You have a payment account with EUR 12,000.",
    ],
)
def test_structurally_usable_meanings_persist_identical_deterministic_status(
    monkeypatch, tmp_path, content
):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(200, _body(content)))

    assert ba_003.capture(tmp_path / "runs") == 0

    record = (tmp_path / "runs" / "run_001" / "run.md").read_text()
    assert "| deterministic_evidence_status | USABLE |" in record
    assert "| behavioral_assessment_status | PENDING_SEMANTIC_EVALUATION |" in record
    assert "| semantic_verdict |" not in record


def test_raw_response_is_persisted_before_run_md(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(200, _body("Visible response")))
    events = []
    original_raw = ba_003.write_raw_response
    original_publish = ba_003.publish_run_record

    def write_raw(*args, **kwargs):
        events.append("raw")
        return original_raw(*args, **kwargs)

    def publish(*args, **kwargs):
        events.append("run.md")
        return original_publish(*args, **kwargs)

    monkeypatch.setattr(ba_003, "write_raw_response", write_raw)
    monkeypatch.setattr(ba_003, "publish_run_record", publish)

    assert ba_003.capture(tmp_path / "runs") == 0
    assert events == ["raw", "run.md"]


@pytest.mark.parametrize("raw_body", [b"{}", b"[]", b'"scalar"', b"42", b"null"])
def test_json_values_are_preserved_as_json(monkeypatch, tmp_path, raw_body):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    assert ba_003.capture(tmp_path / "runs") == 0
    assert (
        tmp_path / "runs" / "run_001" / "raw_response.json"
    ).read_bytes() == raw_body
    record = (tmp_path / "runs" / "run_001" / "run.md").read_text()
    assert "| deterministic_evidence_status | INSUFFICIENT |" in record
    assert "| behavioral_assessment_status | UNASSESSED |" in record


def test_non_json_bytes_are_preserved_as_text(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    raw_body = b"\xffnot-json\r\nexact bytes"
    _fake_post(monkeypatch, response=FakeResponse(502, raw_body))

    assert ba_003.capture(tmp_path / "runs") == 0
    assert (
        tmp_path / "runs" / "run_001" / "raw_response.txt"
    ).read_bytes() == raw_body


def test_zero_length_body_is_distinct_from_unavailable_body(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    _fake_post(monkeypatch, response=FakeResponse(500, b""))

    assert ba_003.capture(tmp_path / "runs") == 0
    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.txt").read_bytes() == b""
    record = (run_dir / "run.md").read_text()
    assert "| response_body_status | available (zero-length) |" in record


def test_request_exception_without_response_records_absence(monkeypatch, tmp_path):
    _allow_capture_preflight(monkeypatch)
    calls = _fake_post(
        monkeypatch,
        exc=requests.ConnectionError("unsafe request details"),
    )

    assert ba_003.capture(tmp_path / "runs") == 0
    assert len(calls) == 1
    run_dir = tmp_path / "runs" / "run_001"
    assert sorted(path.name for path in run_dir.iterdir()) == ["run.md"]
    record = (run_dir / "run.md").read_text()
    assert "| response_body_status | unavailable |" in record
    assert "| raw_response_file | none (response body unavailable) |" in record
    assert "unsafe request details" not in record


def test_request_exception_with_response_persists_available_body(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    raw_body = b'{"error": "upstream unavailable"}'
    exc = requests.ConnectionError(
        "unsafe request details",
        response=FakeResponse(503, raw_body),
    )
    calls = _fake_post(monkeypatch, exc=exc)

    assert ba_003.capture(tmp_path / "runs") == 0
    assert len(calls) == 1
    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    record = (run_dir / "run.md").read_text()
    assert "| http_status | 503 |" in record
    assert "| error_type | ConnectionError |" in record
    assert "unsafe request details" not in record


def test_raw_write_failure_leaves_incomplete_consumed_run_without_retry(
    monkeypatch, tmp_path, capsys
):
    _allow_capture_preflight(monkeypatch)
    raw_body = _body("secret visible output", reasoning="hidden secret")
    calls = _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    def fail_raw_write(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(ba_003, "write_raw_response", fail_raw_write)

    assert ba_003.capture(tmp_path / "runs") == 1
    assert len(calls) == 1
    run_dir = tmp_path / "runs" / "run_001"
    assert run_dir.is_dir()
    assert not ba_003.is_complete_run(run_dir)
    assert ba_003.next_run_number(tmp_path / "runs") == 2
    terminal = capsys.readouterr()
    output = terminal.out + terminal.err
    assert "secret visible output" not in output
    assert "hidden secret" not in output
    assert API_KEY not in output
    assert "provider_retry=no" in terminal.err


def test_run_md_publication_failure_keeps_raw_and_incomplete_consumed_run(
    monkeypatch, tmp_path
):
    _allow_capture_preflight(monkeypatch)
    raw_body = _body("Visible response")
    calls = _fake_post(monkeypatch, response=FakeResponse(200, raw_body))

    def fail_publication(*args, **kwargs):
        raise OSError("link failed")

    monkeypatch.setattr(ba_003, "publish_run_record", fail_publication)

    assert ba_003.capture(tmp_path / "runs") == 1
    assert len(calls) == 1
    run_dir = tmp_path / "runs" / "run_001"
    assert (run_dir / "raw_response.json").read_bytes() == raw_body
    assert not ba_003.is_complete_run(run_dir)
    assert ba_003.next_run_number(tmp_path / "runs") == 2


def test_cleanup_failure_after_publication_keeps_complete_package(
    monkeypatch, tmp_path, capsys
):
    _allow_capture_preflight(monkeypatch)
    calls = _fake_post(
        monkeypatch,
        response=FakeResponse(200, _body("Visible response")),
    )

    def cleanup_failure(reservation):
        return [(reservation["marker_path"], "PermissionError")]

    monkeypatch.setattr(ba_003, "cleanup_after_publication", cleanup_failure)

    assert ba_003.capture(tmp_path / "runs") == 0
    assert len(calls) == 1
    assert ba_003.is_complete_run(tmp_path / "runs" / "run_001")
    assert "runtime package is complete" in capsys.readouterr().err


def test_existing_publication_paths_are_never_overwritten(tmp_path):
    run_dir = tmp_path / "run_001"
    run_dir.mkdir()
    raw_path = run_dir / "raw_response.json"
    raw_path.write_bytes(b"foreign raw")

    with pytest.raises(FileExistsError):
        ba_003.write_raw_response(run_dir, "raw_response.json", b"new raw")
    assert raw_path.read_bytes() == b"foreign raw"

    reservation = {
        "run_dir": run_dir,
        "temp_path": run_dir / ".run.md.tmp.test",
    }
    reservation["temp_path"].write_text("foreign temp")
    with pytest.raises(FileExistsError):
        ba_003.publish_run_record(reservation, "new record")
    assert reservation["temp_path"].read_text() == "foreign temp"

    reservation["temp_path"].unlink()
    (run_dir / "run.md").write_text("foreign run")
    with pytest.raises(FileExistsError):
        ba_003.publish_run_record(reservation, "new record")
    assert (run_dir / "run.md").read_text() == "foreign run"

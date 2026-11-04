import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_TEST_PATHS = (
    "tests/test_groq_smoke.py",
    "tests/test_ba_001_unknown_transaction_status.py",
    "tests/test_ba_002_ambiguous_sms_settings.py",
    "tests/test_ba_003_backend_relationship_interpretation.py",
)
LIVE_OPT_IN_VARIABLES = (
    "RUN_LIVE_TESTS",
    "RUN_LIVE_BA_002",
    "RUN_LIVE_BA_003",
)


def test_live_tests_are_skipped_by_default_without_groq_credentials():
    env = os.environ.copy()
    env["GROQ_API_KEY"] = ""
    env["GROQ_MODEL"] = ""
    for name in LIVE_OPT_IN_VARIABLES:
        env.pop(name, None)

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *LIVE_TEST_PATHS, "-q"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert "4 skipped" in output

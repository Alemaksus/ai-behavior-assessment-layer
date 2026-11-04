import os

import pytest

from ba_002 import evaluate, execute, prepare_request, print_report


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_TESTS") != "1"
    and os.environ.get("RUN_LIVE_BA_002") != "1",
    reason=(
        "explicit live BA-002 execution requires RUN_LIVE_TESTS=1 "
        "or RUN_LIVE_BA_002=1"
    ),
)


def test_ba_002_ambiguous_sms_settings():
    execution = execute(prepare_request())
    evaluation = evaluate(execution)
    print_report(execution, evaluation)

    if evaluation["deterministic_evidence_status"] != "USABLE":
        pytest.fail(
            "Insufficient deterministic evidence; behavioral claim remains unassessed: "
            f"visible_content_status={evaluation['visible_content_status']}, "
            f"error={execution['error']}"
        )

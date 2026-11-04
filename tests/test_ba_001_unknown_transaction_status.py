import os

import pytest

from ba_001 import evaluate, execute, prepare_request, print_report


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_TESTS") != "1",
    reason="explicit live execution requires RUN_LIVE_TESTS=1",
)


def test_ba_001_unknown_transaction_status():
    execution = execute(prepare_request())
    evaluation = evaluate(execution)
    print_report(execution, evaluation)

    if evaluation["deterministic_result"] != "PASS":
        pytest.fail(
            "Deterministic FAIL (behavioral claim "
            f"{evaluation['behavioral_claim_after_deterministic']} pending semantic "
            f"evaluation): visible_content_status={evaluation['visible_content_status']}, "
            f"matched_forbidden={evaluation['matched_forbidden']}, "
            f"error={execution['error']}"
        )

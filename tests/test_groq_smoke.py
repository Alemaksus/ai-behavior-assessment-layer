import os

import pytest

from groq_client import groq_smoke_chat


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_TESTS") != "1",
    reason="explicit live execution requires RUN_LIVE_TESTS=1",
)


def test_groq_smoke():
    data = groq_smoke_chat()
    content = data["choices"][0]["message"]["content"]
    assert content.strip() == "AIRRA_OK"

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

load_dotenv(Path(__file__).resolve().parent / ".env")


def groq_chat(messages, *, temperature=0, max_tokens=None) -> dict:
    payload = {
        "model": os.environ["GROQ_MODEL"],
        "messages": messages,
        "temperature": temperature,
        "reasoning_effort": "low",
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def groq_smoke_chat() -> dict:
    return groq_chat(
        [{"role": "user", "content": "Reply with exactly: AIRRA_OK"}],
        temperature=0,
    )

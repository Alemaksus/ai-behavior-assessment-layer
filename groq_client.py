import os
from pathlib import Path

import requests
from dotenv import load_dotenv

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

load_dotenv(Path(__file__).resolve().parent / ".env")


def groq_smoke_chat() -> dict:
    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.environ["GROQ_MODEL"],
            "messages": [{"role": "user", "content": "Reply with exactly: AIRRA_OK"}],
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()

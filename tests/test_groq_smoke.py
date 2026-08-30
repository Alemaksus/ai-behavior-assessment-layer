from groq_client import groq_smoke_chat


def test_groq_smoke():
    data = groq_smoke_chat()
    content = data["choices"][0]["message"]["content"]
    assert content.strip() == "AIRRA_OK"

import pytest


@pytest.fixture(autouse=True)
def _no_real_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests never touch a real language-model API, even if a key is present in
    backend/.env. Tests that need a model patch `llm.generate_reply` themselves."""
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(name, raising=False)

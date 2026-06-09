import asyncio
from unittest.mock import AsyncMock

from utils import model_availability
from utils.llm_config import get_llm_config


def test_custom_llm_model_availability_accepts_configured_model(monkeypatch):
    monkeypatch.setenv("CAN_CHANGE_KEYS", "false")
    monkeypatch.setenv("LLM", "custom")
    monkeypatch.setenv("CUSTOM_LLM_URL", "https://llm.example/v1")
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("CUSTOM_MODEL", "demo-model")
    monkeypatch.setenv("DISABLE_IMAGE_GENERATION", "true")

    list_models = AsyncMock(return_value=["other-model", "demo-model"])
    monkeypatch.setattr(
        model_availability,
        "list_available_openai_compatible_models",
        list_models,
    )

    asyncio.run(
        model_availability.check_llm_and_image_provider_api_or_model_availability()
    )

    list_models.assert_awaited_once_with("https://llm.example/v1", "sk-test")


def test_custom_llm_config_sets_openai_compatible_user_agent(monkeypatch):
    import llmai.openai.client as llmai_openai_client  # type: ignore[import-not-found]

    captured: list[dict] = []

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr(llmai_openai_client, "OpenAI", FakeOpenAI)
    monkeypatch.setenv("LLM", "custom")
    monkeypatch.setenv("CUSTOM_LLM_URL", "https://llm.example/v1")
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("CUSTOM_LLM_USER_AGENT", "Presenton-Test/1")

    config = get_llm_config()
    llmai_openai_client.OpenAI(base_url=config.base_url, api_key=config.api_key)

    assert captured
    assert captured[0]["default_headers"]["User-Agent"] == "Presenton-Test/1"

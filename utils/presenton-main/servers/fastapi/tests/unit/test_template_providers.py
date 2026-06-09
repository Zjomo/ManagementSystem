from templates import providers
import asyncio


def test_custom_template_provider_sets_openai_compatible_user_agent(monkeypatch):
    captured: dict = {}

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(providers, "AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setenv("CUSTOM_LLM_URL", "https://llm.example/v1")
    monkeypatch.setenv("CUSTOM_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("CUSTOM_LLM_USER_AGENT", "Presenton-Test/1")

    providers._get_custom_openai_like_client()

    assert captured["base_url"] == "https://llm.example/v1"
    assert captured["api_key"] == "sk-test"
    assert captured["default_headers"]["User-Agent"] == "Presenton-Test/1"


def test_custom_template_provider_skips_image_by_default(monkeypatch):
    captured: dict = {}

    async def fake_call_chat(**kwargs):
        captured.update(kwargs)
        return "ok"

    async def fake_call_responses(**kwargs):
        raise AssertionError("default custom template provider should prefer chat")

    monkeypatch.setattr(providers, "_call_openai_chat_completions", fake_call_chat)
    monkeypatch.setattr(providers, "_call_openai_like", fake_call_responses)
    monkeypatch.setattr(providers, "_get_custom_openai_like_client", lambda: object())
    monkeypatch.delenv("CUSTOM_LLM_ENABLE_VISION", raising=False)
    monkeypatch.delenv("CUSTOM_LLM_PREFER_RESPONSES", raising=False)

    result = asyncio.run(
        providers._call_custom_openai_like(
            model="demo-model",
            system_prompt="system",
            user_text="html reference",
            image_bytes=b"image-bytes",
            media_type="image/png",
        )
    )

    assert result == "ok"
    assert captured["image_bytes"] is None


def test_custom_template_provider_uses_image_when_enabled(monkeypatch):
    captured: dict = {}

    async def fake_call_chat(**kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(providers, "_call_openai_chat_completions", fake_call_chat)
    monkeypatch.setattr(providers, "_get_custom_openai_like_client", lambda: object())
    monkeypatch.setenv("CUSTOM_LLM_ENABLE_VISION", "true")
    monkeypatch.delenv("CUSTOM_LLM_PREFER_RESPONSES", raising=False)

    result = asyncio.run(
        providers._call_custom_openai_like(
            model="demo-model",
            system_prompt="system",
            user_text="html reference",
            image_bytes=b"image-bytes",
            media_type="image/png",
        )
    )

    assert result == "ok"
    assert captured["image_bytes"] == b"image-bytes"


def test_custom_template_provider_falls_back_when_responses_is_blocked(monkeypatch):
    captured: dict = {}

    async def fake_call_responses(**kwargs):
        raise RuntimeError("403: Your request was blocked.")

    async def fake_call_chat(**kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(providers, "_call_openai_like", fake_call_responses)
    monkeypatch.setattr(providers, "_call_openai_chat_completions", fake_call_chat)
    monkeypatch.setattr(providers, "_get_custom_openai_like_client", lambda: object())
    monkeypatch.setenv("CUSTOM_LLM_PREFER_RESPONSES", "true")
    monkeypatch.delenv("CUSTOM_LLM_ENABLE_VISION", raising=False)

    result = asyncio.run(
        providers._call_custom_openai_like(
            model="demo-model",
            system_prompt="system",
            user_text="html reference",
            image_bytes=b"image-bytes",
            media_type="image/png",
        )
    )

    assert result == "ok"
    assert captured["image_bytes"] is None

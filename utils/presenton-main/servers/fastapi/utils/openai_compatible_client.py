import os
from typing import Any


DEFAULT_OPENAI_COMPATIBLE_USER_AGENT = "Presenton/0.8.0"


def _configured_user_agent() -> str:
    return (
        os.getenv("CUSTOM_LLM_USER_AGENT")
        or os.getenv("OPENAI_COMPATIBLE_USER_AGENT")
        or DEFAULT_OPENAI_COMPATIBLE_USER_AGENT
    ).strip() or DEFAULT_OPENAI_COMPATIBLE_USER_AGENT


def _has_user_agent(headers: dict[str, str]) -> bool:
    return any(key.lower() == "user-agent" for key in headers)


def openai_compatible_default_headers(
    headers: dict[str, str] | None = None,
) -> dict[str, str]:
    default_headers = dict(headers or {})
    if not _has_user_agent(default_headers):
        default_headers["User-Agent"] = _configured_user_agent()
    return default_headers


def ensure_openai_compatible_user_agent() -> None:
    """Patch llmai's OpenAI SDK constructor for OpenAI-compatible gateways.

    Some compatible gateways accept plain HTTP clients but reject the OpenAI
    Python SDK default User-Agent. llmai does not expose SDK default_headers in
    OpenAIClientConfig, so patch its imported OpenAI class once and only add a
    benign application User-Agent when a custom base_url is used.
    """
    import llmai.openai.client as llmai_openai_client  # type: ignore[import-not-found]

    current_openai_cls = llmai_openai_client.OpenAI
    if getattr(current_openai_cls, "_presenton_compatible_user_agent_patch", False):
        return

    class PresentonOpenAI(current_openai_cls):  # type: ignore[misc, valid-type]
        _presenton_compatible_user_agent_patch = True

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            if kwargs.get("base_url"):
                kwargs["default_headers"] = openai_compatible_default_headers(
                    kwargs.get("default_headers")
                )
            super().__init__(*args, **kwargs)

    PresentonOpenAI.__name__ = getattr(current_openai_cls, "__name__", "OpenAI")
    PresentonOpenAI.__qualname__ = getattr(
        current_openai_cls,
        "__qualname__",
        PresentonOpenAI.__qualname__,
    )
    llmai_openai_client.OpenAI = PresentonOpenAI

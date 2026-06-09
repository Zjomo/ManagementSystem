from fastapi import HTTPException
from openai import APIError as OpenAIAPIError
from google.genai.errors import APIError as GoogleAPIError
import traceback

from llmai.shared.errors import BaseError as LLMAIBaseError
from utils.get_env import get_custom_llm_url_env
from utils.llm_provider import get_llm_provider, get_model


def _safe_runtime_label() -> str:
    parts: list[str] = []
    try:
        parts.append(f"provider={get_llm_provider().value}")
    except Exception:
        pass
    try:
        model = get_model()
        if model:
            parts.append(f"model={model}")
    except Exception:
        pass
    try:
        custom_url = get_custom_llm_url_env()
        if custom_url:
            parts.append(f"base_url={custom_url}")
    except Exception:
        pass
    return ", ".join(parts)


def _generation_rejected_detail(e: LLMAIBaseError) -> str:
    runtime_label = _safe_runtime_label()
    suffix = f" Current config: {runtime_label}." if runtime_label else ""
    message = str(e.message).rstrip(".")
    return (
        f"{e.status_code}: {message}. "
        "The model endpoint accepted configuration/model-list checks but rejected "
        "the actual generation request. Use an API key/base URL that allows "
        "chat-completions generation for the selected model, or switch to a "
        "provider/model with generation access."
        f"{suffix}"
    )


def handle_llm_client_exceptions(e: Exception) -> HTTPException:
    if isinstance(e, HTTPException):
        return e
    if isinstance(e, LLMAIBaseError):
        if e.status_code in {401, 403}:
            return HTTPException(
                status_code=e.status_code,
                detail=_generation_rejected_detail(e),
            )
        return HTTPException(status_code=e.status_code, detail=e.message)
    traceback.print_exc()
    if isinstance(e, OpenAIAPIError):
        return HTTPException(status_code=500, detail=f"OpenAI API error: {e.message}")
    if isinstance(e, GoogleAPIError):
        return HTTPException(status_code=500, detail=f"Google API error: {e.message}")
    return HTTPException(status_code=500, detail=f"LLM API error: {e}")

import aiohttp
from google import genai


def _extract_model_ids(payload) -> list[str]:
    if isinstance(payload, dict):
        models = payload.get("data") or payload.get("models") or []
    elif isinstance(payload, list):
        models = payload
    else:
        models = []

    model_ids: list[str] = []
    for model in models:
        if isinstance(model, str):
            model_ids.append(model)
        elif isinstance(model, dict):
            model_id = model.get("id") or model.get("name") or model.get("model")
            if isinstance(model_id, str):
                model_ids.append(model_id)

    return list(dict.fromkeys(model_ids))


async def list_available_openai_compatible_models(url: str, api_key: str) -> list[str]:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=12),
    ) as session:
        async with session.get(f"{url.rstrip('/')}/models") as response:
            response.raise_for_status()
            data = await response.json(content_type=None)

    return _extract_model_ids(data)



async def list_available_anthropic_models(api_key: str) -> list[str]:
    async with aiohttp.ClientSession(
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
    ) as session:
        async with session.get(
            "https://api.anthropic.com/v1/models",
            params={"limit": 50},
        ) as response:
            response.raise_for_status()
            data = await response.json()

    models = data.get("data", [])
    return [model.get("id") for model in models if model.get("id")]


async def list_available_google_models(api_key: str) -> list[str]:
    client = genai.Client(api_key=api_key)
    return list(map(lambda x: x.name, client.models.list(config={"page_size": 50})))

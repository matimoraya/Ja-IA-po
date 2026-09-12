"""Model adapters kept separate from the investigation loop."""

import asyncio
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelProviderError(RuntimeError):
    """A configured model provider could not produce a usable decision."""


def _post_responses(payload, api_key, timeout):
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


class OpenAIResponsesModel:
    """Small Responses API adapter with no SDK dependency.

    It returns plain dictionaries so ``core`` owns the provider-independent
    decision parsing and all safety checks.
    """

    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    async def decide(self, context, tools, timeout):
        payload = {
            "model": self.model,
            "input": context,
            "tools": tools,
            "tool_choice": "auto",
            "parallel_tool_calls": False,
        }
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_post_responses, payload, self.api_key, timeout), timeout=timeout
            )
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise ModelProviderError("El proveedor del modelo excedió el tiempo disponible.") from exc
        except HTTPError as exc:
            raise ModelProviderError(f"El proveedor del modelo respondió HTTP {exc.code}.") from exc
        except (URLError, OSError, ValueError, TypeError) as exc:
            raise ModelProviderError("No se pudo obtener una decisión del proveedor del modelo.") from exc


def configured_model():
    """Return the configured live model, or explain why one is unavailable."""
    provider = os.environ.get("MODEL_PROVIDER", "openai").strip().lower()
    if provider != "openai":
        raise ModelProviderError("MODEL_PROVIDER no está soportado por este agente.")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("MODEL", "").strip()
    if not api_key or not model:
        raise ModelProviderError("Falta configurar OPENAI_API_KEY o MODEL para investigar con el modelo.")
    return OpenAIResponsesModel(api_key, model)

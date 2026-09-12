"""Exa Search por HTTP documentado, sin dependencias externas ni logs de claves."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .common import failure, success

ROOT = Path(__file__).resolve().parents[2]


def read_api_key():
    """El entorno tiene precedencia. Archivos locales no se ejecutan como código."""
    value = os.environ.get("EXA_API_KEY", "").strip()
    if value:
        return value
    for name in (".env", "API.env"):
        path = ROOT / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.strip().removeprefix("export ").partition("=")
            if sep and key.strip() == "EXA_API_KEY":
                value = value.strip()
                if value.startswith(('"', "'")) and value.endswith(value[0]):
                    value = value[1:-1]
                else:
                    value = value.split(" #", 1)[0].strip()
                if value:
                    return value
    return ""


def _request(payload, key, timeout):
    request = Request(
        "https://api.exa.ai/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": key},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("oversized response")
    return json.loads(raw)


async def research_security_context(query, *, api_key=None, timeout=15, transport=None):
    """Consultar términos públicos de seguridad; nunca pasar logs ni secretos.

    transport(payload, key, timeout) es una función sync inyectable para tests.
    Tres resultados es el presupuesto de fuentes acordado para el MVP.
    """
    if not isinstance(query, str) or not 3 <= len(query.strip()) <= 500:
        return failure("INVALID_ARGUMENT", "La consulta debe tener entre 3 y 500 caracteres.")
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 60:
        return failure("INVALID_ARGUMENT", "Timeout debe estar entre 0 y 60 segundos.")
    key = read_api_key() if api_key is None else api_key
    if not isinstance(key, str) or not key.strip():
        return failure("MISSING_API_KEY", "Configurar EXA_API_KEY en el entorno o .env.")
    payload = {"query": query.strip(), "type": "auto", "numResults": 3,
               "contents": {"highlights": True}}
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(transport or _request, payload, key.strip(), timeout),
            timeout=timeout,
        )
        if not isinstance(response, dict) or not isinstance(response.get("results"), list):
            raise ValueError("invalid results")
        sources = []
        seen = set()
        for result in response["results"]:
            if not isinstance(result, dict):
                raise ValueError("invalid item")
            url = result.get("url", "")
            if not isinstance(url, str):
                raise ValueError("invalid url")
            parsed = urlparse(url)
            if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username:
                continue
            if url in seen:
                continue
            highlights = result.get("highlights") or []
            if not isinstance(highlights, list) or any(not isinstance(h, str) for h in highlights):
                raise ValueError("invalid highlights")
            title = result.get("title") or "Sin título"
            if not isinstance(title, str):
                raise ValueError("invalid title")
            seen.add(url)
            sources.append({"id": "exa-" + hashlib.sha256(url.encode()).hexdigest()[:16],
                            "title": title, "url": url, "excerpt": "\n".join(highlights)})
            if len(sources) == 3:
                break
        return success({"sources": sources, "provider": "exa"})
    except HTTPError as exc:
        code = {401: "INVALID_API_KEY", 403: "ACCESS_DENIED", 402: "INSUFFICIENT_CREDITS",
                429: "RATE_LIMITED"}.get(exc.code, "PROVIDER_ERROR")
        return failure(code, f"Exa respondió HTTP {exc.code}; no se reintentó automáticamente.")
    except (TimeoutError, asyncio.TimeoutError):
        return failure("TIMEOUT", "Exa excedió el tiempo disponible.")
    except (URLError, OSError):
        return failure("NETWORK_ERROR", "No se pudo conectar con Exa.")
    except (ValueError, TypeError):
        return failure("INVALID_RESPONSE", "Exa devolvió una respuesta no válida.")

"""JSON stdin/stdout bridge; called by the Next.js server, never a shell."""
import asyncio
import json
import sys

from . import ScenarioTools, research_security_context
from .common import failure

ALLOWED = {
    "search_logs": {"query", "start", "end", "ip", "limit"},
    "get_timeline": {"start", "end", "limit"},
    "inspect_process": {"host", "pid"},
    "get_connections": {"host", "pid"},
    "get_recent_deployments": {"host", "start", "end"},
    "research_security_context": {"query"},
}


async def dispatch(request):
    if not isinstance(request, dict):
        return failure("INVALID_ARGUMENT", "Solicitud inválida.")
    name, args = request.get("tool"), request.get("arguments", {})
    if not isinstance(name, str) or name not in ALLOWED or not isinstance(args, dict) or not set(args) <= ALLOWED[name]:
        return failure("INVALID_ARGUMENT", "Herramienta o argumentos inválidos.")
    try:
        if name == "research_security_context":
            return await research_security_context(**args)
        local = ScenarioTools(request.get("scenario_id"))
        result = await getattr(local, name)(**args)
        # Only absent files may use the server-provided demo. Broken files stay errors.
        fallback = request.get("sample_data")
        sample = False
        if (result.get("error") or {}).get("code") == "SCENARIO_NOT_FOUND":
            if fallback is not None:
                result = await getattr(ScenarioTools(request.get("scenario_id"), scenario_data=fallback), name)(**args)
                sample = True
        if result["ok"]:
            result["data"]["provenance"] = {
                "scenario_id": request.get("scenario_id"),
                "source": "ui_demo_timeline" if sample else "scenario_file",
                "limitations": ["Timeline ficticio; procesos, conexiones y deployments no disponibles.",
                                "Fecha 2026-09-12 asignada para normalizar las horas del demo."] if sample else [],
            }
        return result
    except (TypeError, ValueError):
        return failure("INVALID_ARGUMENT", "Argumentos incompletos o inválidos.")


def main():
    try:
        text = sys.stdin.read(100_001)
        if len(text) > 100_000:
            raise ValueError("too large")
        result = asyncio.run(dispatch(json.loads(text)))
    except (ValueError, TypeError):
        result = failure("INVALID_ARGUMENT", "JSON inválido.")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

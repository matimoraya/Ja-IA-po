"""Consultas de solo lectura aisladas por escenario."""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from .common import failure, success


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Fecha inválida")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("La fecha requiere zona horaria")
    return parsed


class ScenarioTools:
    """Crear una instancia por investigación; scenario_id lo fija el servidor."""

    def __init__(self, scenario_id, root=None, *, scenario_data=None):
        self.scenario_id = scenario_id
        self.root = Path(root or Path(__file__).resolve().parents[2] / "data/scenarios").resolve()
        self.scenario_data = scenario_data

    def _load(self):
        if not isinstance(self.scenario_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", self.scenario_id):
            raise ValueError("ID de escenario inválido")
        path = (self.root / self.scenario_id / "scenario.json").resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Ruta fuera del directorio de escenarios")
        if self.scenario_data is not None:
            data = self.scenario_data
        else:
            if path.stat().st_size > 5_000_000:
                raise ValueError("Escenario demasiado grande")
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or data.get("id") != self.scenario_id:
            raise ValueError("ID del archivo incompatible")
        for collection in ("events", "processes", "connections", "deployments"):
            rows = data.get(collection)
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise ValueError("Colección inválida")
        return data

    @staticmethod
    def _window(rows, start=None, end=None):
        first = timestamp(start) if start is not None else None
        last = timestamp(end) if end is not None else None
        if first and last and first > last:
            raise ValueError("Rango temporal invertido")
        ordered = sorted(rows, key=lambda row: timestamp(row.get("timestamp")))
        return [r for r in ordered if (first is None or timestamp(r["timestamp"]) >= first)
                and (last is None or timestamp(r["timestamp"]) <= last)]

    async def _execute(self, operation):
        try:
            data = await asyncio.to_thread(self._load)
        except FileNotFoundError:
            return failure("SCENARIO_NOT_FOUND", "El escenario aún no está disponible.")
        except (ValueError, OSError):
            return failure("INVALID_SCENARIO", "El escenario no cumple el contrato de datos.")
        try:
            return success(operation(data))
        except (ValueError, TypeError, KeyError):
            return failure("INVALID_ARGUMENT_OR_DATA", "Comprobar argumentos y campos del escenario.")

    async def search_logs(self, query, start=None, end=None, ip=None, limit=50):
        def run(data):
            if not isinstance(query, str) or len(query) > 500:
                raise ValueError("Consulta inválida")
            if type(limit) is not int or not 1 <= limit <= 100:
                raise ValueError("Límite inválido")
            rows = self._window(data["events"], start, end)
            rows = [r for r in rows if (ip is None or r.get("ip") == ip)
                    and query.casefold() in json.dumps(r, ensure_ascii=False).casefold()]
            return {"events": rows[:limit], "truncated": len(rows) > limit}
        return await self._execute(run)

    async def get_timeline(self, start=None, end=None, limit=100):
        return await self.search_logs("", start, end, limit=limit)

    async def inspect_process(self, host, pid):
        def run(data):
            if not isinstance(host, str) or not host or type(pid) is not int or pid < 0:
                raise ValueError("Host o PID inválido")
            process = next((p for p in data["processes"] if p.get("host") == host and p.get("pid") == pid), None)
            return {"process": process,
                    "events": [e for e in data["events"] if e.get("host") == host and
                               (e.get("pid") == pid or e.get("id") in (process or {}).get("event_ids", []))],
                    "connections": [c for c in data["connections"] if c.get("host") == host and c.get("pid") == pid]}
        return await self._execute(run)

    async def get_connections(self, host=None, pid=None):
        def run(data):
            if host is not None and (not isinstance(host, str) or not host):
                raise ValueError("Host inválido")
            if pid is not None and (type(pid) is not int or pid < 0):
                raise ValueError("PID inválido")
            return {"connections": [c for c in data["connections"] if
                    (host is None or c.get("host") == host) and (pid is None or c.get("pid") == pid)]}
        return await self._execute(run)

    async def get_recent_deployments(self, host=None, start=None, end=None):
        def run(data):
            if host is not None and (not isinstance(host, str) or not host):
                raise ValueError("Host inválido")
            return {"deployments": [d for d in self._window(data["deployments"], start, end)
                                    if host is None or d.get("host") == host]}
        return await self._execute(run)

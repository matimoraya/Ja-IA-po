"""Budgeted, evidence-grounded investigation loop."""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Protocol

from app.tools import ScenarioTools, research_security_context

from .models import ModelProviderError, configured_model


EventEmitter = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelDecision:
    """One model turn: tool calls, a proposed report, or both."""

    tool_calls: list[ToolCall] = field(default_factory=list)
    report: dict[str, Any] | None = None


class InvestigationModel(Protocol):
    async def decide(self, context: list[dict[str, Any]], tools: list[dict[str, Any]], timeout: float) -> Any:
        """Choose the next tool calls after observing the supplied context."""


@dataclass(frozen=True)
class AgentLimits:
    max_rounds: int = 10
    max_tool_calls: int = 20
    timeout_seconds: float = 90.0


TOOL_ARGUMENTS = {
    "search_logs": {"query", "start", "end", "ip", "limit"},
    "get_timeline": {"start", "end", "limit"},
    "inspect_process": {"host", "pid"},
    "get_connections": {"host", "pid"},
    "get_recent_deployments": {"host", "start", "end"},
    "research_security_context": {"query"},
}


def default_tool_registry(scenario_id: str) -> dict[str, Callable[..., Awaitable[dict[str, Any]]]]:
    """Bind local tools to the server-selected scenario exactly once."""
    local = ScenarioTools(scenario_id)
    return {
        "search_logs": local.search_logs,
        "get_timeline": local.get_timeline,
        "inspect_process": local.inspect_process,
        "get_connections": local.get_connections,
        "get_recent_deployments": local.get_recent_deployments,
        "research_security_context": research_security_context,
    }


def _tool_definitions():
    # ``scenario_id`` deliberately does not appear in any JSON schema.
    properties = {
        "query": {"type": "string"}, "start": {"type": "string"}, "end": {"type": "string"},
        "ip": {"type": "string"}, "limit": {"type": "integer"}, "host": {"type": "string"},
        "pid": {"type": "integer"},
    }
    return [
        {"type": "function", "name": name, "description": "Consulta de investigación SOC.",
         "parameters": {"type": "object", "properties": {key: properties[key] for key in allowed},
                        "additionalProperties": False}}
        for name, allowed in TOOL_ARGUMENTS.items()
    ]


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _emit(emit: EventEmitter, event_type: str, message: str, *, tool_name=None, evidence_ids=None):
    event = {"id": str(uuid.uuid4()), "timestamp": _now(), "type": event_type, "message": message}
    if tool_name is not None:
        event["tool_name"] = tool_name
    if evidence_ids:
        event["evidence_ids"] = sorted(evidence_ids)
    await emit(event)


def _remaining(deadline):
    return deadline - time.monotonic()


def _parse_decision(value: Any) -> ModelDecision:
    if isinstance(value, ModelDecision):
        return value
    if not isinstance(value, dict):
        raise ValueError("El modelo devolvió una decisión inválida.")
    if "output" in value:  # OpenAI Responses API shape
        calls, text = [], []
        for item in value.get("output", []):
            if item.get("type") == "function_call":
                try:
                    args = json.loads(item.get("arguments", "{}"))
                except json.JSONDecodeError as exc:
                    raise ValueError("El modelo devolvió argumentos de herramienta inválidos.") from exc
                calls.append(ToolCall(item.get("name", ""), args))
            for content in item.get("content", []) or []:
                if content.get("type") == "output_text":
                    text.append(content.get("text", ""))
        report = _json_report("\n".join(text)) if text else None
        return ModelDecision(calls, report)
    calls = [ToolCall(call.get("name", ""), call.get("arguments", {})) for call in value.get("tool_calls", [])]
    report = value.get("report")
    if report is not None and not isinstance(report, dict):
        raise ValueError("El informe propuesto por el modelo no es un objeto.")
    return ModelDecision(calls, report)


def _json_report(text):
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _evidence_from(data: Any):
    local, sources, timeline = set(), {}, []
    if not isinstance(data, dict):
        return local, sources, timeline
    for key in ("events", "connections", "deployments"):
        for row in data.get(key, []) if isinstance(data.get(key), list) else []:
            if isinstance(row, dict) and isinstance(row.get("id"), str):
                local.add(row["id"])
                if key == "events" and isinstance(row.get("timestamp"), str):
                    timeline.append((row["timestamp"], row["id"]))
    for row in data.get("sources", []) if isinstance(data.get("sources"), list) else []:
        if isinstance(row, dict) and isinstance(row.get("id"), str) and isinstance(row.get("url"), str):
            sources[row["id"]] = row
    return local, sources, timeline


def _empty_report(investigation_id, scenario_id, limitation):
    return {
        "investigation_id": investigation_id, "scenario_id": scenario_id,
        "classification": "inconclusive", "severity": "info",
        "summary": "La investigación no reunió evidencia suficiente para una conclusión verificable.",
        "timeline": [], "findings": [], "sources": [], "recommendations": [],
        "limitations": [limitation], "synthetic": True,
    }


def _validate_report(proposed, investigation_id, scenario_id, evidence_ids, source_map, observed_timeline):
    if not isinstance(proposed, dict):
        return None, "El modelo no devolvió un informe estructurado."
    classification = proposed.get("classification")
    severity = proposed.get("severity")
    if classification not in {"incident", "benign", "inconclusive"} or severity not in {"info", "low", "medium", "high", "critical"}:
        return None, "El modelo devolvió una clasificación o severidad inválida."
    findings = proposed.get("findings", [])
    timeline = proposed.get("timeline", [])
    recommendations = proposed.get("recommendations", [])
    if not all(isinstance(value, list) for value in (findings, timeline, recommendations)):
        return None, "El modelo devolvió listas de informe inválidas."
    for finding in findings:
        if not isinstance(finding, dict) or not isinstance(finding.get("statement"), str):
            return None, "El modelo devolvió un hallazgo inválido."
        ids, source_ids = finding.get("evidence_ids", []), finding.get("source_ids", [])
        if (not isinstance(ids, list) or not ids or not isinstance(source_ids, list) or
                not set(ids) <= evidence_ids or not set(source_ids) <= set(source_map)):
            return None, "El informe cita evidencia o fuentes no observadas."
    for entry in timeline:
        if not isinstance(entry, dict) or not isinstance(entry.get("timestamp"), str) or not isinstance(entry.get("description"), str):
            return None, "El modelo devolvió una línea temporal inválida."
        if not set(entry.get("evidence_ids", [])) <= evidence_ids:
            return None, "La línea temporal cita evidencia no observada."
    for recommendation in recommendations:
        if not isinstance(recommendation, dict) or not isinstance(recommendation.get("action"), str) or not isinstance(recommendation.get("rationale"), str):
            return None, "El modelo devolvió una recomendación inválida."
        if not set(recommendation.get("evidence_ids", [])) <= evidence_ids or not set(recommendation.get("source_ids", [])) <= set(source_map):
            return None, "La recomendación cita evidencia o fuentes no observadas."
    if classification != "inconclusive" and not evidence_ids:
        return None, "No hay evidencia local para sostener una clasificación definitiva."
    cleaned_findings = []
    for index, finding in enumerate(findings, 1):
        cleaned_findings.append({"id": finding.get("id") if isinstance(finding.get("id"), str) else f"finding-{index}",
                                 "statement": finding["statement"], "evidence_ids": finding.get("evidence_ids", []),
                                 "source_ids": finding.get("source_ids", [])})
    return {
        "investigation_id": investigation_id, "scenario_id": scenario_id, "classification": classification,
        "severity": severity, "summary": proposed.get("summary", "Investigación completada."),
        "timeline": timeline, "findings": cleaned_findings, "sources": list(source_map.values()),
        "recommendations": recommendations, "limitations": proposed.get("limitations", []), "synthetic": True,
    }, None


async def run_investigation(scenario_id, objective, emit, *, tool_registry_factory=default_tool_registry,
                            model=None, limits=AgentLimits()):
    """Run a model-directed investigation without exposing internal reasoning."""
    investigation_id = str(uuid.uuid4())
    if not isinstance(scenario_id, str) or not scenario_id or not isinstance(objective, str) or not objective.strip():
        report = _empty_report(investigation_id, str(scenario_id), "Los argumentos de la investigación son inválidos.")
        await _emit(emit, "failed", "La investigación no pudo iniciarse por argumentos inválidos.")
        return report
    await _emit(emit, "started", "Investigación iniciada para el escenario seleccionado.")
    deadline = time.monotonic() + limits.timeout_seconds
    context = [{"role": "system", "content": "Investiga solo evidencia observada. Usa herramientas si hacen falta. "
               "No reveles razonamiento interno. Al concluir, responde solo con JSON: classification, severity, summary, "
               "timeline, findings, recommendations, limitations. Cada finding factual requiere evidence_ids observados; "
               "las fuentes externas solo dan contexto, no prueban hechos locales."},
               {"role": "user", "content": objective}]
    evidence_ids, source_map, observed_timeline = set(), {}, []
    limitations, tool_calls, exa_calls = [], 0, 0
    try:
        registry = tool_registry_factory(scenario_id)
        if not isinstance(registry, dict) or not set(TOOL_ARGUMENTS) <= set(registry):
            raise ValueError("El registro de herramientas está incompleto.")
        active_model = model or configured_model()
    except (ValueError, ModelProviderError) as exc:
        report = _empty_report(investigation_id, scenario_id, str(exc))
        await _emit(emit, "failed", "La investigación no pudo iniciar el modelo o las herramientas.")
        return report

    for _round in range(limits.max_rounds):
        remaining = _remaining(deadline)
        if remaining <= 0:
            limitations.append("Se agotó el tiempo total de investigación.")
            break
        try:
            raw = await asyncio.wait_for(active_model.decide(context, _tool_definitions(), remaining), timeout=remaining)
            decision = _parse_decision(raw)
        except (ModelProviderError, ValueError) as exc:
            limitations.append(str(exc) or "El modelo no respondió antes del límite.")
            break
        except asyncio.TimeoutError:
            limitations.append("El modelo excedió el tiempo disponible de investigación.")
            break
        if decision.report is not None:
            report, error = _validate_report(decision.report, investigation_id, scenario_id, evidence_ids, source_map, observed_timeline)
            if report is not None:
                report["limitations"] = list(dict.fromkeys(report["limitations"] + limitations))
                await _emit(emit, "completed", "La investigación produjo un informe verificable.")
                return report
            limitations.append(error)
            break
        if not decision.tool_calls:
            limitations.append("El modelo terminó sin reunir ni estructurar una conclusión.")
            break
        for call in decision.tool_calls:
            if not isinstance(call, ToolCall):
                limitations.append("El modelo solicitó una herramienta con formato inválido.")
                continue
            if tool_calls >= limits.max_tool_calls:
                limitations.append("Se alcanzó el máximo de llamadas de herramientas.")
                break
            if call.name not in TOOL_ARGUMENTS or not isinstance(call.arguments, dict):
                limitations.append("El modelo solicitó una herramienta o argumentos no permitidos.")
                continue
            if call.name == "research_security_context" and exa_calls >= 2:
                limitations.append("Se alcanzó el máximo de consultas Exa por investigación.")
                continue
            # Drop, rather than forward, every non-contract field (including scenario_id).
            args = {key: value for key, value in call.arguments.items() if key in TOOL_ARGUMENTS[call.name]}
            remaining = _remaining(deadline)
            if remaining <= 0:
                limitations.append("Se agotó el tiempo total de investigación.")
                break
            tool_calls += 1
            if call.name == "research_security_context":
                exa_calls += 1
            await _emit(emit, "tool_started", f"Consultando {call.name}.", tool_name=call.name)
            try:
                result = await asyncio.wait_for(registry[call.name](**args), timeout=remaining)
                if not isinstance(result, dict) or not isinstance(result.get("ok"), bool) or "data" not in result:
                    raise ValueError("La herramienta devolvió una respuesta malformada.")
                if not result["ok"]:
                    error = result.get("error") or {}
                    limitations.append(f"{call.name}: {error.get('code', 'ERROR')}")
                    await _emit(emit, "tool_failed", f"{call.name} informó un error.", tool_name=call.name)
                else:
                    local, sources, entries = _evidence_from(result["data"])
                    evidence_ids.update(local)
                    source_map.update(sources)
                    observed_timeline.extend(entries)
                    context.append({"role": "user", "content": "Resultado observable de " + call.name + ": " +
                                    json.dumps(result["data"], ensure_ascii=False)})
                    await _emit(emit, "tool_completed", f"{call.name} devolvió resultados.", tool_name=call.name,
                                evidence_ids=local)
                    if local:
                        await _emit(emit, "finding", f"Se observó evidencia devuelta por {call.name}.",
                                    evidence_ids=local)
            except (ValueError, TypeError, asyncio.TimeoutError):
                limitations.append(f"{call.name}: respuesta inválida o tiempo agotado.")
                await _emit(emit, "tool_failed", f"{call.name} no pudo completarse.", tool_name=call.name)
        else:
            continue
        break
    else:
        limitations.append("Se alcanzó el máximo de rondas de investigación.")
    report = _empty_report(investigation_id, scenario_id, "; ".join(limitations) or "Evidencia insuficiente.")
    report["sources"] = list(source_map.values())
    await _emit(emit, "completed", "La investigación terminó sin una conclusión verificable.")
    return report

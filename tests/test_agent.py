import asyncio
import unittest

from app.agent import AgentLimits, ModelDecision, ToolCall, run_investigation


class ScriptedModel:
    def __init__(self, decisions):
        self.decisions = list(decisions)
        self.contexts = []

    async def decide(self, context, tools, timeout):
        self.contexts.append(context)
        return self.decisions.pop(0) if self.decisions else ModelDecision()


class SlowModel:
    async def decide(self, context, tools, timeout):
        await asyncio.sleep(0.02)
        return ModelDecision()


def report(classification="incident", evidence_ids=None):
    evidence_ids = evidence_ids or ["event-1"]
    return {
        "classification": classification,
        "severity": "high" if classification == "incident" else "low",
        "summary": "Conclusión basada en evidencia observada.",
        "timeline": [{"timestamp": "2026-09-12T12:00:00Z", "description": "Evento observado.",
                      "evidence_ids": evidence_ids}],
        "findings": [{"statement": "El evento fue observado en el escenario.", "evidence_ids": evidence_ids,
                      "source_ids": []}],
        "recommendations": [{"action": "Revisar la cuenta afectada.", "rationale": "Existe evidencia local.",
                             "evidence_ids": evidence_ids, "source_ids": []}],
        "limitations": [],
    }


class FakeTools:
    def __init__(self, result=None):
        self.calls = []
        self.result = result if result is not None else {
            "ok": True,
            "data": {"events": [{"id": "event-1", "timestamp": "2026-09-12T12:00:00Z", "message": "observed"}]},
            "error": None,
        }

    async def search_logs(self, **kwargs):
        self.calls.append(("search_logs", kwargs))
        return self.result

    async def get_timeline(self, **kwargs):
        self.calls.append(("get_timeline", kwargs))
        return self.result

    async def inspect_process(self, **kwargs):
        self.calls.append(("inspect_process", kwargs))
        return self.result

    async def get_connections(self, **kwargs):
        self.calls.append(("get_connections", kwargs))
        return self.result

    async def get_recent_deployments(self, **kwargs):
        self.calls.append(("get_recent_deployments", kwargs))
        return self.result

    async def research_security_context(self, **kwargs):
        self.calls.append(("research_security_context", kwargs))
        return self.result

    def registry(self, scenario_id):
        self.scenario_id = scenario_id
        return {name: getattr(self, name) for name in (
            "search_logs", "get_timeline", "inspect_process", "get_connections",
            "get_recent_deployments", "research_security_context",
        )}


class AgentTest(unittest.IsolatedAsyncioTestCase):
    async def run_agent(self, model, tools=None, limits=AgentLimits()):
        events, tools = [], tools or FakeTools()

        async def emit(event):
            events.append(event)

        result = await run_investigation("scenario-a", "Investigá el servidor.", emit,
                                         model=model, tool_registry_factory=tools.registry, limits=limits)
        return result, events, tools

    async def test_successful_investigation_is_evidence_grounded(self):
        model = ScriptedModel([ModelDecision([ToolCall("get_timeline")]), ModelDecision(report=report())])
        result, events, tools = await self.run_agent(model)
        self.assertEqual(result["classification"], "incident")
        self.assertEqual(result["findings"][0]["evidence_ids"], ["event-1"])
        self.assertEqual(tools.scenario_id, "scenario-a")
        self.assertEqual([event["type"] for event in events], ["started", "tool_started", "tool_completed", "finding", "completed"])

    async def test_benign_conclusion_is_allowed(self):
        model = ScriptedModel([ModelDecision([ToolCall("search_logs", {"query": "maintenance"})]),
                               ModelDecision(report=report("benign"))])
        result, _, _ = await self.run_agent(model)
        self.assertEqual(result["classification"], "benign")

    async def test_empty_results_produce_inconclusive(self):
        tools = FakeTools({"ok": True, "data": {"events": []}, "error": None})
        result, _, _ = await self.run_agent(ScriptedModel([ModelDecision([ToolCall("search_logs", {"query": "ssh"})])]), tools)
        self.assertEqual(result["classification"], "inconclusive")

    async def test_tool_failure_is_a_limitation(self):
        tools = FakeTools({"ok": False, "data": {}, "error": {"code": "NETWORK_ERROR", "message": "private"}})
        result, events, _ = await self.run_agent(ScriptedModel([ModelDecision([ToolCall("research_security_context", {"query": "SSH"})])]), tools)
        self.assertEqual(result["classification"], "inconclusive")
        self.assertIn("research_security_context: NETWORK_ERROR", result["limitations"][0])
        self.assertIn("tool_failed", [event["type"] for event in events])

    async def test_maximum_tool_call_limit(self):
        calls = [ToolCall("get_timeline") for _ in range(21)]
        result, _, tools = await self.run_agent(ScriptedModel([ModelDecision(calls)]))
        self.assertEqual(result["classification"], "inconclusive")
        self.assertEqual(len(tools.calls), 20)
        self.assertIn("máximo de llamadas", result["limitations"][0])

    async def test_maximum_round_limit(self):
        model = ScriptedModel([ModelDecision([ToolCall("get_timeline")]) for _ in range(10)])
        result, _, tools = await self.run_agent(model)
        self.assertEqual(len(tools.calls), 10)
        self.assertIn("máximo de rondas", result["limitations"][0])

    async def test_timeout_budget_exhaustion(self):
        result, _, _ = await self.run_agent(SlowModel(), limits=AgentLimits(timeout_seconds=0.001))
        self.assertEqual(result["classification"], "inconclusive")
        self.assertIn("tiempo", result["limitations"][0])

    async def test_invalid_evidence_is_not_presented_as_success(self):
        invalid = report(evidence_ids=["invented-id"])
        model = ScriptedModel([ModelDecision([ToolCall("get_timeline")]), ModelDecision(report=invalid)])
        result, _, _ = await self.run_agent(model)
        self.assertEqual(result["classification"], "inconclusive")
        self.assertIn("evidencia", result["limitations"][0])

    async def test_scenario_id_is_not_forwarded_from_model_arguments(self):
        model = ScriptedModel([ModelDecision([ToolCall("search_logs", {"query": "ssh", "scenario_id": "scenario-b"})])])
        _, _, tools = await self.run_agent(model)
        self.assertEqual(tools.scenario_id, "scenario-a")
        self.assertEqual(tools.calls[0], ("search_logs", {"query": "ssh"}))

    async def test_activities_do_not_expose_hidden_reasoning(self):
        model = ScriptedModel([ModelDecision([ToolCall("get_timeline")]), ModelDecision(report=report())])
        _, events, _ = await self.run_agent(model)
        rendered = " ".join(event["message"].lower() for event in events)
        self.assertNotIn("chain", rendered)
        self.assertNotIn("reasoning", rendered)
        self.assertTrue(all(event["type"] in {"started", "tool_started", "tool_completed", "tool_failed", "finding", "completed", "failed"}
                            for event in events))


if __name__ == "__main__":
    unittest.main()

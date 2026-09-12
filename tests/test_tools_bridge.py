import unittest
from app.tools.bridge import dispatch


class BridgeTest(unittest.IsolatedAsyncioTestCase):
    async def test_missing_is_explicit_without_fallback(self):
        result = await dispatch({"scenario_id": "absent-bridge-test", "tool": "get_timeline"})
        self.assertEqual(result["error"]["code"], "SCENARIO_NOT_FOUND")

    async def test_demo_has_provenance(self):
        data = {"id": "absent-bridge-test", "events": [], "processes": [], "connections": [], "deployments": []}
        result = await dispatch({"scenario_id": data["id"], "tool": "get_connections", "sample_data": data})
        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["provenance"]["limitations"])

    async def test_forbidden_tool_and_overrides(self):
        for request in [{"tool":"__dict__"}, {"tool":"get_timeline","arguments":{"root":"/"}}, {"tool":"research_security_context","arguments":{"api_key":"x"}}]:
            self.assertFalse((await dispatch(request))["ok"])

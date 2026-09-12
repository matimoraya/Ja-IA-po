import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from app.tools import ScenarioTools, research_security_context


class ToolsTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("a", "b"):
            path = self.root / name
            path.mkdir()
            events = [
                {"id": name + "2", "timestamp": "2026-09-12T11:00:00-03:00", "host": "h1", "pid": 42, "message": "SSH accepted", "ip": "192.0.2.1"},
                {"id": name + "1", "timestamp": "2026-09-12T13:00:00Z", "host": "h1", "message": "SSH failed", "ip": "192.0.2.1"},
            ]
            data = {"id": name, "events": events, "processes": [{"host": "h1", "pid": 42, "event_ids": [name + "2"]}, {"host": "h2", "pid": 42}],
                    "connections": [{"host": "h1", "pid": 42}, {"host": "h2", "pid": 42}], "deployments": []}
            (path / "scenario.json").write_text(json.dumps(data), encoding="utf-8")
        self.tools = ScenarioTools("a", self.root)

    async def test_time_order_and_isolation(self):
        result = await self.tools.get_timeline()
        self.assertEqual([r["id"] for r in result["data"]["events"]], ["a1", "a2"])
        result = await self.tools.search_logs("SSH", start="2026-09-12T13:30:00Z")
        self.assertEqual([r["id"] for r in result["data"]["events"]], ["a2"])

    async def test_limit_and_empty(self):
        self.assertTrue((await self.tools.get_timeline(limit=1))["data"]["truncated"])
        self.assertEqual((await self.tools.search_logs("absent"))["data"]["events"], [])

    async def test_invalid_ranges_and_limits(self):
        for kwargs in ({"limit": -1}, {"start": "yesterday"}, {"start": "2026-09-12T00:00:00"},
                       {"start": "2026-09-13T00:00:00Z", "end": "2026-09-12T00:00:00Z"}):
            self.assertFalse((await self.tools.get_timeline(**kwargs))["ok"])

    async def test_process_host_isolation(self):
        data = (await self.tools.inspect_process("h1", 42))["data"]
        self.assertEqual(data["process"]["host"], "h1")
        self.assertEqual(len(data["connections"]), 1)
        self.assertEqual((await self.tools.get_connections("h2", 42))["data"]["connections"], [{"host": "h2", "pid": 42}])
        self.assertEqual((await self.tools.get_recent_deployments())["data"]["deployments"], [])

    async def test_missing_and_traversal(self):
        self.assertEqual((await ScenarioTools("missing", self.root).get_timeline())["error"]["code"], "SCENARIO_NOT_FOUND")
        self.assertEqual((await ScenarioTools("../a", self.root).get_timeline())["error"]["code"], "INVALID_SCENARIO")

    async def test_exa_sources_and_request(self):
        def transport(payload, key, timeout):
            self.assertEqual(payload["contents"], {"highlights": True})
            self.assertEqual(payload["numResults"], 3)
            return {"results": [{"title": "Source", "url": "https://example.org/security", "highlights": ["Evidence"]},
                                {"url": "javascript:alert(1)"}, {"url": "https://example.org/security"}]}
        result = await research_security_context("SSH mitigation", api_key="test-only", transport=transport)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["data"]["sources"]), 1)
        self.assertEqual(result["data"]["sources"][0]["excerpt"], "Evidence")

    async def test_exa_empty_and_malformed(self):
        result = await research_security_context("SSH mitigation", api_key="test", transport=lambda *a: {"results": []})
        self.assertEqual(result["data"]["sources"], [])
        result = await research_security_context("SSH mitigation", api_key="test", transport=lambda *a: {})
        self.assertEqual(result["error"]["code"], "INVALID_RESPONSE")

    async def test_exa_missing_key(self):
        result = await research_security_context("SSH mitigation", api_key="")
        self.assertEqual(result["error"]["code"], "MISSING_API_KEY")

    async def test_exa_errors_do_not_leak(self):
        for status, code in [(401, "INVALID_API_KEY"), (402, "INSUFFICIENT_CREDITS"), (429, "RATE_LIMITED"), (500, "PROVIDER_ERROR")]:
            def transport(*args):
                raise HTTPError("https://api.exa.ai/search", status, "secret-must-not-leak", {}, None)
            result = await research_security_context("SSH mitigation", api_key="test", transport=transport)
            self.assertEqual(result["error"]["code"], code)
            self.assertNotIn("secret-must-not-leak", json.dumps(result))

    async def test_exa_timeout(self):
        def transport(*args):
            raise TimeoutError("private details")
        result = await research_security_context("SSH mitigation", api_key="test", transport=transport)
        self.assertEqual(result["error"]["code"], "TIMEOUT")


if __name__ == "__main__":
    unittest.main()

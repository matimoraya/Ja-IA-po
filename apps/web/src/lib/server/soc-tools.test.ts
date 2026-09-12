import assert from "node:assert/strict";
import test from "node:test";
import { createSocService, pythonTool } from "./soc-tools";
const input = (tool: string, args = {}, containerId = "CONT-8A19") => ({ tool, arguments: args, containerId });
const ok = (data = {}) => ({ ok: true, data, error: null });

test("SOC validates arguments and container before invoking Python", async () => {
  let calls = 0;
  const service = createSocService(async () => { calls++; return ok(); });
  for (const value of [input("shell"), input("get_timeline", {}, "../secret"), input("search_logs", {query:"x",limit:-1}),
    input("get_timeline", {start:"yesterday"}), input("get_timeline", {root:"/tmp"})]) {
    assert.equal((await service(value,"test")).ok, false);
  }
  assert.equal(calls,0);
});

test("SOC caches identical searches and bounds new queries per container", async () => {
  let calls = 0;
  const service = createSocService(async () => { calls++; return ok({sources:[]}); });
  const query = (q: string) => input("research_security_context", {query:q});
  assert.equal((await service(query("Docker memory"),"same")).ok,true);
  assert.equal((await service(query("Docker memory"),"same")).data.cached,true);
  assert.equal((await service(query("Docker CPU"),"same")).ok,true);
  assert.equal((await service(query("Docker network"),"same")).error?.code,"SEARCH_BUDGET");
  assert.equal(calls,2);
  assert.equal((await service(input("research_security_context",{query:"Docker network"},"CONT-9B21"),"same")).ok,true);
});

test("SOC binds sample evidence to selected container and labels incomplete data", async () => {
  const service = createSocService(pythonTool);
  for (const container of ["CONT-8A19","CONT-9B21"]) {
    const result = await service(input("get_timeline", {}, container),"read");
    assert.equal(result.ok,true, JSON.stringify(result.error));
    const events = result.data.events as {id:string;host:string}[];
    assert.equal(events.length,3);
    assert.ok(events.every(event => event.id.startsWith(container) && event.host === container));
    assert.equal((result.data.provenance as {source:string}).source,"ui_demo_timeline");
  }
});

test("SOC returns provider failure without converting it to success or caching", async () => {
  const service = createSocService(async () => ({ok:false,data:{},error:{code:"MISSING_API_KEY",message:"Missing key"}}));
  const result = await service(input("research_security_context",{query:"Docker security"}),"missing");
  assert.equal(result.ok,false);
  assert.equal(result.error?.code,"MISSING_API_KEY");
});

test("SOC reads Elias scenarios with real evidence IDs and process correlations", async () => {
  const service = createSocService(pythonTool);
  for (const [container, prefix] of [["CONT-SOCA", "evt-a-"], ["CONT-SOCB", "evt-b-"]]) {
    const result = await service(input("get_timeline", {}, container), "scenario");
    assert.equal(result.ok, true, JSON.stringify(result.error));
    const events = result.data.events as { id: string }[];
    assert.ok(events.length > 0 && events.every(e => e.id.startsWith(prefix!)));
    assert.equal((result.data.provenance as { source: string }).source, "scenario_file");
  }
  const process = await service(input("inspect_process", {host:"web-01",pid:4368}, "CONT-SOCA"), "scenario");
  assert.equal(process.ok,true);
  assert.ok(process.data.process);
  assert.ok((process.data.connections as unknown[]).length > 0);
});

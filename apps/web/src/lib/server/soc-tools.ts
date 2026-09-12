import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { z } from "zod";
import { findIncident } from "../incidents";
import { SOC_SCENARIOS } from "../soc-scenarios";
import type { SocResult } from "../soc-types";

const date = z.string().datetime({ offset: true }).optional();
const windowFields = { start: date, end: date };
const args = {
  search_logs: z.object({ query: z.string().max(500), ...windowFields, ip: z.string().max(64).optional(), limit: z.number().int().min(1).max(100).optional() }).strict(),
  get_timeline: z.object({ ...windowFields, limit: z.number().int().min(1).max(100).optional() }).strict(),
  inspect_process: z.object({ host: z.string().min(1).max(100), pid: z.number().int().nonnegative() }).strict(),
  get_connections: z.object({ host: z.string().min(1).max(100).optional(), pid: z.number().int().nonnegative().optional() }).strict(),
  get_recent_deployments: z.object({ host: z.string().min(1).max(100).optional(), ...windowFields }).strict(),
  research_security_context: z.object({ query: z.string().trim().min(3).max(500) }).strict(),
};
const envelope = z.object({ containerId: z.string(), tool: z.enum(Object.keys(args) as [keyof typeof args, ...(keyof typeof args)[]]), arguments: z.record(z.string(), z.unknown()) }).strict();
const resultSchema = z.object({ ok: z.boolean(), data: z.record(z.string(), z.unknown()), error: z.object({ code: z.string(), message: z.string() }).nullable() });
export const fail = (code: string, message: string): SocResult => ({ ok: false, data: {}, error: { code, message } });

function projectRoot() {
  let current = resolve(process.cwd());
  for (let i = 0; i < 6; i++) {
    if (existsSync(resolve(current, "app/tools/bridge.py"))) return current;
    current = dirname(current);
  }
  throw new Error("SOC tools not found");
}

export function pythonTool(input: Record<string, unknown>): Promise<SocResult> {
  return new Promise((done) => {
    const root = projectRoot();
    const child = spawn(process.env.PYTHON_EXECUTABLE || "python", ["-X", "utf8", "-m", "app.tools.bridge"], {
      cwd: root, shell: false, windowsHide: true, stdio: ["pipe", "pipe", "pipe"],
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    let output = "", settled = false;
    const finish = (result: SocResult) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      done(result);
    };
    const timer = setTimeout(() => { child.kill(); finish(fail("TIMEOUT", "La consulta excedió 20 segundos.")); }, 20_000);
    child.on("error", () => finish(fail("PYTHON_UNAVAILABLE", "Configurar PYTHON_EXECUTABLE con Python 3.11+ y reiniciar.")));
    child.stdin.on("error", () => {});
    child.stderr.resume(); // Provider or process details may contain secrets.
    child.stdout.on("data", (chunk) => {
      output += chunk.toString();
      if (output.length > 2_000_000) { child.kill(); finish(fail("OUTPUT_LIMIT", "La respuesta es demasiado grande.")); }
    });
    child.on("close", (code) => {
      if (code !== 0) return finish(fail("TOOL_FAILED", "No se pudo ejecutar la consulta Python."));
      try { finish(resultSchema.parse(JSON.parse(output))); }
      catch { finish(fail("INVALID_RESPONSE", "La herramienta devolvió un resultado inválido.")); }
    });
    child.stdin.end(JSON.stringify(input));
  });
}

export function createSocService(run = pythonTool) {
  const cache = new Map<string, { expires: number; result: SocResult }>();
  const budget = new Map<string, { expires: number; calls: number }>();
  let active = 0;
  return async (raw: unknown, session: string): Promise<SocResult> => {
    const input = envelope.safeParse(raw);
    if (!input.success) return fail("INVALID_ARGUMENT", "Solicitud SOC inválida.");
    const { containerId, tool } = input.data;
    const parsed = args[tool].safeParse(input.data.arguments);
    if (!parsed.success) return fail("INVALID_ARGUMENT", "Filtros o argumentos inválidos.");
    let incident;
    try { incident = findIncident(containerId); }
    catch { return fail("UNKNOWN_CONTAINER", "Seleccionar un contenedor disponible."); }
    const now = Date.now();
    for (const [key, value] of cache) if (value.expires < now) cache.delete(key);
    for (const [key, value] of budget) if (value.expires < now) budget.delete(key);
    const key = JSON.stringify([session, containerId, tool, parsed.data]);
    const cached = cache.get(key);
    if (cached) return { ...cached.result, data: { ...cached.result.data, cached: true } };
    if (active >= 4) return fail("BUSY", "Hay consultas en curso. Intentar al terminar.");
    if (tool === "research_security_context") {
      const owner = `${session}:${containerId}`;
      const usage = budget.get(owner) ?? { expires: now + 90_000, calls: 0 };
      if (usage.calls >= 2) return fail("SEARCH_BUDGET", "Máximo de dos búsquedas nuevas por contenedor cada 90 segundos.");
      if (budget.size >= 200 && !budget.has(owner)) return fail("BUSY", "Capacidad temporal alcanzada.");
      usage.calls++;
      budget.set(owner, usage);
    }
    // Container ID is validated against the server catalog; never accept a path from the model.
    let mapping: Record<string, string> = Object.fromEntries(SOC_SCENARIOS.map(s => [s.containerId, s.scenarioId]));
    try { mapping = { ...mapping, ...z.record(z.string(), z.string().regex(/^[a-zA-Z0-9_-]+$/)).parse(JSON.parse(process.env.SOC_SCENARIO_MAP || "{}")) }; }
    catch { return fail("INVALID_CONFIGURATION", "SOC_SCENARIO_MAP debe ser un mapa JSON válido."); }
    const scenarioId = mapping[containerId] ?? containerId;
    const sample = { id: scenarioId, synthetic: true, events: incident.timeline.map((event, index) => ({
      id: `${containerId}-event-${index + 1}`, timestamp: `2026-09-12T${event.time}:00Z`, host: containerId,
      source: event.author, event_type: "observation", message: event.detail,
    })), processes: [], connections: [], deployments: [] };
    active++;
    try {
      const result = await run({ tool, arguments: parsed.data, scenario_id: scenarioId,
        // An explicit mapping must resolve a real scenario; never silently substitute a demo.
        ...(mapping[containerId] ? {} : { sample_data: sample }) });
      const enriched = { ...result, data: { ...result.data, container_id: containerId, cached: false, retrieved_at: new Date().toISOString() } };
      if (result.ok && tool === "research_security_context") {
        if (cache.size >= 100) cache.delete(cache.keys().next().value!);
        cache.set(key, { result: enriched, expires: now + 300_000 });
      }
      return enriched;
    } catch { return fail("TOOL_FAILED", "La consulta no pudo completarse."); }
    finally { active--; }
  };
}

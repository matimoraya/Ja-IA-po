import { randomBytes } from "node:crypto";
import { createSocService, fail } from "@/lib/server/soc-tools";
export const runtime = "nodejs";
const execute = createSocService();
export async function POST(request: Request) {
  const host = request.headers.get("host") || new URL(request.url).host;
  const origin = request.headers.get("origin");
  let expected: URL;
  try { expected = new URL(`http://${host}`); } catch { return Response.json(fail("FORBIDDEN", "Host inválido."), { status: 403 }); }
  const requestOrigin = `${new URL(request.url).protocol}//${host}`;
  const configuredOrigin = process.env.APP_ORIGIN?.replace(/\/$/, "");
  const loopback = ["localhost", "127.0.0.1", "[::1]"].includes(expected.hostname);
  if ((!loopback && configuredOrigin !== requestOrigin) || origin !== requestOrigin ||
      !request.headers.get("content-type")?.startsWith("application/json")) {
    return Response.json(fail("FORBIDDEN", "Origen no autorizado para consultar herramientas."), { status: 403 });
  }
  const cookie = request.headers.get("cookie")?.match(/(?:^|;\s*)soc-session=([a-f0-9]{32})(?:;|$)/)?.[1];
  const session = cookie || randomBytes(16).toString("hex");
  const secure = new URL(request.url).protocol === "https:" ? "; Secure" : "";
  const headers = { "Cache-Control": "no-store", ...(!cookie ? { "Set-Cookie": `soc-session=${session}; HttpOnly; SameSite=Strict${secure}; Path=/api/soc-tools; Max-Age=3600` } : {}) };
  try {
    const text = await request.text();
    if (text.length > 4096) return Response.json(fail("INVALID_ARGUMENT", "Solicitud demasiado grande."), { status: 413, headers });
    const result = await execute(JSON.parse(text), session);
    return Response.json(result, { headers });
  } catch { return Response.json(fail("INVALID_ARGUMENT", "JSON inválido."), { status: 400, headers }); }
}

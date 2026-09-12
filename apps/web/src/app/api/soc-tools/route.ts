import { randomBytes } from "node:crypto";
import { createSocService, fail } from "@/lib/server/soc-tools";
export const runtime = "nodejs";
const execute = createSocService();
export async function POST(request: Request) {
  const host = request.headers.get("host") || new URL(request.url).host;
  const origin = request.headers.get("origin");
  let expected: URL;
  try { expected = new URL(`http://${host}`); } catch { return Response.json(fail("FORBIDDEN", "Host inválido."), { status: 403 }); }
  if (!["localhost", "127.0.0.1", "[::1]"].includes(expected.hostname) ||
      origin !== `${new URL(request.url).protocol}//${host}` ||
      !request.headers.get("content-type")?.startsWith("application/json")) {
    return Response.json(fail("FORBIDDEN", "Usar la aplicación local para consultar herramientas."), { status: 403 });
  }
  const cookie = request.headers.get("cookie")?.match(/(?:^|;\s*)soc-session=([a-f0-9]{32})(?:;|$)/)?.[1];
  const session = cookie || randomBytes(16).toString("hex");
  const headers = { "Cache-Control": "no-store", ...(!cookie ? { "Set-Cookie": `soc-session=${session}; HttpOnly; SameSite=Strict; Path=/api/soc-tools; Max-Age=3600` } : {}) };
  try {
    const text = await request.text();
    if (text.length > 4096) return Response.json(fail("INVALID_ARGUMENT", "Solicitud demasiado grande."), { status: 413, headers });
    const result = await execute(JSON.parse(text), session);
    return Response.json(result, { headers });
  } catch { return Response.json(fail("INVALID_ARGUMENT", "JSON inválido."), { status: 400, headers }); }
}

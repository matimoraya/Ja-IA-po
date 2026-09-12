export const runtime = "nodejs";

function configured(name: string) {
  const value = process.env[name]?.trim();
  return Boolean(value && !/^(stub|test|preview|replace|your[-_])/i.test(value));
}

export async function GET() {
  const provider = (process.env.MODEL_PROVIDER || "openai").toLowerCase();
  const chatConfigured = provider === "openrouter"
    ? configured("OPENROUTER_API_KEY")
    : configured("OPENAI_API_KEY");

  return Response.json({
    chatConfigured,
    exaConfigured: configured("EXA_API_KEY"),
    dataMode: "synthetic-scenarios",
    actionStorage: configured("AMBIGUOUS_API_KEY") ? "persistent" : "local-session",
  }, { headers: { "Cache-Control": "no-store" } });
}

export type SocResult = {
  ok: boolean;
  data: Record<string, unknown>;
  error: { code: string; message: string } | null;
};
export type SocObservation = {
  containerId: string;
  tool: string;
  state: "running" | "done";
  result?: SocResult;
};

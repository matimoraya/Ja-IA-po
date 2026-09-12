// Public catalog only; event records remain on the Python/server side.
export const SOC_SCENARIOS = [
  { containerId: "CONT-SOCA", scenarioId: "scenario-a", host: "web-01", title: "Actividad remota fuera de horario" },
  { containerId: "CONT-SOCB", scenarioId: "scenario-b", host: "reports-01", title: "Accesos remotos y cambios en reportes" },
] as const;

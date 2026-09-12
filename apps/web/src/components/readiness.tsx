"use client";

import { useEffect, useState } from "react";

type Readiness = {
  chatConfigured: boolean;
  exaConfigured: boolean;
  dataMode: string;
  actionStorage: string;
};

export function ReadinessStatus() {
  const [status, setStatus] = useState<Readiness | null>(null);
  useEffect(() => {
    fetch("/api/readiness", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  if (!status) return null;
  return (
    <aside className="ck-readiness" aria-label="Estado de integraciones">
      <strong>Estado:</strong>
      <span className={status.exaConfigured ? "is-ready" : "is-missing"}>Exa {status.exaConfigured ? "conectado" : "sin configurar"}</span>
      <span className={status.chatConfigured ? "is-ready" : "is-missing"}>Agente {status.chatConfigured ? "conectado" : "requiere clave del modelo"}</span>
      <span>Datos de escenarios sintéticos</span>
      <span>Acciones en {status.actionStorage === "persistent" ? "almacenamiento persistente" : "sesión local"}</span>
    </aside>
  );
}

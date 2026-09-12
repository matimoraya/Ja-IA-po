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
      <strong>Servicios</strong>
      <span className={status.exaConfigured ? "is-ready" : "is-missing"}><i /> Exa {status.exaConfigured ? "operativo" : "sin configurar"}</span>
      <span className={status.chatConfigured ? "is-ready" : "is-missing"}><i /> Modelo {status.chatConfigured ? "operativo" : "pendiente"}</span>
      <span><i /> Escenarios locales</span>
      <span><i /> {status.actionStorage === "persistent" ? "Registro persistente" : "Registro de sesión"}</span>
    </aside>
  );
}

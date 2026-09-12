"use client";

import { useCallback, useState } from "react";
import {
  CopilotChat,
  useConfigureSuggestions,
} from "@copilotkit/react-core/v2";
import { SocTools } from "@/components/soc-tools";
import { ReadinessStatus } from "@/components/readiness";
import { GenerativeUI } from "@/components/generative-ui";
import { AppControl } from "@/components/app-control";
import { findIncident, incidents, workspaceContext } from "@/lib/incidents";
import { useWorkplace } from "@/lib/use-workplace";
import { WorkplaceFollowups } from "@/components/workplace-followups";

export default function Home() {
  const [selectedId, setSelectedId] = useState<string>(incidents[0].id);
  const workplace = useWorkplace(selectedId);
  const { selectedIncident: incident } = workspaceContext(
    selectedId,
    workplace.status?.status === "connected" ? workplace.status.tasks : [],
  );
  const selectIncident = useCallback((id: string) => {
    setSelectedId(findIncident(id).id);
  }, []);

  useConfigureSuggestions(
    {
      suggestions: [
        {
          title: "Analyze this container",
          message:
            "Analyze the selected container using the page context. Is there suspicious activity or errors?",
        },
        {
          title: "Propose an action",
          message:
            "Prepare a Docker action for the selected container. Show me the proposal before it is saved.",
        },
      ],
      available: "before-first-message",
    },
    [],
  );

  return (
    <>
      <GenerativeUI />
      <AppControl
        selectedId={selectedId}
        selectIncident={selectIncident}
        workplace={workplace}
      />
      <main className="ck-workspace">
        <header className="ck-workspace-header">
          <div>
            <p className="ck-eyebrow">Ja-IA-po · Docker SOC Agent</p>
            <h1>Asistente SOC para Docker</h1>
            <p className="ck-intro">
              Selecciona un contenedor, investiga la evidencia y revisa la acción propuesta.
            </p>
          </div>
          <span className="ck-tag">Escenarios sintéticos</span>
        </header>

        <ReadinessStatus />

        <SocTools key={selectedId} containerId={selectedId} />
        <div className="ck-workspace-grid">
          <section className="ck-panel" aria-labelledby="incident-title">
            <div className="ck-incident-picker">
              <label htmlFor="incident-select">Contenedor</label>
              <select
                id="incident-select"
                value={selectedId}
                onChange={(event) => selectIncident(event.target.value)}
              >
                {incidents.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.id} · {item.service}
                  </option>
                ))}
              </select>
            </div>

            <div className="ck-detail">
              <span className="ck-status-label">{incident.status}</span>
              <h2 id="incident-title">{incident.title}</h2>
              <p>{incident.summary}</p>
              <details className="ck-more" key={incident.id}>
                <summary>Detalles y línea de tiempo</summary>
                <dl className="ck-detail-facts">
                  <div>
                    <dt>Responsable</dt>
                    <dd>{incident.owner}</dd>
                  </div>
                  <div>
                    <dt>Severidad</dt>
                    <dd>{incident.severity}</dd>
                  </div>
                  <div>
                    <dt>Última actualización</dt>
                    <dd>{incident.updated}</dd>
                  </div>
                </dl>
                <h3>Impacto</h3>
                <p>{incident.impact}</p>
                <h3>Línea de tiempo</h3>
                <ol className="ck-timeline">
                  {incident.timeline.map((event) => (
                    <li key={event.time}>
                      <time>{event.time} UTC</time>
                      <div>
                        <strong>{event.author}</strong>
                        <p>{event.detail}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              </details>
            </div>

            <WorkplaceFollowups incidentId={selectedId} workplace={workplace} />
          </section>

          <section
            className="ck-panel ck-assistant"
            aria-labelledby="assistant-title"
          >
            <header className="ck-assistant-header">
              <h2 id="assistant-title">Consultar al asistente</h2>
              <p>Puede investigar este contenedor y preparar acciones para revisión.</p>
            </header>
            <CopilotChat
              className="ck-chat"
              labels={{
                welcomeMessageText: "¿Qué contenedor necesita investigación?",
                chatInputPlaceholder: "Pregunta sobre este contenedor…",
              }}
            />
          </section>
        </div>
      </main>
    </>
  );
}

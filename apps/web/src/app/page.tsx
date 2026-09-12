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
          title: "Investigar caso completo",
          message:
            "Ejecuta una investigación completa del contenedor seleccionado. Primero consulta su línea de tiempo y la evidencia local disponible; después correlaciona procesos, conexiones y despliegues cuando existan. Busca con Exa contexto público sobre la técnica o el fallo observado sin enviar datos privados. Entrega una clasificación, severidad, resumen, hallazgos y recomendaciones. Cita los IDs exactos de evidencia local y de fuentes públicas, separa hechos de contexto externo y declara cualquier limitación o dato faltante.",
        },
        {
          title: "Preparar respuesta segura",
          message:
            "Basándote únicamente en la evidencia observada del contenedor seleccionado, prepara una acción de respuesta con su justificación, riesgo e impacto esperado. No afirmes que fue ejecutada y muéstrala para revisión humana antes de registrarla.",
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
      <div className="ck-app-shell">
        <aside className="ck-sidebar">
          <div className="ck-brand">
            <span className="ck-brand-mark" aria-hidden="true">J</span>
            <div><strong>Ja-IA-po</strong><small>Security Operations</small></div>
          </div>
          <nav className="ck-nav" aria-label="Navegación principal">
            <span className="ck-nav-item is-active"><b aria-hidden="true">⌁</b><span className="ck-nav-label">Investigación</span></span>
            <span className="ck-nav-item"><b aria-hidden="true">▦</b><span className="ck-nav-label">Escenarios</span><em>{incidents.length}</em></span>
            <span className="ck-nav-item"><b aria-hidden="true">◇</b><span className="ck-nav-label">Evidencias</span></span>
            <span className="ck-nav-item"><b aria-hidden="true">✓</b><span className="ck-nav-label">Acciones</span></span>
          </nav>
          <div className="ck-sidebar-foot">
            <span className="ck-live-dot" aria-hidden="true" />
            <div><strong>Entorno de demo</strong><small>Datos sintéticos controlados</small></div>
          </div>
        </aside>

      <main className="ck-workspace">
        <div className="ck-topbar">
          <span>Centro de operaciones <b>/</b> Investigación activa</span>
          <span className="ck-session"><i aria-hidden="true" /> Sesión protegida</span>
        </div>
        <header className="ck-workspace-header">
          <div>
            <p className="ck-eyebrow">CASO ACTIVO · {selectedId}</p>
            <h1>Asistente SOC para Docker</h1>
            <p className="ck-intro">
              Reúne evidencia, contrasta fuentes y prepara una respuesta controlada.
            </p>
          </div>
          <span className="ck-tag ck-tag--warning"><i aria-hidden="true" /> Entorno simulado</span>
        </header>

        <ReadinessStatus />

        <section className="ck-metrics" aria-label="Resumen del escenario">
          <article><span>Severidad</span><strong>{incident.severity}</strong><small>Prioridad del caso</small></article>
          <article><span>Estado</span><strong>{incident.status}</strong><small>Monitoreo activo</small></article>
          <article><span>Evidencias</span><strong>{incident.timeline.length}</strong><small>Eventos correlacionados</small></article>
          <article><span>Responsable</span><strong>{incident.owner}</strong><small>Asignación actual</small></article>
        </section>

        <SocTools key={selectedId} containerId={selectedId} />
        <div className="ck-workspace-grid">
          <section className="ck-panel ck-case-panel" aria-labelledby="incident-title">
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
              <span className="ck-status-label"><i aria-hidden="true" /> {incident.status}</span>
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
              <div className="ck-assistant-icon" aria-hidden="true">J</div>
              <div><h2 id="assistant-title">Analista de apoyo</h2>
              <p>Investiga el contexto visible y prepara acciones para tu revisión.</p></div>
              <span className="ck-agent-state"><i aria-hidden="true" /> Disponible</span>
            </header>
            <div className="ck-runbook" aria-label="Flujo de investigación guiada">
              <strong>Runbook guiado</strong>
              <span><b>1</b> Evidencia local</span><i aria-hidden="true">→</i>
              <span><b>2</b> Correlación</span><i aria-hidden="true">→</i>
              <span><b>3</b> Fuentes Exa</span><i aria-hidden="true">→</i>
              <span><b>4</b> Decisión revisable</span>
            </div>
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
      </div>
    </>
  );
}

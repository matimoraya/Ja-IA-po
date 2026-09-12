"use client";

import { useState, type FormEvent } from "react";
import type { WorkplaceControls } from "@/lib/use-workplace";

export function WorkplaceFollowups({
  incidentId,
  workplace,
}: {
  incidentId: string;
  workplace: WorkplaceControls;
}) {
  const [title, setTitle] = useState("");
  const [details, setDetails] = useState("");
  const [error, setError] = useState("");
  const [preparing, setPreparing] = useState(false);
  const { status, proposal, busy, notice } = workplace;
  const tasks = status?.status === "connected" ? status.tasks : [];

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPreparing(true);
    setError("");
    try {
      await workplace.propose({ incidentId, title, details });
      setTitle("");
      setDetails("");
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Unable to prepare proposal.",
      );
    } finally {
      setPreparing(false);
    }
  }

  async function refresh() {
    setError("");
    try {
      await workplace.refresh();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to refresh actions.",
      );
    }
  }

  return (
    <section className="ck-followups" aria-labelledby="followup-title">
      <header className="ck-followups-header">
        <div>
          <h2 id="followup-title">Plan de respuesta</h2>
          <p className="ck-local-note">
            Ninguna acción se registra sin tu aprobación.
          </p>
        </div>
        <span className="ck-tag">Registro local</span>
      </header>

      {status?.status === "unconfigured" ? (
        <div className="ck-setup-note">
          <strong>Registro temporal activo</strong>
          <p>{status.message}</p>
        </div>
      ) : status?.status === "connected" ? (
        <p className="ck-local-note">
          Sesión de {status.identityName}.
        </p>
      ) : (
        <p className="ck-local-note">
          {workplace.error
            ? "El registro de acciones no está disponible."
            : "Conectando…"}
        </p>
      )}

      {tasks.length ? (
        <ul className="ck-task-list">
          {tasks.map((task) => (
            <li key={task.id}>
              <span aria-hidden="true">○</span>
              <div>
                <strong>{task.title}</strong>
                <code className="ck-record-id">{task.id}</code>
                {task.url ? (
                  <a href={task.url} target="_blank" rel="noreferrer">
                    Ver registro de acción
                  </a>
                ) : (
                  <span className="ck-muted">
                    Usa este identificador dentro del espacio de trabajo.
                  </span>
                )}
                <details>
                  <summary>Detalles guardados</summary>
                  <p className="ck-preserve-lines">{task.description}</p>
                </details>
              </div>
            </li>
          ))}
        </ul>
      ) : status?.status === "connected" ? (
        <p className="ck-empty">Todavía no hay acciones registradas para {incidentId}.</p>
      ) : null}

      <button
        type="button"
        className="ck-btn"
        disabled={busy}
        onClick={refresh}
      >
        Actualizar registro
      </button>

      <form onSubmit={submit} className="ck-task-form ck-task-form--stacked">
        <label className="ck-sr-only" htmlFor="task-title">
          New action for {incidentId}
        </label>
        <input
          id="task-title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          maxLength={200}
          placeholder="Título de la acción (ej. Aislar contenedor)"
          required
        />
        <label className="ck-sr-only" htmlFor="task-details">
          Action details
        </label>
        <textarea
          id="task-details"
          value={details}
          onChange={(event) => setDetails(event.target.value)}
          maxLength={4000}
          placeholder="Describe la acción, el motivo y el resultado esperado"
          required
          rows={3}
        />
        <button
          className="ck-btn ck-btn--primary"
          disabled={status?.status !== "connected" || preparing || busy}
          type="submit"
        >
          {preparing ? "Preparando…" : "Revisar propuesta"}
        </button>
      </form>

      {proposal && (
        <section className="ck-approval" aria-label="Aprobar acción">
          <h3>Revisar antes de registrar</h3>
          <p>
            Se registrará como {proposal.identityName}. Vence a las{" "}
            {new Date(proposal.expiresAt).toLocaleTimeString()}.
          </p>
          <strong>{proposal.title}</strong>
          <p className="ck-preserve-lines">{proposal.description}</p>
          <div className="ck-approval-actions">
            <button
              type="button"
              className="ck-btn ck-btn--primary"
              disabled={busy}
              onClick={workplace.approve}
            >
              {busy ? "Procesando…" : "Aprobar acción"}
            </button>
            <button
              type="button"
              className="ck-btn"
              disabled={busy}
              onClick={workplace.deny}
            >
              Rechazar
            </button>
          </div>
        </section>
      )}

      {(error || workplace.error) && (
        <p role="alert" className="ck-error">
          {error || workplace.error}
        </p>
      )}
      <p role="status" className="ck-notice">
        {notice}
      </p>
    </section>
  );
}

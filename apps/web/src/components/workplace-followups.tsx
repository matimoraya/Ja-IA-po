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
          <h2 id="followup-title">Docker Actions</h2>
          <p className="ck-local-note">
            Proposals are saved only after page approval.
          </p>
        </div>
        <span className="ck-tag">Local Log</span>
      </header>

      {status?.status === "unconfigured" ? (
        <div className="ck-setup-note">
          <strong>Backend configured to run in Mock Mode</strong>
          <p>{status.message}</p>
        </div>
      ) : status?.status === "connected" ? (
        <p className="ck-local-note">
          Saving as {status.identityName}.
        </p>
      ) : (
        <p className="ck-local-note">
          {workplace.error
            ? "Action logging unavailable."
            : "Connecting…"}
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
                    View Action Record
                  </a>
                ) : (
                  <span className="ck-muted">
                    No URL provided. Use this ID in the workspace.
                  </span>
                )}
                <details>
                  <summary>Saved details</summary>
                  <p className="ck-preserve-lines">{task.description}</p>
                </details>
              </div>
            </li>
          ))}
        </ul>
      ) : status?.status === "connected" ? (
        <p className="ck-empty">No saved actions for {incidentId}.</p>
      ) : null}

      <button
        type="button"
        className="ck-btn"
        disabled={busy}
        onClick={refresh}
      >
        Refresh actions
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
          placeholder="Write an action title (e.g. Restart Container)…"
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
          placeholder="What action should be taken?"
          required
          rows={3}
        />
        <button
          className="ck-btn ck-btn--primary"
          disabled={status?.status !== "connected" || preparing || busy}
          type="submit"
        >
          {preparing ? "Preparing…" : "Review"}
        </button>
      </form>

      {proposal && (
        <section className="ck-approval" aria-label="Approve Action">
          <h3>Approve this Action</h3>
          <p>
            Save as {proposal.identityName}. Expires{" "}
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
              {busy ? "Working…" : "Approve Action"}
            </button>
            <button
              type="button"
              className="ck-btn"
              disabled={busy}
              onClick={workplace.deny}
            >
              Decline
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

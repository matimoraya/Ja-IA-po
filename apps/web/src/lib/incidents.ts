/** Sample container context. Follow-ups are retrieved separately from Ambiguous. */
import type { WorkplaceTask } from "./followup-types";

export const incidents = [
  {
    id: "CONT-8A19",
    title: "Database Container Restarting",
    severity: "High",
    status: "CrashLoopBackOff",
    service: "PostgreSQL DB",
    owner: "Alex Rivera",
    channel: "#ops-db",
    updated: "09:24 UTC",
    summary:
      "The PostgreSQL container is repeatedly crashing. Logs show an out-of-memory error and connection pool exhaustion.",
    impact:
      "All services dependent on the database are currently experiencing 5xx errors.",
    timeline: [
      {
        time: "09:12",
        author: "Docker Swarm",
        detail: "Container CONT-8A19 started.",
      },
      {
        time: "09:17",
        author: "Monitor",
        detail: "Memory usage exceeded 2GB limit. Container killed.",
      },
      {
        time: "09:24",
        author: "Alex Rivera",
        detail:
          "Investigating memory leak. Considering increasing memory limit or debugging connection pool.",
      },
    ],
  },
  {
    id: "CONT-9B21",
    title: "Web Frontend High CPU",
    severity: "Medium",
    status: "Running (Degraded)",
    service: "Next.js Frontend",
    owner: "Maya Chen",
    channel: "#ops-frontend",
    updated: "09:31 UTC",
    summary:
      "The web frontend container is using 100% of its allocated CPU. Response times are elevated.",
    impact:
      "Users are experiencing slow page loads. No downtime reported yet.",
    timeline: [
      {
        time: "09:05",
        author: "Support",
        detail: "Customers report slow loading pages.",
      },
      {
        time: "09:19",
        author: "Maya Chen",
        detail: "Scaled up the container instances, but CPU per instance remains high.",
      },
      {
        time: "09:31",
        author: "Monitor",
        detail: "CPU usage stuck at 99%. Possible infinite loop in recent deploy.",
      },
    ],
  },
] as const;

export type Incident = (typeof incidents)[number];

export function findIncident(id: string): Incident {
  const incident = incidents.find((item) => item.id === id);
  if (!incident)
    throw new Error(
      `Unknown container ${id}. Choose ${incidents.map((item) => item.id).join(" or ")}.`,
    );
  return incident;
}

export function workspaceContext(
  selectedId: string,
  followups: WorkplaceTask[],
) {
  return {
    dataSource:
      "Fictional sample Docker containers. Actions shown here were retrieved for the selected container. A proposal is not a saved task.",
    availableIncidents: incidents.map(({ id, title, status }) => ({
      id,
      title,
      status,
    })),
    selectedIncident: {
      ...findIncident(selectedId),
      timeline: [...findIncident(selectedId).timeline],
    },
    followups,
  };
}

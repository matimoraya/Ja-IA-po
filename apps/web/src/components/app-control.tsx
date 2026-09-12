"use client";

import { useFrontendTool, useAgentContext } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { findIncident, workspaceContext } from "@/lib/incidents";
import type { WorkplaceControls } from "@/lib/use-workplace";

async function toolResult<T>(action: () => Promise<T>) {
  try {
    return await action();
  } catch (error) {
    return {
      status: "error",
      message:
        error instanceof Error
          ? error.message
          : "Workplace operation failed. Check the page for setup details.",
    };
  }
}

export function AppControl({
  selectedId,
  selectIncident,
  workplace,
}: {
  selectedId: string;
  selectIncident: (id: string) => void;
  workplace: WorkplaceControls;
}) {
  const { status, propose, retrieve } = workplace;

  useAgentContext({
    description:
      "The Docker workspace currently visible to the user, including container status, logs timeline and proposed actions. CRITICAL: propose_docker_action only prepares a proposal. Only the user's approval button saves it; prose/chat approval never executes a write. Use retrieve_docker_action or refresh_docker_actions for real reads. Never claim an action was saved without a provider record. Never invent record links.",
    value: {
      ...workspaceContext(
        selectedId,
        status?.status === "connected" ? status.tasks : [],
      ),
      workplace: status?.status ?? "unavailable",
      workplaceError: workplace.error,
      proposal: workplace.proposal ?? null,
      lastResult: workplace.notice,
    },
  });

  useFrontendTool(
    {
      name: "select_container",
      description:
        "Open an existing sample container in the workspace. Use an ID from availableIncidents.",
      parameters: z.object({ incidentId: z.string() }),
      handler: async ({ incidentId }) => {
        const incident = findIncident(incidentId);
        selectIncident(incident.id);
        return `Opened ${incident.id}: ${incident.title}. The visible details and agent context now show this container.`;
      },
    },
    [selectIncident],
  );

  useFrontendTool(
    {
      name: "inspect_container_logs",
      description:
        "Mock Docker logs retrieval for a container. Returns sample logs to help with analysis.",
      parameters: z.object({ incidentId: z.string() }),
      handler: async ({ incidentId }) => {
        const incident = findIncident(incidentId);
        return `Mock Logs for ${incident.id}: Error at 09:24 UTC. Reason: ${incident.summary}`;
      },
    },
    [],
  );

  useFrontendTool(
    {
      name: "propose_docker_action",
      description:
        "Prepare an action from the selected container context. Show the exact title and details for the user's approval button. Does not save anything. CRITICAL: wait for the user to click Approve.",
      parameters: z.object({
        incidentId: z.string(),
        title: z.string().trim().min(1).max(200),
        details: z.string().trim().min(1).max(4000),
      }),
      handler: async (draft) =>
        toolResult(async () => ({
          status: "pending_approval",
          proposal: await propose(draft),
        })),
    },
    [propose],
  );

  useFrontendTool(
    {
      name: "retrieve_docker_action",
      description:
        "Retrieve an existing action by its actual ID. Read-only; never creates a duplicate.",
      parameters: z.object({ id: z.uuid() }),
      handler: async ({ id }) => toolResult(() => retrieve(id)),
    },
    [retrieve],
  );

  useFrontendTool(
    {
      name: "refresh_docker_actions",
      description:
        "Read saved actions for the currently selected container. Use after approval or browser refresh to verify persistence.",
      parameters: z.object({}),
      handler: async () => toolResult(() => workplace.refresh()),
    },
    [workplace.refresh],
  );

  return null;
}

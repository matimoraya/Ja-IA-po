import assert from "node:assert/strict";
import test from "node:test";
import { findIncident, workspaceContext } from "./incidents";
import type { WorkplaceTask } from "./followup-types";

test("selection changes the shared container and timeline together", () => {
  const db = workspaceContext("CONT-8A19", []);
  const frontend = workspaceContext("CONT-9B21", []);
  assert.equal(db.selectedIncident.service, "PostgreSQL DB");
  assert.equal(frontend.selectedIncident.service, "Next.js Frontend");
  assert.match(frontend.selectedIncident.timeline[0].detail, /loading/);
  assert.equal(frontend.availableIncidents.length, 2);
});

test("workspace context labels sample containers and provider actions", () => {
  const tasks: WorkplaceTask[] = [
    {
      id: "11111111-1111-4111-8111-111111111111",
      title: "Restart DB",
      description: "Provider task details\nagents-everywhere:CONT-8A19",
      url: null,
    },
  ];
  const context = workspaceContext("CONT-8A19", tasks);
  assert.throws(() => findIncident("unknown"), /Unknown container/);
  assert.match(context.dataSource, /Fictional sample/);
  assert.deepEqual(context.followups, tasks);
});

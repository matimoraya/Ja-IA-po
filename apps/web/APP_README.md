# Ja-IA-po Docker SOC Agent

This is a web-based Assistant tailored for software engineers and operations teams to monitor and review suspicious Docker container activity. It is built using **OpenAI + CopilotKit React** and features local execution caching via a `MockWorkplace`.

## Getting Started

This app runs fully locally by default using mocked API keys and local state. To run it:

```bash
npm run dev:web
```

Open `http://localhost:3100`. The app UI provides a dashboard where you can:
1. Select a container (e.g., `CONT-8A19` for PostgreSQL or `CONT-9B21` for Next.js).
2. Ask the assistant to "Inspect container logs" or "What's wrong with this container?"
3. Ask the assistant to "Create a follow-up action" or "Propose an action" (like Restart, Ignore, etc.).
4. Review the proposition on the UI, and click **Approve** to mock-save the action.

## Core Architecture for Other Agents

If you are an agent tasked with continuing the development of this application, here is what you need to know about the current implementation:

- **Mocked Persistence (`MockWorkplace`)**: We have intentionally bypassed the Ambiguous AI requirement for speed and ease-of-use. `apps/web/src/lib/server/workplace.ts` exposes a `MockWorkplace` that is used whenever `AMBIGUOUS_API_KEY` is not present. This stores tasks in-memory. **Do not attempt to restore Ambiguous AI integration unless explicitly instructed to by the user.**
- **Container Data (`incidents.ts`)**: The application uses mock Docker containers instead of generic IT incidents. Containers follow the `CONT-XXXX` naming convention. Do not use the old `INC-XXXX` format.
- **Tools (`app-control.tsx`)**: The UI defines custom CopilotKit tools tailored to Docker management:
  - `inspect_container_logs`: Reads logs from the selected container.
  - `propose_docker_action`: Proposes a task for approval on the UI.
  - `retrieve_docker_action`: Recalls actions previously stored in the `MockWorkplace`.
- **Testing**: We have adapted `incidents.test.ts`, `followup-http.test.ts`, and `workplace.test.ts` to expect the new container IDs and the mock behavior. Run `npm run verify` to test the entire suite before completing your tasks.

## Giving Instructions to Agents

To extend this application, provide this exact context to your coding agent:

```text
Read apps/web/APP_README.md. The application is a Docker SOC Agent using CopilotKit.
We are using a MockWorkplace instead of Ambiguous AI to store tasks.
Containers use the CONT- schema. Ensure that any new CopilotKit frontend tools 
you create relate directly to Docker management and are rendered for approval 
on the page if they execute state-changing actions. Run `npm run verify` to
verify changes.
```

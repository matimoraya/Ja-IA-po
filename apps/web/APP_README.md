# Ja-IA-po Docker SOC Agent

This is a web-based Assistant tailored for software engineers and operations teams to monitor and review suspicious Docker container activity. It is built using **OpenAI + CopilotKit React** and features local execution caching via a `MockWorkplace`.

## Getting Started

The interface and synthetic SOC queries run locally. Exa requires `EXA_API_KEY`, and the CopilotKit chat requires a real model-provider key. To run it:

```bash
npm run dev:web
```

Open `http://localhost:3100`. The app UI provides a dashboard where you can:
1. Select a container (e.g., `CONT-8A19` for PostgreSQL or `CONT-9B21` for Next.js).
2. Use **Consultar eventos** and **Buscar fuentes** to verify the SOC tools independently from the model.
3. Ask the assistant to inspect the selected container and cite event/source IDs.
4. Ask the assistant to create a follow-up action.
5. Review the proposal and approve or decline it. Without `AMBIGUOUS_API_KEY`, approved actions remain in local session storage.

## Core Architecture for Other Agents

If you are an agent tasked with continuing the development of this application, here is what you need to know about the current implementation:

- **Mocked Persistence (`MockWorkplace`)**: We have intentionally bypassed the Ambiguous AI requirement for speed and ease-of-use. `apps/web/src/lib/server/workplace.ts` exposes a `MockWorkplace` that is used whenever `AMBIGUOUS_API_KEY` is not present. This stores tasks in-memory. **Do not attempt to restore Ambiguous AI integration unless explicitly instructed to by the user.**
- **SOC evidence**: `scenario-a` and `scenario-b` come from the team's JSON scenario files. The older Docker entries use explicitly labelled UI demo timelines. All data is synthetic.
- **Exa**: `research_security_context` calls Exa `/search` through the controlled Python bridge and returns stable source IDs, URLs and highlights.
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

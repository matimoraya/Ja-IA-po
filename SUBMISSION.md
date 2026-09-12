# Submission checklist

Choose your city on the [global event page](https://aitinkerers.org/hackathons/global/agents-everywhere). Use that city's participant portal for the submission deadline and published judging criteria, and its handbook for eligibility and required deliverables. See [hackathon-rules.md](hackathon-rules.md) for the agent-readable summary.

## Build eligibility

- [x] Our submitted project is a net-new build created during the official hackathon period
- [x] Its core functionality was built during the event; we are not resubmitting or extending a pre-existing project and entering it as new
- [x] We identify inherited templates, libraries, prompts, components, and starter code separately from our event work

**What we inherited**
- Agents Everywhere Starter Kit (apps/web template)
- Next.js UI, CopilotKit setup
- Standard hackathon README and instructions.

**What we built during the hackathon**
- Adapted the CopilotKit web template into a Docker SOC Assistant.
- Implemented mock container lists (`incidents.ts`).
- Created custom frontend tools (`inspect_container_logs`, `propose_docker_action`, `retrieve_docker_action`).
- Modified the Next.js page UI to support analyzing containers, handling approvals, and logging local Actions.

## Title and description

**What you built**
Ja-IA-po Docker SOC Assistant: A web dashboard to review suspicious Docker container activity. Analysts can select a container and use the in-app CopilotKit assistant to fetch mock logs, perform an analysis, and propose an action.

**Who it is for**
Software Engineers and ops working with Docker containers.

**Why the context matters**
The agent reads the specific container logs and context from the UI without the user having to switch context to a command line. It also allows the user to immediately perform an approval from the same page, bridging the gap between analysis and action.

**Sponsor technologies used**
- CopilotKit React UI and `useCopilotChat`
- CopilotKit Frontend Tools
- OpenAI (as the backing model for CopilotKit)

## Evidence for the judging criteria

Judges score each of the four official criteria from 1–5. This checklist helps you gather evidence; it does not guarantee a score. A working starter is a foundation for your own project.

| Official criterion | Show in your project and demo |
|---|---|
| Core Requirements & Functionality | Run one complete workflow in the intended environment, from user request through tools to a verified result. Repeat it with live integrations; offline tests alone do not prove the deployed flow. |
| Innovation & Theme Alignment | Show the surrounding context before the prompt and explain the original interaction it enables. Compare with the context removed: what value would a standalone chatbox lose? |
| Technical Execution & Integration | Show how tools, data, and the environment connect. Demonstrate a relevant failure or cancellation path and explain recovery, state persistence, and integration limits. |
| Usefulness & Agentic Experience | Identify the user and problem, show a meaningful action in the surface, and demonstrate clear feedback and appropriate user control. Explain what work the agent saves. |

- [x] We can point to visible evidence for every criterion
- [x] We distinguish live services, sample data, session-only state, and standalone recipes
- [x] Sponsor technologies contribute to the workflow; their count is not a judging criterion

## Public repository

- [x] A new participant can run the quickstart from a clean clone
- [x] The README lists the credentials and separate processes required
- [x] `npm run verify` passes; optional recipe checks pass if used
- [x] `.env`, tokens, generated traces with sensitive data, and account secrets are excluded
- [x] Sample data, session-only state, and unimplemented integrations are clearly labeled

## Two-minute demo video

- [ ] Show the surface and existing context before the prompt
- [ ] Demonstrate one complete interaction
- [ ] Show a visible result: an actual record, local state change, or research source links
- [ ] If showing an approval, distinguish the decision from execution and demonstrate the resulting behavior
- [ ] State which sponsor technologies made the interaction possible
- [ ] Keep the video within the event's limit and check audio

See [demo prompts](dev-docs/demo-prompts.md) for a reproducible incident workflow.

## Social post and final submission

- [ ] Follow the organizer's posting and sponsor-tagging instructions
- [ ] Link the public repository and video
- [ ] Credit the sponsors you used and applicable local partners
- [ ] Check the live integration once more before recording or submitting
- [ ] Inspect the repository, video and screenshots for secrets

Prepare the post and submission for a human to publish; running the starter kit
does not publish either automatically.

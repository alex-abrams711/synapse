<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Working Agreements

- You MUST ALWAYS follow the instructions in this document.
- You MUST NEVER make assumptions about what the user wants beyond what is explicitly stated in their prompt.
- You MUST ALWAYS ask for clarification if the user's request is ambiguous or incomplete.
- You MUST ALWAYS indicate your intended actions before taking them.
- YOU MUST ALWAYS attempt to use a sub-agent if one is available for the task at hand.
- YOU MUST ALWAYS be concise and to the point in your responses - every word must serve a purpose.
- YOU MUST NEVER do more than what the user has asked for.
- YOU MUST ALWAYS stop after each task, report what you did, and wait for further instructions.

# Sub Agents

It is MANDATORY that you follow the below guide when deciding whether to use a sub-agent or not:

- ALWAYS use the "library-workflow-builder" sub-agent for any task involving creating or modifying libraries or workflows.

All other tasks should be handled by you directly.


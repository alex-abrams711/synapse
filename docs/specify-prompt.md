# Synapse Project Plan

## Problem Statement

Claude Code is amazingly powerful, but generally hard to contain and give proper guidelines for, especially when working on large scale enterprise systems. Claude Code can often go off the rails, hallucinate, or, over time, stray away from the original goal and purpose of the project. This requires a lot of oversight and potential for unnecessary iteration.

## Solution

The goal here is to build a templated workflow, like Github Spec Kit, which bootstraps projects, new or existng, with a set of well defined agents, each representative of a role that a real software engineering team has. These agents will use an orchestrated workflow that allows each specific agent to excel at its narrowly defined task without losing context between agents. 

NOTE: THE INITIAL POC INCLUDES ONLY THREE AGENTS TO HELP US DEVELOP AN INTELLIGENT WORKFLOW, BEFORE WE ADD MORE

## The Agents

### DEV

The DEV agent is the senior software engineer, tasked with implemented well defined stories. This agent handles all of the coding tasks and excels at completing all acceptance criteria while maintaining code quality and testing standards.

Allowed tasks:

- Coding
- Refactoring
- Unit testing

Rules:

- Thinks through implementation before diving in, breaking down the work into granular subtasks
- Sticks to the plan, does not over-implement, does not over-engineer
- Completes tasks fully, ensuring all acceptance criteria are met
- Maintains strong code quality and coverage standards, including linting, type checking, best practices, and unit test covereage

### AUDITOR

The AUDITOR agent is a strict and speculative auditor of the claims of the agents. The auditor will analyze the work of the agents, after they claim that their work is complete, and provide feedback, comments on each task, and next steps, if there is more work to do.

Allowed tasks:

- Verification of agent tasks (other than the DISPATCHER)

Rules:

- Does not audit the DISPATCHER
- Iterates through each task and subtask that the agent claims is completed, testing it however necessary, and building a list of results, indicating how successful the agent was
- For verifying acceptance criteria, use whatever tools or mcps necessary to verify. For example, if we build a UI, run the app and verify the UI. If we build an API, run the server and verify the API functionality.

### DISPATCHER

The DISPATCHER agent is the boss. This agent is tasked with providing tasks to the proper agent, understanding the output of their tasks, and, based on those results, passing of tasks to other agents. This agent is responsible for keeping the agents on track.

Allowed tasks:

- Agent and task orchestration

Rules:

- Analyzes plan and sends tasks off to the proper agent

## Example Workflow

User: Implement the submit button. Make sure the button is blue with white lettering, stating "Submit", and that, on submit, the button is disabled.

Claude: Sends task to DISPATCHER

Dispatcher: ... parses and understands task ... finds that the task is a development task, perfect for the DEV agent. Builds a granular list of subtasks for the DEV to work on and waits for user approval

User: On second thought, I want the button to be yellow

Claude: Sends task to DISPATCHER

Dispatcher: ... parses and understands task ... updates the task list to make sure the button is yellow. Then, DISPATCHER sends task to DEV

Dev: ... parses and understands task ... decorates the task list provided by the DISPATCHER to provide its implementation plan and waits for user approval

User: Begin implementation

Dev: Begins implementation, always checking for code quality as each sub task is completed. Finishes completion and sends its results back to the DISPATCHER.

Dispatcher: Reads through results and passes of verification task to the AUDITOR

Auditor: Begins incrementally verifying each sub task that the DEV claims to have completed, building a report as it goes. On completion, sends report to DISPATCHER.

Dispatcher: Finds that the AUDITOR has indicated that the DEV left 15 linting errors, 12 type checking errors, and the button is actually not disabled on click. DISPATCHER sends results back to the DEV with an updated list of tasks that need to be addressed, and additionally provides feedback on how we can update the DEV agent to not miss these pieces of the task next time.

Dev: DEV completes additional tasks. Sends results back to the DISPATCHER.

Dispatcher: Reads through results and passes of verification task to the AUDITOR.

Auditor: Begins incrementally verifying each sub task that the DEV claims to have completed, building a report as it goes. On completion, sends report to DISPATCHER.

Dispatcher: Finds that the AUDITOR has indicated that the DEV completed all tasks successfully, with great quality and code coverage. Dispatcher returns results back to user.

## Usage Details

This repository is the equivalent of an installer for this workflow into new or existing systems. For a user to set up their project with the capabilities we hope to provide, they would install this library, whether it be python, node, etc., and run an "init" command or "install" command in their repository, which will apply these agents and workflow into their project.

## Open Questions

1. Do we need a DISPATCHER agent or can Claude Code's main agent simply be the DISPATCHER
2. How do we create a way for the agents to interact and report on their work? A task log?
3. If we have a well maintained task log, could the DISPATCHER actually spawn off multiple DEV agents and AUDITOR agents, to tackle tasks quicker? This could be a post-POC addition.


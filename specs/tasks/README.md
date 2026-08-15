# Development Tasks

## Purpose

Development tasks track the work needed to build and evolve Pekopeko. They provide a structured way to organize, prioritize, and execute the implementation work.

## Task Lifecycle

Tasks follow this lifecycle:

### backlog/
Tasks that are defined but not currently being implemented. These represent future work that has been identified but is not yet prioritized.

### active/
Tasks currently being implemented. These represent the work that is actively being done.

### completed/
Completed tasks retained for historical traceability. These represent work that has been finished and can be referenced for understanding system evolution.

## Task Structure

Each task should contain:

- **Task ID**: Unique identifier for the task
- **Objective**: What the task aims to accomplish
- **Context**: Background information and rationale
- **Scope**: Boundaries of what is included in the task
- **Requirements**: Specific conditions that must be met
- **Constraints**: Limitations or restrictions
- **Files/modules concerned**: Which parts of the system are affected
- **Dependencies**: What other work must be completed first
- **Acceptance criteria**: How success will be determined
- **Testing requirements**: How the task will be validated
- **Out of scope**: What is explicitly not included
- **Status**: Current state of the task

## Task Characteristics

Tasks should be:
- Small enough to be implemented and verified by an AI coding agent without redesigning the project
- Independent where possible
- Clearly defined with measurable outcomes
- Well-scoped to avoid scope creep
- Prioritized based on impact and dependencies

## Development Approach

When creating tasks:
1. Start with a clear understanding of the problem or feature
2. Define specific, achievable objectives
3. Consider dependencies and constraints
4. Ensure tasks are testable and verifiable
5. Keep tasks focused on a single, well-defined goal

## Note

This directory contains only the task structure specification. Actual implementation tasks will be created as development begins.
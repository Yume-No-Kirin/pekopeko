# Module Architecture

## Conceptual Framework

This document defines the conceptual module architecture for Pekopeko. The architecture supports a modular system that can grow over many years by adding independent capabilities without destabilizing or tightly coupling existing functionality, while maintaining a shared knowledge system underneath.

## What is a Module?

A module in Pekopeko represents a distinct functional area with:
- Clear responsibility and well-defined boundaries
- Ownership of its own domain-specific concepts, workflows, and logic
- Independent testability and maintainability
- Explicit interfaces for interaction with the shared Knowledge Core
- Ability to consume and contribute knowledge through standardized mechanisms

## Module Responsibilities

### What Belongs to a Module

Modules own domain-specific capabilities including:
- Domain-specific concepts (vocabulary, rules, patterns, strategies)
- Domain-specific workflows and processes
- Domain-specific calculations and reasoning strategies
- Domain-specific UI views and interfaces
- Domain-specific validation workflows
- Domain-specific derived information generation
- Domain-specific representations and visualizations

### What Does NOT Belong to a Module

Modules must NOT own:
- Canonical knowledge storage or management (this belongs to the Knowledge Core)
- Validation lifecycle mechanisms (this belongs to the Knowledge Core)
- Provenance tracking (this belongs to the Knowledge Core)
- History preservation (this belongs to the Knowledge Core)
- Relationship management (this belongs to the Knowledge Core)
- Temporal validity handling (this belongs to the Knowledge Core)
- Epistemic status tracking (this belongs to the Knowledge Core)
- Lifecycle status management (this belongs to the Knowledge Core)

## Shared Knowledge Core

The Knowledge Core is responsible for generic knowledge concepts and guarantees including:
- Canonical knowledge storage and management
- Proposal handling and validation lifecycle
- Provenance tracking and auditability
- History preservation and change tracking
- Relationship management and graph structure
- Temporal validity handling
- Epistemic status tracking
- Lifecycle status management
- Derivation tracking and dependency analysis
- Domain/context boundaries enforcement
- Auditability and traceability mechanisms

## Module Independence

Modules must maintain strict independence:
- Modules cannot directly manipulate another module's internal state
- Modules cannot directly access another module's private storage
- Modules cannot depend on another module's internal implementation
- Modules cannot silently mutate canonical knowledge
- Modules cannot bypass the human validation mechanism
- Modules cannot silently cross domain boundaries

If a module needs another capability, it must request it through explicit shared capabilities or operations.

## Module Interaction with Knowledge Core

### How Modules Contribute Knowledge

A module may:
- Submit proposals to the Knowledge Core for review and validation
- Create domain-specific knowledge items that enter the proposal lifecycle
- Request analysis from the Knowledge Core
- Request relationships and connections between knowledge elements
- Request temporal reasoning and validity checking
- Request contradiction detection and conflict resolution
- Request change impact analysis
- Provide derived knowledge results that are traceable to supporting inputs

All mutations to canonical knowledge must respect the universal human validation invariant.

### How Modules Consume Knowledge

A module may:
- Query knowledge within its authorized domain/context boundaries
- Receive validated knowledge from the Knowledge Core
- Access relevant relationships and provenance information
- Obtain historical versions of knowledge items
- Get temporal information and validity data
- Receive contradiction information
- Get stale derived knowledge notifications
- Access change impact information

## Module Requesting Reasoning

Modules may request reasoning from the Knowledge Core:
- General reasoning over connected knowledge
- Temporal reasoning across events and time periods
- Relationship analysis between entities
- Contradiction detection and presentation
- Impact analysis of proposed changes
- Dependency tracking for derived knowledge
- Cross-domain reasoning through explicit operations

## Cross-Domain Operations

Cross-domain operations are explicit temporary operations that:
- Are explicitly authorized by the user or system
- Access multiple domains/contexts as needed
- Do not merge domains or silently create cross-domain canonical knowledge
- Maintain clear boundaries between source domains
- Produce results that remain traceable to their inputs
- Require human validation for any resulting canonical knowledge

## Module Capabilities Exposure

Modules expose capabilities through the unified Pekopeko application interface including:
- Screens and dashboards specific to the module's domain
- Workflows and task views
- Actions and operations within the module's scope
- Reports and visualizations
- Analysis tools and insights
- User interface components for knowledge management

## Module Lifecycle

A conceptual lifecycle for modules includes:
- Proposed (conceptual design phase)
- Specified (formal specification completed)
- Implemented (code developed)
- Validated (tested and verified)
- Active (operational in the system)
- Deprecated (no longer recommended for use)
- Removed (completely removed from the system)

Modules should be removable or replaceable without corrupting the shared knowledge model.

## Module Data Ownership

The conceptual distinction between different types of data ownership:

1. **Shared Canonical Knowledge** - Owned by the Knowledge Core, managed through validation lifecycle
2. **Module-Specific Domain Knowledge** - Owned by modules but represented in canonical form
3. **Module-Specific Operational State** - Owned by modules for runtime operations
4. **Derived Results** - Owned by modules but traceable to canonical knowledge
5. **Temporary Task State** - Owned by modules during processing

The conceptual distinction is what matters, not necessarily physical storage separation.

## Module Capability Contract

Every future module should be able to answer:

### Core Questions About Its Role

- **What problem does this module solve?**
  The specific domain or functional area the module addresses

- **Which domain(s) does it operate in?**
  The conceptual domains (PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING) it works within

- **Which contexts/universes does it operate in?**
  The more granular contexts within those domains where it applies

- **Which knowledge concepts does it consume?**
  What canonical knowledge elements it needs to access and use

- **Which knowledge concepts does it produce?**
  What new knowledge items it creates through its operations

- **Which proposals can it create?**
  What types of knowledge items it generates that require human review

- **Which derived knowledge can it create?**
  What analytical results or insights it produces from canonical knowledge

- **Which shared capabilities does it require?**
  What generic services or mechanisms from the Knowledge Core it needs

- **Which domain-specific rules does it own?**
  The specific logic, patterns, and principles unique to its domain

- **Which UI capabilities does it expose?**
  How users interact with its functionality through the unified interface

- **Which cross-domain operations can it participate in?**
  What authorized multi-domain tasks it can engage in

- **What does it explicitly NOT own?**
  What aspects of knowledge management and system operation remain under the Knowledge Core's control

## Module Invariants

Module-specific invariants that complement the existing knowledge invariants:

### MOD-001 — Modules Cannot Bypass Human Validation
Modules must never submit knowledge for canonical status without going through the human validation process, regardless of their own internal logic or data sources.

### MOD-002 — Modules Cannot Silently Cross Domain Boundaries
Modules cannot silently access or merge information across domain boundaries without explicit authorization and operation.

### MOD-003 — Modules Do Not Own the Shared Knowledge Model
Modules must consume and contribute to the shared knowledge model rather than owning isolated versions of it.

### MOD-004 — Modules Must Preserve Provenance
All knowledge contributions from modules must maintain clear provenance that can be traced back to their source and processing steps.

### MOD-005 — Modules Must Preserve Distinction Between Direct and Derived Knowledge
Modules must maintain clear separation between directly sourced information and derived insights in their knowledge representations.

### MOD-006 — Modules Must Not Depend on Another Module's Internal Implementation
Module interfaces must be explicit and well-defined, with modules interacting through shared conceptual knowledge rather than direct dependencies.

### MOD-007 — Module Removal Must Not Corrupt Unrelated Knowledge
Removing a module from the system should not affect the integrity or availability of canonical knowledge in other domains.

### MOD-008 — Module-Specific Logic Must Remain Within the Module Boundary
Domain-specific logic and rules must remain encapsulated within the module boundaries and not leak into shared core functionality.

### MOD-009 — Cross-Domain Operations Must Be Explicit
Cross-domain reasoning or analysis must be explicitly authorized operations rather than automatic behavior.

### MOD-010 — Module Results Must Remain Traceable
All results produced by modules must be traceable back to their supporting knowledge inputs and processing steps.

## Open Questions

1. Which capabilities belong directly to the Knowledge Core versus a shared platform layer?
2. Whether some future modules should be optional plugins that can be enabled/disabled.
3. How module-specific permissions should work for different user roles or access levels.
4. How module-specific representations should be synchronized with the unified GUI.
5. Whether some derived computations should be cached or regenerated based on changes to source knowledge.
6. What mechanisms should govern when a module's domain-specific logic needs to be updated or modified.
7. How the system should handle scenarios where multiple modules need to coordinate on a single cross-domain operation.

These questions represent genuinely unresolved conceptual decisions that will require later discussion and decision-making processes.

## Quality Assurance

This module architecture:
- Does not violate knowledge-invariants.md
- Maintains the Knowledge Core as a non-god module
- Ensures strict module independence
- Preserves explicit cross-domain operations
- Maintains universal human validation
- Treats Obsidian as a representation, not canonical model
- Makes no database or framework decisions
- Does not imply monolithic architecture for the unified GUI
- Contains no application code
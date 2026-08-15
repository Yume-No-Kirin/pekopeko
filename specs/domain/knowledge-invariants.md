# Knowledge Invariants

## Overview

This document contains the core invariants that define the fundamental constraints and principles of Pekopeko's conceptual knowledge model. These invariants are higher-level constraints than implementation choices and must be preserved throughout all system design and development.

## Invariants

### INV-001 — Universal Human Validation
No information or interpretation enters canonical knowledge without passing through the review mechanism. All proposed knowledge items must undergo human validation before becoming part of the persistent knowledge base, regardless of their source or origin.

### INV-002 — AI Inference Is Not Sourced Fact
AI inference, extraction, and interpretation must remain distinguishable from directly sourced information. The system must preserve clear semantic distinctions between what a source actually states and what the system infers or derives from it.

### INV-003 — Provenance
Important canonical knowledge must have traceable provenance. Every piece of canonical knowledge must be able to be traced back to its source material, processing steps, validation events, and transformation history.

### INV-004 — History Is Never Silently Destroyed
Changes must preserve an auditable history where appropriate. The system must never silently destroy or overwrite historical information, even when updating or replacing canonical knowledge items.

### INV-005 — Rejected ≠ False ≠ Unknown
These states must remain semantically distinct. Rejection of a proposal does not automatically mean the proposition is false or unknown; it simply means that particular proposal was not accepted into canonical status.

### INV-006 — Contradictions Are Not Automatically Resolved
Conflicting information must remain representable until appropriately resolved by human judgment. The system must preserve contradictory knowledge items and present conflicts for human resolution rather than silently resolving them.

### INV-007 — Temporal Validity
Recording time and claimed validity/effective time must remain distinguishable. The system must track when information was ingested or recorded separately from when it claims to be true or applicable.

### INV-008 — Domain Isolation
Knowledge does not silently cross domain boundaries. Different knowledge domains (PERSONAL, FICTION, LEARNING, RESEARCH) must maintain conceptual isolation by default, with explicit operations required for cross-domain access.

### INV-009 — Explicit Cross-Domain Operations
Cross-domain reasoning must be explicitly authorized as an operation. Any integration or analysis across domains must be a deliberate, authorized process rather than automatic behavior.

### INV-010 — Modules Do Not Own the Core Knowledge Model
Modules consume and contribute to the shared knowledge model rather than owning isolated versions. All modules interact through the established conceptual knowledge model with explicit interfaces.

### INV-011 — Representations Are Not Canonical Truth
Obsidian, GUI interfaces, export files, and other representations must not be treated as the canonical knowledge model itself. Representations are projections of canonical knowledge but do not constitute the knowledge itself.

### INV-012 — Derived Knowledge Is Traceable
Derived knowledge must be traceable to its supporting inputs and sources. Every piece of derived knowledge must maintain clear lineage back to its foundational knowledge items.

### INV-013 — Derived Knowledge Can Become Stale
Changes to supporting knowledge can invalidate the freshness of derived knowledge. The system must track dependencies so that changes to source knowledge can trigger staleness indicators for dependent derived knowledge.

### INV-014 — Uncertainty Remains Explicit
The system must preserve uncertainty rather than silently converting it into certainty. When information has confidence limits or is contested, this uncertainty must be maintained and represented explicitly.

### INV-015 — Human Canonical Authority Is Not Objective Truth
Human validation establishes canonical status, not objective truth. The system must clearly distinguish between what humans have accepted as part of their knowledge base versus what may be objectively true in the real world.

### INV-016 — Source Content and Interpretation Remain Distinguishable
The system must preserve the distinction between what a source actually states and what the system infers or interprets from it. These are semantically different concepts that must remain separately trackable.

### INV-017 — Modules Remain Decoupled
Modules must not require direct dependencies on one another's internal implementations. Module interfaces must be explicit and well-defined, with modules interacting through shared conceptual knowledge rather than shared code or data structures.

### INV-018 — Important Mutations Are Auditable
Important changes must be attributable and traceable. All significant modifications to canonical knowledge must maintain audit trails that show who changed what, when, and why.

### INV-019 — Failures Must Degrade Safely
Failed processing must not silently corrupt canonical knowledge. System failures should result in preserved state rather than loss or corruption of important information.

### INV-020 — Repeated Ingestion Must Be Safe
Repeated processing of the same source must not blindly create duplicated knowledge. The system must detect and handle duplicate ingestion appropriately to avoid redundancy.

### INV-021 — The Knowledge Model Is Technology Independent
The conceptual model must remain valid independently of implementation technologies, database choices, or architectural decisions. All technical implementation choices should be made without violating fundamental conceptual constraints.

## Invariant Priority

These invariants are higher-level constraints than implementation choices. A future technical proposal that violates an invariant must either:

1. Be rejected, or
2. Trigger an explicit architectural/product decision to change the invariant

It must never be violated accidentally as a side effect of implementation convenience.

## Open Questions

1. Should there be additional invariants for handling edge cases such as knowledge that is partially accepted or conditionally valid?
2. How should the system handle situations where domain boundaries are ambiguous or overlapping?
3. What mechanisms are appropriate for ensuring invariants are maintained during system evolution?
4. Are there scenarios where the distinction between "rejected" and "unknown" might need additional nuance?
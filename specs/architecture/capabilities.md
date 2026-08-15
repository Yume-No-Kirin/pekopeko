# Capability Architecture

## Conceptual Framework

This document defines the cross-cutting capabilities that form the conceptual platform underneath Pekopeko's modules. These generic system abilities can be reused by multiple modules while maintaining the shared knowledge foundation.

## Capability vs Module Distinction

A **capability** is a generic system ability that can be reused by multiple modules.
A **module** is a domain-specific product capability.

For example:
- Knowledge Search = cross-cutting capability
- Japanese Learning = module
- Character Arc Analysis = Fiction module capability  
- Calendar Conflict Detection = Personal Planning module capability

The distinction is critical: capabilities provide generic services that support many modules, while modules implement specific domain functionality.

## Major Cross-Cutting Capabilities

### CAP-CORE-001 — Knowledge Management

Defines the generic system for managing knowledge elements including:
- Entities, assertions, events, relationships
- Temporal information and validity
- Domains and contexts/universes
- Canonical state, historical state, derived state
- Provenance tracking
- Storage is conceptual, not physical

### CAP-CORE-002 — Human Review

Supports the universal validation principle with:
- Proposal queue management
- Proposal inspection capabilities
- Source/context visibility
- AI reasoning/explanation presentation
- Editing functionality
- Acceptance/rejection mechanisms
- Bulk selection and actions
- Prioritization and filtering
- Review history tracking
- Applies equally to all knowledge sources

### CAP-CORE-003 — Provenance

Manages the complete history and origin of knowledge items including:
- Source material tracking
- Processing steps documentation
- Validation events recording
- Transformation history preservation
- Potential provenance sources:
  - user input
  - documents, novels, web pages
  - audio/video content
  - research results
  - other knowledge assertions
  - derived analysis

### CAP-CORE-004 — Knowledge History

Supports conceptual history management including:
- Previous states preservation
- Corrections tracking
- Supersession handling
- Invalidation processes
- Temporal evolution monitoring
- Audit trail maintenance
- Example: Character age changing from 24 to 25 or appointment time correction

### CAP-CORE-005 — Relationship Management

Provides conceptual relationship handling between knowledge elements:
- Connects entities, events, assertions, sources, contexts, domains, derived knowledge
- Supports various relationship types and directions
- Enables reasoning across interconnected knowledge
- "Graph" here is a conceptual model, not necessarily a database structure

### CAP-CORE-006 — Temporal Reasoning

Supports temporal concepts including:
- Before, after, during relationships
- Overlaps, starts, ends, recurring patterns
- Validity period tracking
- Supersession at specific points in time
- Examples:
  - Personal: Tokyo trip (Aug 10–26) vs doctor appointment (Aug 12)
  - Fiction: Character is 24 in chapter 3 vs 27 later
  - Japanese: Vocabulary acquisition dates and mastery evolution

### CAP-CORE-007 — Contradiction Detection

Identifies potential contradictions without automatic resolution:
- Logical contradictions
- Temporal incompatibilities  
- Contextual differences
- Apparent contradictions
- Uncertain contradictions
- Produces findings for human review where appropriate

### CAP-CORE-008 — Derived Knowledge Management

Handles creation and traceability of derived knowledge:
- Creation processes
- Traceability to supporting knowledge
- Derivation explanation generation
- Dependency tracking
- Stale detection
- Invalidation/recomputation proposals
- Example: Character profile derived from multiple sources that becomes stale when those change

### CAP-CORE-009 — Domain and Context Isolation

Enforces boundaries between:
- Domain boundaries (PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING)
- Context/universe boundaries within domains
- Authorization for access
- Explicit cross-domain operations
- Prevents accidental contamination between domains

### CAP-CORE-010 — Explicit Cross-Domain Operations

Manages authorized multi-domain access:
- Explicit authorization required
- Access to multiple domains/contexts
- No automatic domain merging
- Results remain traceable to inputs
- Human validation required for canonical integration
- Destination domain/context must be explicit

### CAP-CORE-011 — Knowledge Search and Retrieval

Provides generic search/retrieval capabilities:
- Exact search
- Semantic search
- Relationship-aware retrieval
- Temporal retrieval
- Domain-filtered retrieval
- Provenance-aware retrieval
- Hybrid retrieval approaches
- Returns information with sufficient context for reasoning and provenance inspection

### CAP-CORE-012 — Reasoning and Analysis

Supports generic reasoning/analysis operations:
- Synthesis, comparison, inference, summarization
- Impact analysis, consistency analysis, pattern detection
- Explanation generation
- Distinguishes reasoning from canonical knowledge mutation
- Results do not automatically become canonical knowledge

### CAP-CORE-013 — Task / Workflow Management

Handles long-running or multi-step tasks:
- Inputs, steps, intermediate results, status, errors, retries, outputs, provenance
- Examples: ingest novel, analyze manuscript, research market, process YouTube video
- May contain multiple capability operations
- Status tracking and error handling

### CAP-CORE-014 — Source and Ingestion Management

Manages knowledge ingestion from various sources:
- Plain text, Markdown, PDF, images, audio, video, web pages, social media
- Distinguishes source acquisition from interpretation from knowledge proposal
- Supports multiple input types conceptually
- Prevents accidental contamination between domains

### CAP-CORE-015 — Auditability

Enables answering questions about knowledge changes:
- What changed?
- When?
- Why?
- Based on what?
- Proposed by whom/what?
- Validated by whom?
- What knowledge depends on it?
- Does not define authentication/identity systems yet

### CAP-CORE-016 — Knowledge Health / Integrity Monitoring

Identifies potential knowledge problems:
- Stale derived knowledge
- Unresolved contradictions
- Orphaned relationships
- Missing provenance
- Ambiguous entities
- Conflicting temporal information
- Invalidated dependencies
- Duplicate ingestion
- Unresolved review proposals
- Surfaces problems without silent fixing

## Capability Composition

Capabilities can be composed to perform complex operations:
- "Analyze scheduling conflict" could compose: Knowledge Retrieval + Temporal Reasoning + Relationship Management + Contradiction Detection + Reasoning + Human Review
- "Complete character profile" could compose: Source Retrieval + Knowledge Retrieval + Relationship Traversal + Temporal Reasoning + Derived Knowledge + Reasoning

Composition remains conceptually separate from implementation.

## Capability Dependency Map

```
                 Knowledge Management
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
      Provenance      History      Relationships
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  Search / Retrieval
                         ↓
                    Reasoning
                         ↓
                 Derived Knowledge
                         │
                         ↓
                  Human Review

And independently:

Domains / Contexts
        ↓
Cross-Domain Operations

Tasks / Workflows
        ↓
compose multiple capabilities
```

## Capability Invariants

Additional invariants for shared capabilities:

### CAP-INV-001 — Shared capabilities must respect knowledge invariants
All capabilities must preserve the fundamental knowledge invariants.

### CAP-INV-002 — Shared capabilities must not silently mutate canonical knowledge
Only through explicit human validation can knowledge become canonical.

### CAP-INV-003 — Reasoning results remain distinguishable from canonical knowledge
Analysis results are separate from validated facts.

### CAP-INV-004 — Retrieval must preserve domain/context boundaries
Search operations respect conceptual boundaries.

### CAP-INV-005 — Provenance must survive capability composition
Traceability is maintained through complex operations.

### CAP-INV-006 — Failures must not create false canonical knowledge
System failures should not corrupt the canonical knowledge base.

### CAP-INV-007 — Long-running tasks must preserve intermediate state and provenance where relevant
Complex operations maintain traceability throughout their execution.

### CAP-INV-008 — Cross-domain operations must remain explicit
Multi-domain access requires authorization.

### CAP-INV-009 — Derived knowledge must remain traceable
All derived results can be traced back to their inputs.

### CAP-INV-010 — Capability composition must not create hidden module coupling
Composition should not introduce dependencies between modules.

## Capability vs Agent

Explicitly distinguish:
**Capability ≠ Agent**

An agent may orchestrate one or more capabilities.
A capability may be used without an autonomous agent.

The product architecture is capability-oriented, with agents being one possible execution mechanism.

## Capability vs Storage

Explicitly distinguish:
**Capability ≠ Storage mechanism**

Knowledge Management does not imply PostgreSQL.
Relationship Management does not imply Neo4j.
Semantic Search does not imply Qdrant.

The same conceptual capability may eventually be implemented using multiple technologies.

## Safety and Failure Behavior

Conceptual safety requirements for shared capabilities:
- If extraction fails: source remains preserved, no false canonical knowledge created
- If reasoning is uncertain: uncertainty remains explicit  
- If contradiction detected: contradiction remains visible, no silent resolution
- If ingestion repeated: duplicate creation prevented or surfaced
- If derived knowledge becomes stale: stale state visible, automatic destructive replacement avoided

## Open Questions

1. Which capabilities belong in the initial V1?
2. Which capabilities should be available to all modules?
3. Which capabilities require explicit permissions?
4. Which operations should eventually support automation?
5. Which derived results should be persisted?
6. What constitutes "important" knowledge for auditability?
7. How should expensive reasoning tasks be prioritized?

These questions represent genuinely unresolved conceptual decisions that will require later discussion and decision-making processes.

## Quality Assurance

This capability architecture:
- Is internally consistent with all previous specifications
- Makes no technology selections
- Makes no database architecture choices
- Makes no frontend/backend architecture decisions
- Makes no agent architecture decisions
- Maintains clear distinction between capabilities and modules
- Maintains clear distinction between capabilities and storage
- Preserves universal human validation
- Preserves domain isolation
- Preserves explicit cross-domain operations
- Preserves derived knowledge traceability
- Contains no application code
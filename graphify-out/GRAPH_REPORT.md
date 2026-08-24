# Graph Report - pekopeko  (2026-08-24)

## Corpus Check
- 56 files · ~51,179 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 551 nodes · 963 edges · 55 communities (26 shown, 29 thin omitted)
- Extraction: 88% EXTRACTED · 11% INFERRED · 1% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d4160c53`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ExtractionResult
- Knowledge Invariants Document
- ADI-001: Canonical Persistence Model Decision
- Generic Knowledge Core
- Invariance Compliance Principle
- pipeline.py
- What is a Module?
- CAP-003 Knowledge Relationships and Reasoning
- Task Lifecycle Conventions
- Retrieval & Performance Requirements
- Product Boundaries
- OllamaProvider
- Project Overview
- Knowledge Reasoning
- Scalability
- Review Queue UX
- Architecture Overview
- Architectural Pressure Points
- Goal-Driven Execution Principle
- Graphify Usage Rules
- French/English Language Convention
- Roadmap Update Discipline
- Significant Decisions Must Be ADRs
- Simplicity First Principle
- Source of Truth (ROADMAP.md + specs/)
- Surgical Changes Principle
- Think Before Coding Principle
- Ticket Self-Containment Rule
- Domain Isolation Principle
- Historical State Preservation Principle
- Human Validation Enforcement Principle
- No Application Code Principle
- No Premature Technology Selection Principle
- Provenance Tracking Principle
- Provider
- Retrieval
- CAP-CORE-016 Knowledge Health / Integrity Monitoring
- test_extensibility.py
- TASK-001: Data Ingestion Module (V1)
- ingest_source
- TaskState
- TASK-002: Proposal Review Workflow (V1)
- Pekopeko — Questions ouvertes, points à définir, incohérences
- test_pipeline.py
- Implementation Status
- TASK-001 Implementation - Final Compliance Report
- Data Ingestion Module (TASK-001)
- AGENTS.md
- test_import_isolation.py
- SourceReaderRegistry
- .get_reader
- .read
- app/__init__.py
- test_domain_validation_comprehensive
- test_import_isolation

## God Nodes (most connected - your core abstractions)
1. `ingest_source()` - 32 edges
2. `ExtractionResult` - 25 edges
3. `OllamaProvider` - 22 edges
4. `Knowledge Invariants Document` - 22 edges
5. `ExtractedAssertion` - 21 edges
6. `SourceReaderRegistry` - 20 edges
7. `Knowledge Model Document` - 19 edges
8. `Generic Knowledge Core` - 19 edges
9. `CAP-CORE-001 Knowledge Management` - 18 edges
10. `Failure Scenarios` - 18 edges

## Surprising Connections (you probably didn't know these)
- `ADR Format Specification` --semantically_similar_to--> `Structured Verification Report Discipline`  [INFERRED] [semantically similar]
  specs/decisions/README.md → docs/ROADMAP.md
- `Rejection of Git-Based Historization` --semantically_similar_to--> `No Git-Based Historization Rule`  [INFERRED] [semantically similar]
  specs/decisions/ADI-001-canonical-persistence-model.md → CLAUDE.md
- `Technical Requirements Summary (81 Requirements, Corrected)` --conceptually_related_to--> `Roadmap de Reprise`  [AMBIGUOUS]
  specs/architecture/technical-requirements.md → docs/ROADMAP.md
- `Verification Discipline` --semantically_similar_to--> `KC-001 Independent Verification Review`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/ROADMAP.md
- `Verification Discipline` --semantically_similar_to--> `Structured Verification Report Discipline`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/ROADMAP.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Canonical/Derived Storage Split Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_006_persistence_vs_recomputation_decision [INFERRED 0.85]
- **Domain Isolation and Explicit Cross-Domain Operations** — specs_domain_knowledge_invariants_inv_008_domain_isolation, specs_domain_knowledge_invariants_inv_009_explicit_cross_domain_operations, specs_modules_module_architecture_mod_002_modules_cannot_silently_cross_domain_boundaries, specs_domain_knowledge_model_cross_domain_task_operation [INFERRED 0.85]
- **Universal Human Validation Gate** — specs_domain_knowledge_invariants_inv_001_universal_human_validation, specs_modules_module_architecture_mod_001_modules_cannot_bypass_human_validation, specs_product_capabilities_cap_002_human_reviewed_knowledge_ingestion, specs_domain_knowledge_model_validation, specs_product_product_model_human_control [INFERRED 0.85]
- **Obsidian Vault Sync-Conflict Avoidance Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_005_sync_vs_async_decision, specs_decisions_adi_008_llm_provider_architecture_decision [INFERRED 0.85]

## Communities (55 total, 29 thin omitted)

### Community 0 - "ExtractionResult"
Cohesion: 0.12
Nodes (21): ExtractedAssertion, ExtractionResult, Provider, Protocol, Base interfaces for LLM providers used in ingestion., Represents a single extracted assertion from source content., Result of an extraction operation., Interface for LLM providers used in ingestion. (+13 more)

### Community 1 - "Knowledge Invariants Document"
Cohesion: 0.05
Nodes (64): Knowledge Invariants Document, INV-001 Universal Human Validation, INV-002 AI Inference Is Not Sourced Fact, INV-003 Provenance, INV-004 History Is Never Silently Destroyed, INV-005 Rejected ≠ False ≠ Unknown, INV-006 Contradictions Are Not Automatically Resolved, INV-007 Temporal Validity (+56 more)

### Community 2 - "ADI-001: Canonical Persistence Model Decision"
Cohesion: 0.07
Nodes (52): ADR Proposed Is Not Accepted, Read ROADMAP.md First (session start rule), No Git-Based Historization Rule, PROJECT_HANDOFF.md Staleness Warning, Pytest tmp_path Testing Convention, Python Backend Language Convention, Verification Discipline, Cleo (Project Owner) (+44 more)

### Community 3 - "Generic Knowledge Core"
Cohesion: 0.15
Nodes (48): English Learning, Japanese Learning, Module Structure, Personal Brain, Research, Voice, CAP-002 Human-Reviewed Knowledge Ingestion, Agent (+40 more)

### Community 4 - "Invariance Compliance Principle"
Cohesion: 0.08
Nodes (33): CAP-CORE-XXX Traceability Correction (2026-08-23), Gap Consigne (CAP-CORE Traceability, 3 Open Items), CAP-CORE-003 — Complete Provenance Tracking Capability, CAP-CORE-014 — Cross-Domain Authorization Capability, CAP-CORE-006 — Derived Knowledge Tracking Capability, CAP-CORE-005 — Domain Isolation Capability, CAP-CORE-004 — Historical State Preservation Capability, CAP-CORE-002 — Human Validation Capability (+25 more)

### Community 5 - "pipeline.py"
Cohesion: 0.16
Nodes (18): Ingestion module for Pekopeko - data ingestion pipeline., Main ingestion pipeline for processing source files., _generate_proposal_id(), _generate_source_id(), Any, Path, Storage utilities for ingestion pipeline with atomic writes., Write a proposal file atomically. Args: vault_root: Root directory of the vault… (+10 more)

### Community 6 - "What is a Module?"
Cohesion: 0.07
Nodes (31): INV-010 Modules Do Not Own the Core Knowledge Model, INV-017 Modules Remain Decoupled, Cross-Domain Operations, Shared Knowledge Core, MOD-003 Modules Do Not Own the Shared Knowledge Model, MOD-006 Modules Must Not Depend on Another Module's Internal Implementation, MOD-007 Module Removal Must Not Corrupt Unrelated Knowledge, MOD-008 Module-Specific Logic Must Remain Within the Module Boundary (+23 more)

### Community 7 - "CAP-003 Knowledge Relationships and Reasoning"
Cohesion: 0.33
Nodes (6): Relationship, CAP-003 Knowledge Relationships and Reasoning, CAP-CORE-005 Relationship Management, CAP-CORE-012 Reasoning and Analysis, Long-Term Needs, Secondary Needs

### Community 8 - "Task Lifecycle Conventions"
Cohesion: 0.47
Nodes (6): active/, backlog/, completed/, Task Characteristics, Task Lifecycle, Task Structure

### Community 9 - "Retrieval & Performance Requirements"
Cohesion: 0.67
Nodes (3): CAP-CORE-010 — Knowledge Search and Retrieval Capability, Performance Requirement Principle, Retrieval Requirements (RTR-001..003)

### Community 10 - "Product Boundaries"
Cohesion: 0.67
Nodes (3): Core Product Areas, Long-Term Direction, Product Boundaries

### Community 11 - "OllamaProvider"
Cohesion: 0.13
Nodes (16): OllamaProvider, OllamaProviderConfig, Parse assertions from LLM response., Configuration for Ollama provider., Concrete implementation of Provider using Ollama API., Extract assertions from text using Ollama. Args: text: The source text to…, Build the prompt for extraction., Test that all providers properly implement the Provider interface. (+8 more)

### Community 37 - "test_extensibility.py"
Cohesion: 0.13
Nodes (18): Protocol, Base interfaces for source readers used in ingestion., Interface for reading source files., SourceReader, MarkdownReader, Markdown source reader implementation., Concrete implementation of SourceReader for Markdown files., MockTextReader (+10 more)

### Community 38 - "TASK-001: Data Ingestion Module (V1)"
Cohesion: 0.11
Nodes (18): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, File layout (exact contract), Files/modules concerned, Objective, Out of scope (+10 more)

### Community 39 - "ingest_source"
Cohesion: 0.16
Nodes (16): ingest_source(), IngestionResult, process_source(), Path, Represents the result of an ingestion operation., Process a source file (backward compatibility alias). Args: source_path: Path…, Ingest a single source file and extract assertions. Args: vault_root: Root…, Final verification of TASK-001 implementation. This script runs all the… (+8 more)

### Community 40 - "TaskState"
Cohesion: 0.16
Nodes (14): create_task_state(), load_task_state(), Any, Path, Task state management for ingestion pipeline., Create a new task state. Args: source_path: Path to the source file domain:…, Update task state on disk. Args: task_state: TaskState object to save…, Represents the state of an ingestion task. (+6 more)

### Community 41 - "TASK-002: Proposal Review Workflow (V1)"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, File layout (exact contract), Files/modules concerned, Frontmatter added/updated on the Proposal file (accept or reject), Objective (+7 more)

### Community 42 - "Pekopeko — Questions ouvertes, points à définir, incohérences"
Cohesion: 0.13
Nodes (14): 10. Glossaire, 11. ADR — sous-questions différées, 12. Format des ADR, 13. Points de vérification (pour mémoire — pas des questions ouvertes), 1. Vision & portée produit, 2. Besoins utilisateurs, 3. Modèle produit, 4. Capacités produit (CAP-001/002/003) (+6 more)

### Community 43 - "test_pipeline.py"
Cohesion: 0.14
Nodes (13): Unit tests for the ingestion pipeline., Test that pipeline handles provider failures gracefully., Test that file writes are atomic., Test that all assertions have valid epistemic status., Test that invalid domains are rejected., Test IngestionResult class., Test duplicate ingestion detection., test_atomic_writes() (+5 more)

### Community 44 - "Implementation Status"
Cohesion: 0.15
Nodes (12): 1. Epistemic Status Validation ✅, 2. Import Isolation ✅, 3. Atomic Write Operations ✅, 4. Git Usage Elimination ✅, Compliance Status, Core Features Implemented, Domain Support, File Structure (+4 more)

### Community 45 - "TASK-001 Implementation - Final Compliance Report"
Cohesion: 0.15
Nodes (12): 1. Domain Validation Consistency (ADI-004 Compliance), 2. Extensibility Requirements (Criteria 5 & 6), 3. Temporal Fields in Proposals, 4. Git Usage Verification, 5. Import Isolation Testing, 6. Source Format Field, 7. Atomic Write Validation, 8. Comprehensive Acceptance Criteria Testing (+4 more)

### Community 46 - "Data Ingestion Module (TASK-001)"
Cohesion: 0.18
Nodes (10): Acceptance Criteria Met, Compliance, Configuration, Data Ingestion Module (TASK-001), Dependencies, Features Implemented, Module Structure, Pekopeko - Knowledge Core (+2 more)

### Community 47 - "AGENTS.md"
Cohesion: 0.20
Nodes (8): Code and tests, Coding Discipline, First thing, every session, graphify, Language, Source of truth, Windows Encoding Rules, Working conventions

### Community 48 - "test_import_isolation.py"
Cohesion: 0.20
Nodes (9): analyze_pipeline_imports(), Static analysis test to verify pipeline code doesn't directly import LLM SDKs., Verify that no git usage exists in ingestion module., Run comprehensive git verification across all files., Test that provider classes are only imported where they should be., Analyze the pipeline.py file for direct imports of LLM SDKs., test_comprehensive_git_verification(), test_no_git_usage() (+1 more)

### Community 49 - "SourceReaderRegistry"
Cohesion: 0.22
Nodes (7): Registry mapping file extensions to SourceReader implementations., Register a reader for a specific file extension., SourceReaderRegistry, Test that all 9 acceptance criteria are met., test_all_acceptance_criteria(), Test source reader registry functionality., test_source_reader_registry()

### Community 50 - ".get_reader"
Cohesion: 0.33
Nodes (3): Path, Get the reader class for a given file extension., Read content from a file using the appropriate reader.

## Ambiguous Edges - Review These
- `CAP-001 Persistent Knowledge Management` → `CAP-CORE-001 Knowledge Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-002 Human-Reviewed Knowledge Ingestion` → `CAP-CORE-002 Human Review`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-002 Human-Reviewed Knowledge Ingestion` → `CAP-CORE-014 Source and Ingestion Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Module Structure` → `Fiction module`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Module Structure` → `Personal Planning module`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-005 Relationship Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-012 Reasoning and Analysis`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Roadmap de Reprise` → `Technical Requirements Summary (81 Requirements, Corrected)`  [AMBIGUOUS]
  specs/architecture/technical-requirements.md · relation: conceptually_related_to

## Knowledge Gaps
- **142 isolated node(s):** `First thing, every session`, `Source of truth`, `Working conventions`, `Coding Discipline`, `Code and tests` (+137 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `CAP-001 Persistent Knowledge Management` and `CAP-CORE-001 Knowledge Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-002 Human-Reviewed Knowledge Ingestion` and `CAP-CORE-002 Human Review`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-002 Human-Reviewed Knowledge Ingestion` and `CAP-CORE-014 Source and Ingestion Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Module Structure` and `Fiction module`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Module Structure` and `Personal Planning module`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-003 Knowledge Relationships and Reasoning` and `CAP-CORE-005 Relationship Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-003 Knowledge Relationships and Reasoning` and `CAP-CORE-012 Reasoning and Analysis`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
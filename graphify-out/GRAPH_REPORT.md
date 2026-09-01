# Graph Report - pekopeko  (2026-09-01)

## Corpus Check
- 197 files · ~149,484 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2208 nodes · 3747 edges · 150 communities (117 shown, 33 thin omitted)
- Extraction: 93% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 238 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `eb44cfeb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SourceReaderRegistry
- Knowledge Invariants Document
- ADI-001: Canonical Persistence Model Decision
- Generic Knowledge Core
- Invariance Compliance Principle
- ExtractedAssertion
- What is a Module?
- Design Document Template
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
- ingestion/test_extensibility.py
- 2. Knowledge Core — cycle de vie proposition/canonique (manquant)
- extraction/storage.py
- routes_ingestion.py
- Section Authoring Guidance
- Pekopeko — Questions ouvertes, points à définir, incohérences
- ingest_source
- api/conftest.py
- load_config
- Data Ingestion Module (TASK-001)
- AGENTS.md
- test_import_isolation.py
- make_proposal_file
- review/pipeline.py
- extract_source
- app/__init__.py
- OllamaProvider
- extraction/pipeline.py
- SourceReaderRegistry
- kiro-review
- ExtractedEntity
- review/storage.py
- Design Review Process
- Core Principles
- parse_frontmatter
- Quick Spec Generator
- TASK-001: Data Ingestion Module (V1)
- Pekopeko Knowledge Management System - UX Specification
- TASK-002: Proposal Review Workflow (V1)
- TASK-003: Entity, Event and Relationship Extraction Module (V1)
- kiro-debug
- Kiro Steering Management
- kiro-impl Skill
- Execution Steps
- Discovery Steps
- Execution Steps
- Kiro Custom Steering Creation
- Analysis Framework
- Execution Steps
- kiro-verify-completion
- Architectural Decision Inputs (Section 23)
- Authentication & Authorization Standards
- Module Structure
- KC-001 Canonical Item Storage Ticket
- Technology Stack
- review/test_storage.py
- Discovery
- Execution Protocol
- EARS Format Guidelines
- Steering Principles
- Steering Principles
- Product Definition
- Requirements Generation
- Technical Design Validation
- Implementation Gap Validation
- CAP-CORE-001 — Knowledge Representation Capability
- Deployment Standards
- Security Standards
- Task Implementation Reviewer
- Focused Discovery Steps
- Research & Design Decisions Template
- Database Standards
- 2. Suite re-priorisée (TASK-013 → TASK-037)
- Spec Batch
- Execution Steps
- Requirements Document
- API Standards
- Error Handling Standards
- Project Structure
- AP-004: Historical State Preservation Requirement
- UC-018 Fictional Universe Isolation
- Design Review Gate
- Requirements Review Gate
- Parallel Task Analysis Rules
- Testing Standards
- Spec Initialization
- ingestion/test_pipeline.py
- edit_proposal
- Debug Investigator
- ADI-009: Frontend Framework for the Pekopeko Application Interface
- Design Synthesis
- Task Format Template
- Product Overview
- CAP-CORE-012 — Asynchronous Task Management Capability
- ExtractionResult
- MockTextReader
- extraction/test_import_isolation.py
- Requirements Document
- test_no_git.py
- TASK-004: Local Configuration Mechanism (V1)
- serialization.py
- TASK-005: Entity, Event and Relationship Proposal Review (V1)
- TASK-006: Proposal EDITED Status and History Versioning (V1)
- TASK-007: Backend API Layer for the Knowledge Core (V1)
- ExtractionResult
- TASK-008: React Scaffold, Dashboard and Settings Screens (V1)
- TASK-001a: Enriched Extraction Provenance Metadata (V1)
- TASK-012: Entity, Event and Relationship Review — API Integration and GUI (V1)
- TASK-001b: Task Event Log for Ingestion and Extraction (V1)
- routes_extraction.py
- TASK-009: Ingestion Logs Screen (V1)
- TASK-010: Validation Screen, Assertions Only (V1)
- TASK-007a: Pagination for List Endpoints (V1)
- TASK-011: Proposal Detail Screen, Assertions Only (V1)
- Candidate Capabilities
- routes_review.py
- test_auth.py
- ADI-010: Backend API Layer and Frontend Integration Contract
- test_config_route.py
- test_bind_host.py
- api/test_no_git.py
- config/test_import_isolation.py
- config/_helpers.py

## God Nodes (most connected - your core abstractions)
1. `load_config()` - 61 edges
2. `make_proposal_file()` - 60 edges
3. `ingest_source()` - 50 edges
4. `ExtractionResult` - 47 edges
5. `extract_source()` - 43 edges
6. `parse_frontmatter()` - 41 edges
7. `ExtractionResult` - 38 edges
8. `edit_proposal()` - 35 edges
9. `OllamaProvider` - 30 edges
10. `accept_proposal()` - 29 edges

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
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_extraction.py -> src/app/api/__init__.py`
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_ingestion.py -> src/app/api/__init__.py`
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_review.py -> src/app/api/__init__.py`
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_config.py -> src/app/api/__init__.py`

## Hyperedges (group relationships)
- **Canonical/Derived Storage Split Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_006_persistence_vs_recomputation_decision [INFERRED 0.85]
- **Domain Isolation and Explicit Cross-Domain Operations** — specs_domain_knowledge_invariants_inv_008_domain_isolation, specs_domain_knowledge_invariants_inv_009_explicit_cross_domain_operations, specs_modules_module_architecture_mod_002_modules_cannot_silently_cross_domain_boundaries, specs_domain_knowledge_model_cross_domain_task_operation [INFERRED 0.85]
- **Universal Human Validation Gate** — specs_domain_knowledge_invariants_inv_001_universal_human_validation, specs_modules_module_architecture_mod_001_modules_cannot_bypass_human_validation, specs_product_capabilities_cap_002_human_reviewed_knowledge_ingestion, specs_domain_knowledge_model_validation, specs_product_product_model_human_control [INFERRED 0.85]
- **Obsidian Vault Sync-Conflict Avoidance Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_005_sync_vs_async_decision, specs_decisions_adi_008_llm_provider_architecture_decision [INFERRED 0.85]

## Communities (150 total, 33 thin omitted)

### Community 0 - "SourceReaderRegistry"
Cohesion: 0.09
Nodes (20): Path, Protocol, Base interfaces for source readers used in ingestion., Registry mapping file extensions to SourceReader implementations., Register a reader for a specific file extension., Get the reader class for a given file extension., Read content from a file using the appropriate reader., Interface for reading source files. (+12 more)

### Community 1 - "Knowledge Invariants Document"
Cohesion: 0.10
Nodes (36): Knowledge Invariants Document, INV-002 AI Inference Is Not Sourced Fact, INV-003 Provenance, INV-004 History Is Never Silently Destroyed, INV-005 Rejected ≠ False ≠ Unknown, INV-006 Contradictions Are Not Automatically Resolved, INV-007 Temporal Validity, INV-011 Representations Are Not Canonical Truth (+28 more)

### Community 2 - "ADI-001: Canonical Persistence Model Decision"
Cohesion: 0.24
Nodes (20): ADR Proposed Is Not Accepted, No Git-Based Historization Rule, Cleo (Project Owner), Phase 0: Identifier Cleanup, Phase 1: Architecture Decisions (ADI-001..006), ADI-004 Obsidian Integration (Open Question), ADI-001: Canonical Persistence Model Decision, Rejection of Git-Based Historization (+12 more)

### Community 3 - "Generic Knowledge Core"
Cohesion: 0.25
Nodes (34): CAP-CORE-001 Knowledge Management, CAP-CORE-002 Human Review, CAP-CORE-003 Provenance, CAP-CORE-004 Knowledge History, CAP-CORE-006 Temporal Reasoning, CAP-CORE-007 Contradiction Detection, CAP-CORE-008 Derived Knowledge Management, CAP-CORE-009 Domain and Context Isolation (+26 more)

### Community 4 - "Invariance Compliance Principle"
Cohesion: 0.18
Nodes (13): CAP-CORE-014 — Cross-Domain Authorization Capability, CAP-CORE-005 — Domain Isolation Capability, Security Requirement Principle, CAP-CORE-007 — Temporal Reasoning Capability, CAP-CORE-008 — Uncertainty Preservation Capability, AP-005: Domain Boundary Enforcement Requirement, AP-006: Cross-Domain Authorization Requirement, AP-008: Temporal Reasoning Support Requirement (+5 more)

### Community 5 - "ExtractedAssertion"
Cohesion: 0.12
Nodes (25): ExtractedAssertion, Represents a single extracted assertion from source content., _generate_proposal_id(), Any, Path, Storage utilities for ingestion pipeline with atomic writes., Write a proposal file atomically. Args: vault_root: Root directory of the vault…, Write content to a file atomically. Args: path: Target file path content:… (+17 more)

### Community 6 - "What is a Module?"
Cohesion: 0.12
Nodes (20): INV-010 Modules Do Not Own the Core Knowledge Model, INV-017 Modules Remain Decoupled, Cross-Domain Operations, Shared Knowledge Core, MOD-003 Modules Do Not Own the Shared Knowledge Model, MOD-006 Modules Must Not Depend on Another Module's Internal Implementation, MOD-007 Module Removal Must Not Corrupt Unrelated Knowledge, MOD-008 Module-Specific Logic Must Remain Within the Module Boundary (+12 more)

### Community 7 - "Design Document Template"
Cohesion: 0.05
Nodes (42): Allowed Dependencies, API Contract, Architecture, Architecture Pattern & Boundary Map, Batch / Job Contract, Boundary Commitments, [Component Name], Components and Interfaces (+34 more)

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
Cohesion: 0.09
Nodes (24): OllamaProvider, OllamaProviderConfig, ExtractionResult, Provider, Parse assertions from LLM response., Configuration for Ollama provider., Concrete implementation of Provider using Ollama API., Extract assertions from text using Ollama. Args: text: The source text to… (+16 more)

### Community 37 - "ingestion/test_extensibility.py"
Cohesion: 0.12
Nodes (17): MarkdownReader, Path, SourceReader, Read a markdown file and return its content. Args: path: Path to the markdown…, Concrete implementation of SourceReader for Markdown files., MockTextReader, Path, SourceReader (+9 more)

### Community 38 - "2. Knowledge Core — cycle de vie proposition/canonique (manquant)"
Cohesion: 0.05
Nodes (42): 1. Knowledge Core — déjà ticketé, 2. Knowledge Core — cycle de vie proposition/canonique (manquant), 3. Ingestion & Extraction — extensibilité (manquant), 4. Interface (ADI-009 tranche React, aucun ticket n'existe encore), 5. Modules de domaine (aucun n'existe, seul le Knowledge Core est ticketé), 6. Dette technique assumée, Backlog complet Pekopeko (vue indépendante), TASK-001 — Module d'ingestion de données (Assertions) (+34 more)

### Community 39 - "extraction/storage.py"
Cohesion: 0.11
Nodes (39): Raised when frontmatter is missing/invalid, before any file is written., ValidationError, Any, YAML frontmatter serialization for the extraction pipeline. Write-side only:…, Render frontmatter + body as "---\\n<yaml>---\\n\\n<body>". Uses the same…, serialize_frontmatter(), Entity/Event/Relationship extraction pipeline: SOURCE -> AI EXTRACTION ->…, _base_proposal_frontmatter() (+31 more)

### Community 40 - "routes_ingestion.py"
Cohesion: 0.06
Nodes (53): Fixed domain enum, re-declared for the API layer's own early request-boundary…, get_ingestion(), list_ingestions(), route, Ingestion endpoints (async, ADI-010 SS2): POST starts a background…, start_ingestion(), _state_dir(), _vault_root() (+45 more)

### Community 41 - "Section Authoring Guidance"
Cohesion: 0.06
Nodes (32): 0. Boundary First, 1. Type Safety is Mandatory, 2. Design vs Implementation, 3. Visual Communication, 4. Component Design Rules, 5. Data Modeling Standards, 6. Error Handling Philosophy, 7. Integration Patterns (+24 more)

### Community 42 - "Pekopeko — Questions ouvertes, points à définir, incohérences"
Cohesion: 0.13
Nodes (14): 10. Glossaire, 11. ADR — sous-questions différées, 12. Format des ADR, 13. Points de vérification (pour mémoire — pas des questions ouvertes), 1. Vision & portée produit, 2. Besoins utilisateurs, 3. Modèle produit, 4. Capacités produit (CAP-001/002/003) (+6 more)

### Community 43 - "ingest_source"
Cohesion: 0.14
Nodes (18): ingest_source(), IngestionResult, process_source(), Path, Provider, Main ingestion pipeline for processing source files., Represents the result of an ingestion operation., Process a source file (backward compatibility alias). Args: source_path: Path… (+10 more)

### Community 44 - "api/conftest.py"
Cohesion: 0.06
Nodes (47): create_app(), main(), HTTP/REST API layer for the Knowledge Core (TASK-007, ADI-010): exposes…, ApiSettings, load_settings(), MissingSettingError, Exception, API process startup settings (ADI-010 SS4/SS5): vault_root and the shared API… (+39 more)

### Community 45 - "load_config"
Cohesion: 0.07
Nodes (45): load_config(), fixture, AC12: a companion .env file next to the resolved config.yaml is loaded into…, _restore_real_environ(), test_dotenv_value_applied_as_bounded_override(), test_missing_dotenv_file_is_not_an_error(), test_real_env_var_wins_over_dotenv_value(), AC1: with no config file present and no relevant environment variable set,… (+37 more)

### Community 46 - "Data Ingestion Module (TASK-001)"
Cohesion: 0.18
Nodes (10): Acceptance Criteria Met, Compliance, Configuration, Data Ingestion Module (TASK-001), Dependencies, Features Implemented, Module Structure, Pekopeko - Knowledge Core (+2 more)

### Community 47 - "AGENTS.md"
Cohesion: 0.20
Nodes (8): Code and tests, Coding Discipline, First thing, every session, graphify, Language, Source of truth, Windows Encoding Rules, Working conventions

### Community 48 - "test_import_isolation.py"
Cohesion: 0.20
Nodes (9): analyze_pipeline_imports(), Static analysis test to verify pipeline code doesn't directly import LLM SDKs., Verify that no git usage exists in ingestion module., Run comprehensive git verification across all files., Test that provider classes are only imported where they should be., Analyze the pipeline.py file for direct imports of LLM SDKs., test_comprehensive_git_verification(), test_no_git_usage() (+1 more)

### Community 49 - "make_proposal_file"
Cohesion: 0.13
Nodes (37): accept_proposal(), reject_proposal(), make_proposal_file(), Unit tests for pipeline.accept_proposal (acceptance criteria 1, 3, 4, 5)., test_accept_already_accepted_proposal_raises_and_leaves_files_unchanged(), test_accept_already_edited_then_accepted_proposal_raises_on_second_accept(), test_accept_nonexistent_proposal_raises_proposal_not_found(), test_accept_proposal_after_edit_writes_assertion_from_edited_body_and_fields() (+29 more)

### Community 50 - "review/pipeline.py"
Cohesion: 0.11
Nodes (30): Proposal review workflow: PROPOSAL -> HUMAN REVIEW -> CANONICAL KNOWLEDGE., AcceptResult, EditResult, get_proposal(), list_proposals(), _load_and_validate_common(), _load_and_validate_for_edit(), _load_and_validate_for_review() (+22 more)

### Community 51 - "extract_source"
Cohesion: 0.11
Nodes (30): extract_source(), Path, Provider, Path, Shared test-only helpers for extraction/ tests. Not a fixture factory that…, Parse a '---\\n<yaml>---\\n\\n<body>' file independently of app code., read_frontmatter(), Extensibility tests: second reader (AC5), second provider (AC6). (+22 more)

### Community 53 - "OllamaProvider"
Cohesion: 0.06
Nodes (66): ConfigError, Exception, Typed exceptions for the app/config module., Raised when a config file is malformed or a present value fails schema…, Local device configuration for Pekopeko (ADI-008). Dependency-free with respect…, _apply_env_overrides(), _build_config(), _load_dotenv() (+58 more)

### Community 54 - "extraction/pipeline.py"
Cohesion: 0.09
Nodes (39): Entity/Event/Relationship extraction pipeline orchestration. Implements SOURCE…, append_task_event(), create_task_state(), list_task_states(), load_task_state(), Any, Path, Task state management for the extraction pipeline. Persisted outside the vault,… (+31 more)

### Community 55 - "SourceReaderRegistry"
Cohesion: 0.09
Nodes (19): SourceReaderRegistry, _build_reader_registry(), Path, Protocol, Base interfaces for source readers used in extraction. Independent of…, Interface for reading source files., Registry mapping file extensions to SourceReader implementations., Register a reader for a specific file extension. (+11 more)

### Community 56 - "kiro-review"
Cohesion: 0.08
Nodes (25): 10.5 Boundary Audit, 10. Design Alignment, 11. Test Quality, 12. Error Handling, 1. Regression Safety, 2. No Residual Placeholder Markers, 3. No Hardcoded Secrets, 4. Boundary Respect (+17 more)

### Community 57 - "ExtractedEntity"
Cohesion: 0.30
Nodes (13): ExtractedEntity, ExtractedRelationship, local_id is a transient identifier scoped to a single extraction call, assigned…, FakeProvider, _proposal_frontmatter(), ExtractionResult, Type-specific proposal fields per proposed_item_type (AC1), and relationship…, test_entity_type_field_present() (+5 more)

### Community 58 - "review/storage.py"
Cohesion: 0.11
Nodes (33): archive_proposal_version(), assertion_path(), _generate_assertion_id(), list_proposal_ids(), proposal_edit_lock(), proposal_path(), Any, Path (+25 more)

### Community 59 - "Design Review Process"
Cohesion: 0.08
Nodes (24): 1. Existing Architecture Alignment (Critical), 2. Design Consistency & Standards, 3. Extensibility & Maintainability, 4. Type Safety & Interface Design, Core Review Criteria, Critical Issues (≤3), Design Review Process, Design Review Summary (+16 more)

### Community 60 - "Core Principles"
Cohesion: 0.09
Nodes (22): 1. Natural Language Descriptions, 2. Task Ordering Principle, 3. Task Integration & Progression, 4. Dependency Declaration, 5. Boundary Scope, 6. Flexible Task Sizing, 7.5 Observable Completion, 7. Requirements Mapping (+14 more)

### Community 61 - "parse_frontmatter"
Cohesion: 0.21
Nodes (15): parse_frontmatter(), Any, YAML frontmatter parsing and serialization. Pure string transformation, no…, Split raw markdown file content into (frontmatter, body). Raises…, Inverse of parse_frontmatter. Uses the same yaml.dump kwargs as…, serialize_frontmatter(), Unit tests for review/frontmatter.py parsing and serialization., test_parse_frontmatter_empty_frontmatter_becomes_empty_dict() (+7 more)

### Community 62 - "Quick Spec Generator"
Cohesion: 0.10
Nodes (19): Core Task, CRITICAL: Automatic Mode Execution Rules, Error Handling, Error Scenarios, Execution Steps, Final Completion Summary, Final Sanity Review, Important Constraints (+11 more)

### Community 63 - "TASK-001: Data Ingestion Module (V1)"
Cohesion: 0.11
Nodes (18): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, File layout (exact contract), Files/modules concerned, Objective, Out of scope (+10 more)

### Community 64 - "Pekopeko Knowledge Management System - UX Specification"
Cohesion: 0.11
Nodes (17): Core Workflow, Dashboard (`pekopeko-dashboard.html`), Data Flow, Domain Organization, Epistemic Status, File Structure, Ingestion Logs (`pekopeko-ingestion.html`), Interactive Folder Path Builder (+9 more)

### Community 65 - "TASK-002: Proposal Review Workflow (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, File layout (exact contract), Files/modules concerned, Frontmatter added/updated on the Proposal file (accept or reject), Objective (+8 more)

### Community 66 - "TASK-003: Entity, Event and Relationship Extraction Module (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, File layout (exact contract), Files/modules concerned, Implementation notes, Objective (+8 more)

### Community 67 - "kiro-debug"
Cohesion: 0.12
Nodes (15): 1. Read the Error Carefully, 2. Inspect Local Runtime and Repository State, 3. Search the Web if Available, 4. Classify the Root Cause, 5. Determine the Smallest Safe Next Action, 6. Determine Whether the Task Plan Is Still Valid, Common Rationalizations, Critical Rule (+7 more)

### Community 68 - "Kiro Steering Management"
Cohesion: 0.12
Nodes (15): Bootstrap:, Bootstrap, Bootstrap Flow, Examples, Granularity Principle, Kiro Steering Management, Notes, Output description (+7 more)

### Community 69 - "kiro-impl Skill"
Cohesion: 0.13
Nodes (14): Autonomous Mode (sub-agent dispatch), Critical Constraints, Error Scenarios, Feature Flag Protocol, kiro-impl Skill, Manual Mode (main context), Output Description, Parallel Research (+6 more)

### Community 70 - "Execution Steps"
Cohesion: 0.13
Nodes (14): Critical Constraints, Error Scenarios, Execution Steps, Next Phase: Task Generation, Output Description, Parallel Research (sub-agent dispatch), Safety & Fallback, Step 1: Load Context (+6 more)

### Community 71 - "Discovery Steps"
Cohesion: 0.14
Nodes (13): 1. Requirements Analysis, 2. Existing Implementation Analysis, 3. Technology Research, 4. External Dependencies Investigation, 5. Architecture Pattern & Boundary Analysis, 6. Risk Assessment, Discovery Steps, Full Discovery Process for Technical Design (+5 more)

### Community 72 - "Execution Steps"
Cohesion: 0.14
Nodes (13): Critical Constraints, Error Scenarios, Execution Steps, Implementation Tasks Generator, Next Phase: Implementation, Output Description, Parallel Research, Safety & Fallback (+5 more)

### Community 73 - "Kiro Custom Steering Creation"
Cohesion: 0.14
Nodes (13): Available Templates, Examples, Kiro Custom Steering Creation, Notes, Output description, Parallel Research, Safety & Fallback, Steering Principles (+5 more)

### Community 74 - "Analysis Framework"
Cohesion: 0.14
Nodes (13): 1. Current State Investigation, 2. Requirements Feasibility Analysis, 3. Implementation Approach Options, 4. Out-of-Scope for Gap Analysis, 5. Implementation Complexity & Risk, Analysis Framework, Gap Analysis Process, Objective (+5 more)

### Community 75 - "Execution Steps"
Cohesion: 0.14
Nodes (13): 1. Detect Validation Target, 2. Load Context, 3. Execute Integration Validation, 4. Generate Report, Error Scenarios, Execution Steps, Implementation Integration Validation, Important Constraints (+5 more)

### Community 76 - "kiro-verify-completion"
Cohesion: 0.14
Nodes (13): Claim-Specific Rules, Common Rationalizations, FEATURE_GO, FIX, Gate Function, Inputs, kiro-verify-completion, Output Format (+5 more)

### Community 77 - "Architectural Decision Inputs (Section 23)"
Cohesion: 0.14
Nodes (14): Read ROADMAP.md First (session start rule), PROJECT_HANDOFF.md Staleness Warning, Discipline de Continuite, Roadmap de Reprise, Demarrage de Session Procedure, ADI-001 Canonical Persistence Model (Open Question), ADI-002 Semantic Retrieval System (Open Question), ADI-003 Relationship Model (Open Question) (+6 more)

### Community 78 - "Authentication & Authorization Standards"
Cohesion: 0.14
Nodes (13): API-to-API Auth, Authentication, Authentication & Authorization Standards, Authorization, Checks (where to enforce), Flow (high-level), Method (choose + rationale), Ownership (+5 more)

### Community 79 - "Module Structure"
Cohesion: 0.22
Nodes (10): English Learning, Japanese Learning, Module Structure, Personal Brain, Research, Voice, Agent, Fiction module (+2 more)

### Community 80 - "KC-001 Canonical Item Storage Ticket"
Cohesion: 0.19
Nodes (13): Pytest tmp_path Testing Convention, Python Backend Language Convention, Verification Discipline, KC-001 Canonical Item Storage Ticket, KC-001 Independent Verification Review, KC-002 Proposal Workflow Ticket, Prochaine Action Exacte, Phase 2: First Concrete Tickets (+5 more)

### Community 81 - "Technology Stack"
Cohesion: 0.15
Nodes (12): Architecture, Code Quality, Common Commands, Core Technologies, Development Environment, Development Standards, Key Libraries, Key Technical Decisions (+4 more)

### Community 82 - "review/test_storage.py"
Cohesion: 0.08
Nodes (37): Flask, Flask app factory for the Pekopeko backend API (ADI-010): registers all route…, Config endpoint (sync, read-only, ADI-010 SS4): projects the already-loaded…, DomainMismatchError, InvalidDomainError, InvalidProposalStatusError, ProposalNotFoundError, Exception (+29 more)

### Community 83 - "Discovery"
Cohesion: 0.17
Nodes (11): Critical Constraints, Discovery, Safety & Fallback, Step 1: Lightweight Scan, Step 2: Determine Action Path, Step 3: Deep Context Loading, Step 4: Understand the Idea, Step 5: Propose Approaches (+3 more)

### Community 84 - "Execution Protocol"
Cohesion: 0.17
Nodes (11): Critical Constraints, Execution Protocol, Role, Status Report, Step 1: Load Task-Relevant Context, Step 2: Build Task Brief, Step 3: Implement with TDD, Step 4: Validate (+3 more)

### Community 85 - "EARS Format Guidelines"
Cohesion: 0.17
Nodes (11): 1. Event-Driven Requirements, 2. State-Driven Requirements, 3. Unwanted Behavior Requirements, 4. Optional Feature Requirements, 5. Ubiquitous Requirements, Combined Patterns, EARS Format Guidelines, Overview (+3 more)

### Community 86 - "Steering Principles"
Cohesion: 0.17
Nodes (11): ❌ Avoid, Content Granularity, ✅ Document, Example Comparison, File-Specific Focus, Golden Rule, Notes, Preservation (when updating) (+3 more)

### Community 87 - "Steering Principles"
Cohesion: 0.17
Nodes (11): ❌ Avoid, Content Granularity, ✅ Document, Example Comparison, File-Specific Focus, Golden Rule, Notes, Preservation (when updating) (+3 more)

### Community 88 - "Product Definition"
Cohesion: 0.09
Nodes (25): INV-001 Universal Human Validation, INV-012 Derived Knowledge Is Traceable, MOD-001 Modules Cannot Bypass Human Validation, MOD-010 Module Results Must Remain Traceable, CAP-001 Persistent Knowledge Management, CAP-002 Human-Reviewed Knowledge Ingestion, Ingestion, Memory (+17 more)

### Community 89 - "Requirements Generation"
Cohesion: 0.18
Nodes (10): Error Scenarios, Execution Steps, Important Constraints, Next Phase: Design Generation, Other Constraints, Output Description, Parallel Research (sub-agent dispatch), Requirements Generation (+2 more)

### Community 90 - "Technical Design Validation"
Cohesion: 0.18
Nodes (10): Core Task, Error Scenarios, Execution Steps, Important Constraints, Next Phase: Task Generation, Output Description, Parallel Research, Safety & Fallback (+2 more)

### Community 91 - "Implementation Gap Validation"
Cohesion: 0.18
Nodes (10): Core Task, Error Scenarios, Execution Steps, Implementation Gap Validation, Important Constraints, Next Phase: Design Generation, Output Description, Parallel Research (+2 more)

### Community 92 - "CAP-CORE-001 — Knowledge Representation Capability"
Cohesion: 0.20
Nodes (11): CAP-CORE-XXX Traceability Correction (2026-08-23), Gap Consigne (CAP-CORE Traceability, 3 Open Items), CAP-CORE-006 — Derived Knowledge Tracking Capability, CAP-CORE-001 — Knowledge Representation Capability, CAP-CORE-009 — Relationship Traversal Capability, AP-001: Knowledge Representation Structure Requirement, AP-007: Derived Knowledge Dependency Tracking Requirement, Relationship Modeling Principle (+3 more)

### Community 93 - "Deployment Standards"
Cohesion: 0.18
Nodes (10): CI/CD Flow, Configuration & Secrets, Deployment Standards, Deployment Strategies, Environments, Health & Monitoring, Incident Response & DR, Philosophy (+2 more)

### Community 94 - "Security Standards"
Cohesion: 0.18
Nodes (10): Authentication & Authorization, Headers & Transport, Input & Output, Logging (security-aware), Philosophy, Secrets & Configuration, Security Standards, Sensitive Data (+2 more)

### Community 95 - "Task Implementation Reviewer"
Cohesion: 0.20
Nodes (9): Core Principle, First Action, Judgment Checks (read code, compare to spec), Mechanical Checks (run commands, use results), Review Checklist, Review Verdict, Role, Task Implementation Reviewer (+1 more)

### Community 96 - "Focused Discovery Steps"
Cohesion: 0.20
Nodes (9): 1. Extension Point Analysis, 2. Dependency Check, 3. Quick Technology Verification, 4. Integration Risk Assessment, Focused Discovery Steps, Light Discovery Process for Extensions, Objective, Output Requirements (+1 more)

### Community 97 - "Research & Design Decisions Template"
Cohesion: 0.20
Nodes (9): Architecture Pattern Evaluation, Decision: `<Title>`, Design Decisions, References, Research & Design Decisions Template, Research Log, Risks & Mitigations, Summary (+1 more)

### Community 98 - "Database Standards"
Cohesion: 0.20
Nodes (9): Backup & Recovery, Connection & Transactions, Data Integrity, Database Standards, Migrations, Naming & Types, Philosophy, Query Patterns (+1 more)

### Community 99 - "2. Suite re-priorisée (TASK-013 → TASK-037)"
Cohesion: 0.05
Nodes (36): 0. Déjà écrit ou complété — inchangé, 1. Socle GUI (TASK-007 → TASK-012), 2. Suite re-priorisée (TASK-013 → TASK-037), Backlog complet Pekopeko — v2, priorité GUI (vue indépendante), Table de correspondance (ancien ID `BACKLOG-CLAUDE.md` → nouvel ID), TASK-007 — Couche API backend pour le Knowledge Core, TASK-008 — Scaffold React + écrans Dashboard et Settings, TASK-009 — Écran Logs d'ingestion (+28 more)

### Community 100 - "Spec Batch"
Cohesion: 0.22
Nodes (8): Critical Constraints, Safety & Fallback, Spec Batch, Step 1: Read Roadmap and Validate, Step 2: Build Dependency Waves, Step 3: Execute Waves, Step 4: Cross-Spec Review, Step 5: Finalize

### Community 101 - "Execution Steps"
Cohesion: 0.22
Nodes (8): Error Scenarios, Execution Steps, List All Specs, Safety & Fallback, Specification Status, Step 1: Load Spec Context, Step 2: Analyze Status, Step 3: Generate Report

### Community 102 - "Requirements Document"
Cohesion: 0.22
Nodes (8): Acceptance Criteria, Acceptance Criteria, Boundary Context (Optional), Introduction, Requirement 1: {{REQUIREMENT_AREA_1}}, Requirement 2: {{REQUIREMENT_AREA_2}}, Requirements, Requirements Document

### Community 103 - "API Standards"
Cohesion: 0.22
Nodes (8): API Standards, Authentication, Endpoint Pattern, Pagination/Filtering (if applicable), Philosophy, Request/Response, Status Codes (pattern), Versioning

### Community 104 - "Error Handling Standards"
Cohesion: 0.22
Nodes (8): Classification (decide handling by source), Error Handling Standards, Error Shape (single canonical format), Logging (context over noise), Monitoring & Health, Philosophy, Propagation (where to convert), Retry (only when safe)

### Community 105 - "Project Structure"
Cohesion: 0.22
Nodes (8): Code Organization Principles, Directory Patterns, Import Organization, Naming Conventions, Organization Philosophy, [Pattern Name], [Pattern Name], Project Structure

### Community 106 - "AP-004: Historical State Preservation Requirement"
Cohesion: 0.28
Nodes (9): CAP-CORE-003 — Complete Provenance Tracking Capability, CAP-CORE-004 — Historical State Preservation Capability, CAP-CORE-002 — Human Validation Capability, AP-002: Human Validation Requirement, AP-003: Complete Provenance Tracking Requirement, AP-004: Historical State Preservation Requirement, Auditability Principle, History Requirements (HIR-001..010) (+1 more)

### Community 107 - "UC-018 Fictional Universe Isolation"
Cohesion: 0.18
Nodes (14): INV-008 Domain Isolation, INV-009 Explicit Cross-Domain Operations, Context / Universe, Cross-Domain Task / Operation, Relationship, MOD-002 Modules Cannot Silently Cross Domain Boundaries, MOD-009 Cross-Domain Operations Must Be Explicit, CAP-003 Knowledge Relationships and Reasoning (+6 more)

### Community 108 - "Design Review Gate"
Cohesion: 0.25
Nodes (7): Architecture Readiness Review, Boundary Readiness Review, Design Review Gate, Executability Review, Mechanical Checks, Requirements Coverage Review, Review Loop

### Community 109 - "Requirements Review Gate"
Cohesion: 0.25
Nodes (7): Boundary Continuity, EARS and Testability Review, Mechanical Checks, Requirements Review Gate, Review Loop, Scope and Coverage Review, Structure and Quality Review

### Community 110 - "Parallel Task Analysis Rules"
Cohesion: 0.25
Nodes (7): Grouping & Ordering Guidelines, Marking Convention, Parallel Task Analysis Rules, Purpose, Quality Checklist, Relationship to Task Ordering, When to Consider Tasks Parallel

### Community 111 - "Testing Standards"
Cohesion: 0.25
Nodes (7): Coverage, Mocking & Data, Organization, Philosophy, Structure (AAA), Test Types, Testing Standards

### Community 112 - "Spec Initialization"
Cohesion: 0.29
Nodes (6): Core Task, Execution Steps, Important Constraints, Output Description, Safety & Fallback, Spec Initialization

### Community 113 - "ingestion/test_pipeline.py"
Cohesion: 0.09
Nodes (33): _events_from_last_task_state(), Path, Unit tests for the ingestion pipeline., Test that pipeline handles provider failures gracefully., Test that file writes are atomic., Test that all assertions have valid epistemic status., Test that invalid domains are rejected., Read back a written Proposal file's provenance dict. (+25 more)

### Community 114 - "edit_proposal"
Cohesion: 0.11
Nodes (34): edit_proposal(), proposal_history_dir(), make_entity_proposal_file(), make_event_proposal_file(), make_relationship_proposal_file(), make_source_file(), fixture, Path (+26 more)

### Community 115 - "Debug Investigator"
Cohesion: 0.33
Nodes (5): Critical Rule, Debug Investigator, Method, Output, You Will Receive

### Community 116 - "ADI-009: Frontend Framework for the Pekopeko Application Interface"
Cohesion: 0.33
Nodes (5): ADI-009: Frontend Framework for the Pekopeko Application Interface, Alternatives considered, Consequences, Context, Decision

### Community 117 - "Design Synthesis"
Cohesion: 0.40
Nodes (4): 1. Generalization, 2. Build vs. Adopt, 3. Simplification, Design Synthesis

### Community 118 - "Task Format Template"
Cohesion: 0.40
Nodes (4): Implementation Plan, Major + Sub-task structure, Major task only, Task Format Template

### Community 119 - "Product Overview"
Cohesion: 0.40
Nodes (4): Core Capabilities, Product Overview, Target Use Cases, Value Proposition

### Community 120 - "CAP-CORE-012 — Asynchronous Task Management Capability"
Cohesion: 0.40
Nodes (5): CAP-CORE-012 — Asynchronous Task Management Capability, CAP-CORE-016 — Module Integration Capability, Cross-Module Communication Principle, Module Decoupling Principle, Task Requirements (TKR-001..002)

### Community 121 - "ExtractionResult"
Cohesion: 0.13
Nodes (13): ExtractionResult, FakeExtractionProvider, FakeIngestionProvider, Poll the on-disk TaskState until it leaves pending/running, or timeout. The…, wait_for_terminal_status(), Extraction route tests (AC5): identical shape to test_ingestion_routes.py, kept…, test_get_extraction_wrong_domain_returns_404(), test_list_extractions_scoped_to_domain() (+5 more)

### Community 122 - "MockTextReader"
Cohesion: 0.40
Nodes (4): MockTextReader, Path, SourceReader, A second reader, registered only in this test - no pipeline.py change needed.

### Community 124 - "Requirements Document"
Cohesion: 0.50
Nodes (3): Project Description (Input), Requirements, Requirements Document

### Community 126 - "TASK-004: Local Configuration Mechanism (V1)"
Cohesion: 0.10
Nodes (19): Acceptance criteria, Amendment verification (2026-08-30), Binding context (references, not duplicated here), Code-review triage (2026-08-30), Constraints, Dependencies, .env example (amendment, 2026-08-30), Files/modules concerned (+11 more)

### Community 127 - "serialization.py"
Cohesion: 0.16
Nodes (17): get_config(), route, accept_result_to_dict(), config_to_dict(), extraction_result_to_dict(), ingestion_result_to_dict(), proposal_detail_to_dict(), proposal_summary_to_dict() (+9 more)

### Community 128 - "TASK-005: Entity, Event and Relationship Proposal Review (V1)"
Cohesion: 0.11
Nodes (18): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Endpoint resolution (relationship acceptance only), File layout (exact contract), Files/modules concerned, Frontmatter added/updated on the Proposal file (accept or reject) (+10 more)

### Community 129 - "TASK-006: Proposal EDITED Status and History Versioning (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Editable fields (allow-list, per `proposed_item_type`), Files/modules concerned, History versioning (no new `version` field on the live Proposal), Objective (+8 more)

### Community 130 - "TASK-007: Backend API Layer for the Knowledge Core (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Domain validation, Error mapping (typed exception → HTTP status), Files/modules concerned, Implementation notes (+8 more)

### Community 131 - "ExtractionResult"
Cohesion: 0.18
Nodes (12): Ingestion module for Pekopeko - data ingestion pipeline., ExtractionResult, Provider, Protocol, Base interfaces for LLM providers used in ingestion., Result of an extraction operation., Interface for LLM providers used in ingestion., Concrete implementation of LLM provider using Ollama. (+4 more)

### Community 132 - "TASK-008: React Scaffold, Dashboard and Settings Screens (V1)"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dashboard module cards, Dashboard stats (V1, client-side aggregation — no aggregate endpoint exists), Dependencies, Files/modules concerned, Objective (+7 more)

### Community 133 - "TASK-001a: Enriched Extraction Provenance Metadata (V1)"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Deviation from this ticket, flagged and resolved with Cleo before implementation (2026-08-31), Files/modules concerned, Implementation notes, Objective (+7 more)

### Community 134 - "TASK-012: Entity, Event and Relationship Review — API Integration and GUI (V1)"
Cohesion: 0.13
Nodes (14): Acceptance criteria, Backend, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Frontend, Objective (+6 more)

### Community 135 - "TASK-001b: Task Event Log for Ingestion and Extraction (V1)"
Cohesion: 0.13
Nodes (14): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Implementation notes, Objective, Out of scope (+6 more)

### Community 136 - "routes_extraction.py"
Cohesion: 0.24
Nodes (13): get_extraction(), list_extractions(), route, Extraction endpoints (async, ADI-010 SS2) - identical shape to…, start_extraction(), _state_dir(), _vault_root(), ExtractionError (+5 more)

### Community 137 - "TASK-009: Ingestion Logs Screen (V1)"
Cohesion: 0.14
Nodes (13): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Objective, Out of scope, Pagination strategy (cross-domain, cross-type, server-paginated pages) (+5 more)

### Community 138 - "TASK-010: Validation Screen, Assertions Only (V1)"
Cohesion: 0.14
Nodes (13): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Data-fetch trade-off (N+1, explicitly authorized), Dependencies, Files/modules concerned, Objective, Out of scope (+5 more)

### Community 139 - "TASK-007a: Pagination for List Endpoints (V1)"
Cohesion: 0.15
Nodes (12): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Objective, Out of scope, Requirements (+4 more)

### Community 140 - "TASK-011: Proposal Detail Screen, Assertions Only (V1)"
Cohesion: 0.15
Nodes (12): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Objective, Out of scope, Requirements (+4 more)

### Community 141 - "Candidate Capabilities"
Cohesion: 0.20
Nodes (10): Pekopeko, Pipeline, Candidate Capabilities, Confirmed Goals, Foundation / Discovery Phase, Explicitly Out of Scope for the Foundation Phase, Product Definition Phase, Current Product Direction (+2 more)

### Community 142 - "routes_review.py"
Cohesion: 0.53
Nodes (8): accept(), _check_domain(), get_proposal_detail(), get_proposals(), route, Review endpoints (sync, ADI-010 SS3): thin pass-through to…, reject(), _vault_root()

### Community 143 - "test_auth.py"
Cohesion: 0.33
Nodes (6): parametrize, AC13: a request with a missing or wrong X-API-Key header returns 401 for every…, A bad domain in the URL must not leak a 400 before the 401 auth check., test_missing_api_key_on_invalid_domain_still_401_not_400(), test_missing_api_key_returns_401(), test_wrong_api_key_returns_401()

### Community 144 - "ADI-010: Backend API Layer and Frontend Integration Contract"
Cohesion: 0.33
Nodes (5): ADI-010: Backend API Layer and Frontend Integration Contract, Alternatives considered, Consequences, Context, Decision

## Ambiguous Edges - Review These
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-005 Relationship Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-012 Reasoning and Analysis`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-CORE-001 Knowledge Management` → `CAP-001 Persistent Knowledge Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-CORE-002 Human Review` → `CAP-002 Human-Reviewed Knowledge Ingestion`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Personal Planning module` → `Module Structure`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Roadmap de Reprise` → `Technical Requirements Summary (81 Requirements, Corrected)`  [AMBIGUOUS]
  specs/architecture/technical-requirements.md · relation: conceptually_related_to
- `Module Structure` → `Fiction module`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-002 Human-Reviewed Knowledge Ingestion` → `CAP-CORE-014 Source and Ingestion Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to

## Knowledge Gaps
- **821 isolated node(s):** `When to Use`, `Inputs`, `Outputs`, `1. Read the Error Carefully`, `2. Inspect Local Runtime and Repository State` (+816 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `CAP-003 Knowledge Relationships and Reasoning` and `CAP-CORE-005 Relationship Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-003 Knowledge Relationships and Reasoning` and `CAP-CORE-012 Reasoning and Analysis`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-CORE-001 Knowledge Management` and `CAP-001 Persistent Knowledge Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-CORE-002 Human Review` and `CAP-002 Human-Reviewed Knowledge Ingestion`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Personal Planning module` and `Module Structure`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Roadmap de Reprise` and `Technical Requirements Summary (81 Requirements, Corrected)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Module Structure` and `Fiction module`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
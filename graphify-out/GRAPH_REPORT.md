# Graph Report - pekopeko  (2026-09-05)

## Corpus Check
- 264 files · ~217,369 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2907 nodes · 5207 edges · 191 communities (155 shown, 36 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 367 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5cf17242`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SourceReaderRegistry
- Knowledge Invariants Document
- ADI-001: Canonical Persistence Model Decision
- Generic Knowledge Core
- Invariance Compliance Principle
- ingestion/test_pipeline.py
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
- test_pipeline_accept_entity_event_relationship.py
- 2. Knowledge Core — cycle de vie proposition/canonique (manquant)
- extraction/storage.py
- ingestion/test_task_state.py
- Section Authoring Guidance
- Pekopeko — Questions ouvertes, points à définir, incohérences
- serialization.py
- make_proposal_file
- load_config
- Data Ingestion Module (TASK-001)
- AGENTS.md
- test_import_isolation.py
- make_proposal_file
- TASK-005: Entity, Event and Relationship Proposal Review (V1)
- extract_source
- app/__init__.py
- devDependencies
- extraction/pipeline.py
- SourceReaderRegistry
- kiro-review
- ExtractedRelationship
- review/test_storage.py
- Design Review Process
- Core Principles
- ValidationError
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
- get
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
- Path
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
- review/pipeline.py
- routes_ingestion.py
- TASK-006: Proposal EDITED Status and History Versioning (V1)
- TASK-007: Backend API Layer for the Knowledge Core (V1)
- ExtractedEntity
- TASK-008: React Scaffold, Dashboard and Settings Screens (V1)
- TASK-001a: Enriched Extraction Provenance Metadata (V1)
- TASK-012: Entity, Event and Relationship Review — API Integration and GUI (V1)
- TASK-001b: Task Event Log for Ingestion and Extraction (V1)
- TASK-014: Folder-Path Organization — Backend API + Frontend Builder (Assertions, V1)
- ProposalDetail.jsx
- Dashboard.jsx
- Pekopeko Test Plan (Cahier de Tests)
- FolderPathBuilder
- Candidate Capabilities
- routes_review.py
- test_auth.py
- ADI-010: Backend API Layer and Frontend Integration Contract
- test_config_route.py
- test_bind_host.py
- loader.py
- config/test_import_isolation.py
- config/_helpers.py
- poll_task_until_terminal
- TASK-001d: Duplicate Detection Ignores Partial-Failure Retries (V1)
- TASK-007a: Pagination for List Endpoints (V1)
- app.py
- TASK-009: Ingestion Logs Screen (V1)
- extraction/test_provider_factory.py
- TASK-010: Validation Screen, Assertions Only (V1)
- ingestion/test_provider_factory.py
- test_dotenv.py
- test_loader_env_overrides.py
- acceptance/conftest.py
- test_loader_path_resolution.py
- test_no_git_usage.py
- TASK-013: Proposal Edit Mode — API Endpoint and Frontend (V1)
- IngestionLogs.jsx
- TASK-001e: Extraction-Proposed Folder Path Segments (Assertions)
- TASK-011: Proposal Detail Screen, Assertions Only (V1)
- Validation
- TASK-001c: Fail Loudly on Zero-Output Provider Extraction (Ingestion + Extraction)
- Validation.jsx
- TASK-001f: Automatic Folder-Watch Ingestion Trigger
- ProposalDetail
- ingest_source
- test_duplicate_and_modified_ingestion.py
- ADI-011: Provider Zero-Output Contract
- ADI-012: Folder-Path Organization (amends ADI-004)
- ADI-013: Automatic Folder-Watch Ingestion Trigger
- ADI-014: Mandatory Extraction-Proposed Folder Path (amends ADI-012)
- ADI-015: Path-Segment Nomenclature Enforcement + Cross-Proposal Context (amends ADI-014)
- App.jsx
- TASK-003a: Extraction Proposal `id`/`type` Fields (V1)
- routes_extraction.py
- load_task_state_resilient
- TaskEvent
- test_proposal_id_type_fields.py
- ._parse_extraction_result
- .extract
- ExtractionPipelineResult
- test_from_dict_tolerates_missing_events_key

## God Nodes (most connected - your core abstractions)
1. `ingest_source()` - 76 edges
2. `make_proposal_file()` - 66 edges
3. `load_config()` - 62 edges
4. `extract_source()` - 59 edges
5. `accept_proposal()` - 59 edges
6. `ExtractionResult` - 57 edges
7. `OllamaProvider` - 56 edges
8. `OllamaProvider` - 55 edges
9. `parse_frontmatter()` - 51 edges
10. `ExtractionResult` - 46 edges

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
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_config.py -> src/app/api/__init__.py`
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_ingestion.py -> src/app/api/__init__.py`
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_extraction.py -> src/app/api/__init__.py`
- 3-file cycle: `src/app/api/__init__.py -> src/app/api/app.py -> src/app/api/routes_review.py -> src/app/api/__init__.py`

## Hyperedges (group relationships)
- **Canonical/Derived Storage Split Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_006_persistence_vs_recomputation_decision [INFERRED 0.85]
- **Domain Isolation and Explicit Cross-Domain Operations** — specs_domain_knowledge_invariants_inv_008_domain_isolation, specs_domain_knowledge_invariants_inv_009_explicit_cross_domain_operations, specs_modules_module_architecture_mod_002_modules_cannot_silently_cross_domain_boundaries, specs_domain_knowledge_model_cross_domain_task_operation [INFERRED 0.85]
- **Universal Human Validation Gate** — specs_domain_knowledge_invariants_inv_001_universal_human_validation, specs_modules_module_architecture_mod_001_modules_cannot_bypass_human_validation, specs_product_capabilities_cap_002_human_reviewed_knowledge_ingestion, specs_domain_knowledge_model_validation, specs_product_product_model_human_control [INFERRED 0.85]
- **Obsidian Vault Sync-Conflict Avoidance Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_005_sync_vs_async_decision, specs_decisions_adi_008_llm_provider_architecture_decision [INFERRED 0.85]

## Communities (191 total, 36 thin omitted)

### Community 0 - "SourceReaderRegistry"
Cohesion: 0.05
Nodes (39): Path, Protocol, Base interfaces for source readers used in ingestion., Registry mapping file extensions to SourceReader implementations., Register a reader for a specific file extension., Get the reader class for a given file extension., Read content from a file using the appropriate reader., Interface for reading source files. (+31 more)

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

### Community 5 - "ingestion/test_pipeline.py"
Cohesion: 0.06
Nodes (54): Ingestion module for Pekopeko - data ingestion pipeline., Main ingestion pipeline for processing source files., ExtractedAssertion, Provider, Protocol, Base interfaces for LLM providers used in ingestion., Represents a single extracted assertion from source content., Interface for LLM providers used in ingestion. (+46 more)

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
Nodes (63): OllamaProvider, OllamaProviderConfig, Provider, Configuration for Ollama provider., Concrete implementation of Provider using Ollama API., _normalize_path_string(), OllamaProvider, OllamaProviderConfig (+55 more)

### Community 37 - "test_pipeline_accept_entity_event_relationship.py"
Cohesion: 0.11
Nodes (27): make_entity_proposal_file(), make_event_proposal_file(), make_relationship_proposal_file(), make_source_file(), fixture, Path, Fixture builders for Proposal/Source files matching TASK-001's on-disk contract…, _write_frontmatter_file() (+19 more)

### Community 38 - "2. Knowledge Core — cycle de vie proposition/canonique (manquant)"
Cohesion: 0.05
Nodes (42): 1. Knowledge Core — déjà ticketé, 2. Knowledge Core — cycle de vie proposition/canonique (manquant), 3. Ingestion & Extraction — extensibilité (manquant), 4. Interface (ADI-009 tranche React, aucun ticket n'existe encore), 5. Modules de domaine (aucun n'existe, seul le Knowledge Core est ticketé), 6. Dette technique assumée, Backlog complet Pekopeko (vue indépendante), TASK-001 — Module d'ingestion de données (Assertions) (+34 more)

### Community 39 - "extraction/storage.py"
Cohesion: 0.11
Nodes (38): Raised when frontmatter is missing/invalid, before any file is written., ValidationError, Any, YAML frontmatter serialization for the extraction pipeline. Write-side only:…, Render frontmatter + body as "---\\n<yaml>---\\n\\n<body>". Uses the same…, serialize_frontmatter(), _base_proposal_frontmatter(), _generate_proposal_id() (+30 more)

### Community 40 - "ingestion/test_task_state.py"
Cohesion: 0.17
Nodes (26): append_task_event(), create_task_state(), list_task_states(), load_task_state(), Path, Task state management for ingestion pipeline., Load task state from disk. Args: state_dir: Directory where task state is saved…, Create a new task state. Args: source_path: Path to the source file domain:… (+18 more)

### Community 41 - "Section Authoring Guidance"
Cohesion: 0.06
Nodes (32): 0. Boundary First, 1. Type Safety is Mandatory, 2. Design vs Implementation, 3. Visual Communication, 4. Component Design Rules, 5. Data Modeling Standards, 6. Error Handling Philosophy, 7. Integration Patterns (+24 more)

### Community 42 - "Pekopeko — Questions ouvertes, points à définir, incohérences"
Cohesion: 0.13
Nodes (14): 10. Glossaire, 11. ADR — sous-questions différées, 12. Format des ADR, 13. Points de vérification (pour mémoire — pas des questions ouvertes), 1. Vision & portée produit, 2. Besoins utilisateurs, 3. Modèle produit, 4. Capacités produit (CAP-001/002/003) (+6 more)

### Community 43 - "serialization.py"
Cohesion: 0.15
Nodes (21): get_config(), route, accept_result_to_dict(), config_to_dict(), edit_result_to_dict(), extraction_result_to_dict(), ingestion_result_to_dict(), organization_folders_to_dict() (+13 more)

### Community 44 - "make_proposal_file"
Cohesion: 0.06
Nodes (44): make_proposal_file(), AC16: responses carry a CORS header allowing a different localhost origin to…, test_cors_header_present_on_post(), _assert_envelope(), AC15: every non-2xx response follows {"error": {"type": ..., "message": ...}},…, ExtractionValidationError/ReviewValidationError/ConfigError never propagate…, Any exception type with no registered handler still yields the same JSON…, test_domain_mismatch_maps_to_400() (+36 more)

### Community 45 - "load_config"
Cohesion: 0.11
Nodes (28): load_config(), AC1: with no config file present and no relevant environment variable set,…, test_defaults_when_no_file_and_no_env(), parametrize, AC4: a malformed YAML file, or a present-but-invalid value, raises a typed…, test_empty_yaml_file_is_treated_as_no_overrides(), test_malformed_yaml_raises_config_error(), test_negative_temperature_from_file_raises_config_error() (+20 more)

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
Cohesion: 0.11
Nodes (49): parse_frontmatter(), Split raw markdown file content into (frontmatter, body). Raises…, accept_proposal(), AcceptResult, reject_proposal(), RejectResult, make_proposal_file(), Unit tests for pipeline.accept_proposal (acceptance criteria 1, 3, 4, 5). (+41 more)

### Community 50 - "TASK-005: Entity, Event and Relationship Proposal Review (V1)"
Cohesion: 0.10
Nodes (20): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Endpoint resolution (relationship acceptance only), File layout (exact contract), Files/modules concerned, Frontmatter added/updated on the Proposal file (accept or reject) (+12 more)

### Community 51 - "extract_source"
Cohesion: 0.08
Nodes (43): extract_source(), Path, Provider, Path, Shared test-only helpers for extraction/ tests. Not a fixture factory that…, Parse a '---\\n<yaml>---\\n\\n<body>' file independently of app code., read_frontmatter(), test_second_provider_extensibility() (+35 more)

### Community 53 - "devDependencies"
Cohesion: 0.06
Nodes (34): dependencies, react, react-dom, react-router-dom, devDependencies, jsdom, @testing-library/jest-dom, @testing-library/react (+26 more)

### Community 54 - "extraction/pipeline.py"
Cohesion: 0.09
Nodes (39): Entity/Event/Relationship extraction pipeline orchestration. Implements SOURCE…, append_task_event(), create_task_state(), list_task_states(), load_task_state(), Any, Path, Task state management for the extraction pipeline. Persisted outside the vault,… (+31 more)

### Community 55 - "SourceReaderRegistry"
Cohesion: 0.09
Nodes (20): SourceReaderRegistry, _build_reader_registry(), Path, Protocol, Base interfaces for source readers used in extraction. Independent of…, Interface for reading source files., Registry mapping file extensions to SourceReader implementations., Register a reader for a specific file extension. (+12 more)

### Community 56 - "kiro-review"
Cohesion: 0.08
Nodes (25): 10.5 Boundary Audit, 10. Design Alignment, 11. Test Quality, 12. Error Handling, 1. Regression Safety, 2. No Residual Placeholder Markers, 3. No Hardcoded Secrets, 4. Boundary Respect (+17 more)

### Community 57 - "ExtractedRelationship"
Cohesion: 0.34
Nodes (11): ExtractedRelationship, FakeProvider, _proposal_frontmatter(), ExtractionResult, Type-specific proposal fields per proposed_item_type (AC1), and relationship…, test_entity_type_field_present(), test_event_starts_ends_at_present(), test_relationship_endpoint_referencing_existing_canonical_id_passed_through() (+3 more)

### Community 58 - "review/test_storage.py"
Cohesion: 0.06
Nodes (75): archive_proposal_version(), assertion_path(), entity_path(), event_path(), _generate_assertion_id(), _generate_entity_id(), _generate_event_id(), _generate_relationship_id() (+67 more)

### Community 59 - "Design Review Process"
Cohesion: 0.08
Nodes (24): 1. Existing Architecture Alignment (Critical), 2. Design Consistency & Standards, 3. Extensibility & Maintainability, 4. Type Safety & Interface Design, Core Review Criteria, Critical Issues (≤3), Design Review Process, Design Review Summary (+16 more)

### Community 60 - "Core Principles"
Cohesion: 0.09
Nodes (22): 1. Natural Language Descriptions, 2. Task Ordering Principle, 3. Task Integration & Progression, 4. Dependency Declaration, 5. Boundary Scope, 6. Flexible Task Sizing, 7.5 Observable Completion, 7. Requirements Mapping (+14 more)

### Community 61 - "ValidationError"
Cohesion: 0.17
Nodes (15): Raised for invalid pagination query parameters (limit/offset)., ValidationError, Any, YAML frontmatter parsing and serialization. Pure string transformation, no…, Inverse of parse_frontmatter. Uses the same yaml.dump kwargs as…, serialize_frontmatter(), Unit tests for review/frontmatter.py parsing and serialization., test_parse_frontmatter_empty_frontmatter_becomes_empty_dict() (+7 more)

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

### Community 82 - "get"
Cohesion: 0.16
Nodes (16): ApiError, buildListUrl(), get(), post(), request(), acceptProposal(), editProposal(), getProposal() (+8 more)

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

### Community 113 - "Path"
Cohesion: 0.13
Nodes (20): Path, Test that pipeline handles provider failures gracefully., Read back a written Proposal file's provenance dict., AC1: OllamaProvider populates non-null provider_model/provider_temperature., AC2: one extraction_id per ingest_source call, shared by all its Proposals., Test that pipeline code doesn't directly import LLM SDKs., AC3: extraction_duration_seconds is present, numeric, and > 0., AC4: a Provider that doesn't report model/temperature yields null, no exception. (+12 more)

### Community 114 - "edit_proposal"
Cohesion: 0.18
Nodes (23): edit_proposal(), EditResult, proposal_history_dir(), Unit tests for pipeline.edit_proposal (acceptance criteria 1-7, 11, 12)., test_edit_proposal_archive_write_failure_leaves_live_file_untouched(), test_edit_proposal_archive_write_failure_no_orphaned_history_file(), test_edit_proposal_archive_write_is_atomic_no_partial_file_on_replace_failure(), test_edit_proposal_body_archives_pre_edit_content_and_updates_live_file() (+15 more)

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
Cohesion: 0.07
Nodes (33): ExtractionResult, ExtractionResult, Result of an extraction operation., FakeExtractionProvider, FakeIngestionProvider, Path, Shared test-only helpers for api/ tests. Kept out of conftest.py so test…, Poll the on-disk TaskState until it leaves pending/running, or timeout. The… (+25 more)

### Community 122 - "MockTextReader"
Cohesion: 0.40
Nodes (4): MockTextReader, Path, SourceReader, A second reader, registered only in this test - no pipeline.py change needed.

### Community 124 - "Requirements Document"
Cohesion: 0.50
Nodes (3): Project Description (Input), Requirements, Requirements Document

### Community 126 - "TASK-004: Local Configuration Mechanism (V1)"
Cohesion: 0.10
Nodes (20): Acceptance criteria, Amendment: project-relative default paths (2026-09-03), Amendment verification (2026-08-30), Binding context (references, not duplicated here), Code-review triage (2026-08-30), Constraints, Dependencies, .env example (amendment, 2026-08-30) (+12 more)

### Community 127 - "review/pipeline.py"
Cohesion: 0.07
Nodes (57): DomainMismatchError, InvalidProposalStatusError, ProposalNotFoundError, Exception, Typed exceptions for the proposal review workflow., Raised when frontmatter is missing/invalid, on read or write., Raised when proposal_id does not resolve to a file under <domain>/proposals/., Raised when provenance.source_id does not resolve to a file under… (+49 more)

### Community 128 - "routes_ingestion.py"
Cohesion: 0.17
Nodes (14): Fixed domain enum, re-declared for the API layer's own early request-boundary…, get_ingestion(), list_ingestions(), route, Ingestion endpoints (async, ADI-010 SS2): POST starts a background…, start_ingestion(), _state_dir(), _vault_root() (+6 more)

### Community 129 - "TASK-006: Proposal EDITED Status and History Versioning (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Editable fields (allow-list, per `proposed_item_type`), Files/modules concerned, History versioning (no new `version` field on the live Proposal), Objective (+8 more)

### Community 130 - "TASK-007: Backend API Layer for the Knowledge Core (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Domain validation, Error mapping (typed exception → HTTP status), Files/modules concerned, Implementation notes (+8 more)

### Community 131 - "ExtractedEntity"
Cohesion: 0.07
Nodes (41): Entity/Event/Relationship extraction pipeline: SOURCE -> AI EXTRACTION ->…, ExtractedEntity, ExtractedEvent, Provider, Protocol, Base interfaces for extraction LLM providers (ADI-008). Pipeline code depends…, local_id is a transient identifier scoped to a single extraction call, assigned…, Provider-construction helper: maps a loaded config to a concrete extraction… (+33 more)

### Community 132 - "TASK-008: React Scaffold, Dashboard and Settings Screens (V1)"
Cohesion: 0.11
Nodes (18): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dashboard module cards, Dashboard stats (V1, client-side aggregation — no aggregate endpoint exists), Dependencies, Deviation found and resolved during implementation (2026-09-02), Files/modules concerned (+10 more)

### Community 133 - "TASK-001a: Enriched Extraction Provenance Metadata (V1)"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Deviation from this ticket, flagged and resolved with Cleo before implementation (2026-08-31), Files/modules concerned, Implementation notes, Objective (+7 more)

### Community 134 - "TASK-012: Entity, Event and Relationship Review — API Integration and GUI (V1)"
Cohesion: 0.13
Nodes (14): Acceptance criteria, Backend, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Frontend, Objective (+6 more)

### Community 135 - "TASK-001b: Task Event Log for Ingestion and Extraction (V1)"
Cohesion: 0.13
Nodes (14): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Implementation notes, Objective, Out of scope (+6 more)

### Community 136 - "TASK-014: Folder-Path Organization — Backend API + Frontend Builder (Assertions, V1)"
Cohesion: 0.11
Nodes (18): Acceptance criteria, Amendment (2026-09-05): inline editing in the Validation table, matching the mockup, Amendment (2026-09-05): mockup fidelity fix + drag-to-reorder segments, Backend, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned (+10 more)

### Community 137 - "ProposalDetail.jsx"
Cohesion: 0.15
Nodes (10): EpistemicStatusBadge(), LABELS, BASELINE_FIELDS, OPTIONAL_FIELDS, ProvenanceSection(), RejectReasonModal(), formatTimestamp(), TaskEventLog() (+2 more)

### Community 138 - "Dashboard.jsx"
Cohesion: 0.18
Nodes (9): DOMAINS, ModuleCard(), StatCard(), countRecentlyReviewed(), Dashboard(), loadDashboardStats(), sumTotals(), jsonResponse() (+1 more)

### Community 139 - "Pekopeko Test Plan (Cahier de Tests)"
Cohesion: 0.04
Nodes (45): Findings surfaced while building this suite, How to run, Invariant traceability appendix (`specs/domain/knowledge-invariants.md`), Known pre-existing issue (not introduced by this test suite, verified independently), Pekopeko Test Plan (Cahier de Tests), Scope and update discipline, TC-UC001-01 — Assertion full round trip: source → proposal → accept → canonical, TC-UC001-02 — Entity/Event/Relationship: proposals created, accept fails (documented gap) (+37 more)

### Community 140 - "FolderPathBuilder"
Cohesion: 0.18
Nodes (9): cleanSegmentName(), FolderPathBuilder(), closeAll(), findOverPosition(), handleConfirmCreate(), handleSegmentClick(), handleSegmentPointerMove(), handleSelectOption() (+1 more)

### Community 141 - "Candidate Capabilities"
Cohesion: 0.20
Nodes (10): Pekopeko, Pipeline, Candidate Capabilities, Confirmed Goals, Foundation / Discovery Phase, Explicitly Out of Scope for the Foundation Phase, Product Definition Phase, Current Product Direction (+2 more)

### Community 142 - "routes_review.py"
Cohesion: 0.30
Nodes (13): accept(), _check_domain(), edit(), get_organization_folders(), get_proposal_detail(), get_proposals(), route, Review endpoints (sync, ADI-010 SS3): thin pass-through to… (+5 more)

### Community 143 - "test_auth.py"
Cohesion: 0.33
Nodes (6): parametrize, AC13: a request with a missing or wrong X-API-Key header returns 401 for every…, A bad domain in the URL must not leak a 400 before the 401 auth check., test_missing_api_key_on_invalid_domain_still_401_not_400(), test_missing_api_key_returns_401(), test_wrong_api_key_returns_401()

### Community 144 - "ADI-010: Backend API Layer and Frontend Integration Contract"
Cohesion: 0.33
Nodes (5): ADI-010: Backend API Layer and Frontend Integration Contract, Alternatives considered, Consequences, Context, Decision

### Community 147 - "loader.py"
Cohesion: 0.20
Nodes (21): ConfigError, Exception, Typed exceptions for the app/config module., Raised when a config file is malformed or a present value fails schema…, Local device configuration for Pekopeko (ADI-008). Dependency-free with respect…, _apply_env_overrides(), _build_config(), Loader for the Pekopeko local device configuration (ADI-008). Resolution order:… (+13 more)

### Community 150 - "poll_task_until_terminal"
Cohesion: 0.15
Nodes (16): poll_task_until_terminal(), Real-HTTP polling helper for src/tests/e2e/. Named _e2e_helpers.py rather than…, kind: 'ingestions' or 'extractions'. Polls the real GET endpoint until status…, UC-009 (Cross-Domain Analysis, isolation slice) and UC-018 (Fictional Universe…, test_ingestion_task_is_not_found_under_a_different_domain(), test_proposal_is_not_found_under_a_different_domain(), UC-016 (Duplicate/Repeated Ingestion) - TC-UC016-E2E. Real HTTP against a real…, test_duplicate_ingestion_via_real_server_reaches_skipped_duplicate() (+8 more)

### Community 151 - "TASK-001d: Duplicate Detection Ignores Partial-Failure Retries (V1)"
Cohesion: 0.12
Nodes (16): 1. Backend — duplicate check based on prior success, not file existence, 2. Frontend — keep the most recent task status per source, not the last one iterated, Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Implementation notes (+8 more)

### Community 152 - "TASK-007a: Pagination for List Endpoints (V1)"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Deviation from the ticket's file list, Files/modules concerned, Implementation notes, Objective (+7 more)

### Community 153 - "app.py"
Cohesion: 0.07
Nodes (43): Flask, create_app(), main(), Flask app factory for the Pekopeko backend API (ADI-010): registers all route…, ApiError, Exception, Typed exceptions for the api/ orchestration layer itself (as opposed to errors…, Base class for exceptions raised by the api/ orchestration layer itself. (+35 more)

### Community 154 - "TASK-009: Ingestion Logs Screen (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Deviations from the ticket text (flagged, not silent), Files/modules concerned, Implementation notes, Objective (+8 more)

### Community 155 - "extraction/test_provider_factory.py"
Cohesion: 0.39
Nodes (7): build_configured_provider(), Provider, _config_with(), AC6/AC7/AC11: extraction.providers.factory.build_configured_provider maps a…, test_build_configured_provider_raises_on_unknown_provider(), test_build_configured_provider_returns_ollama_provider(), test_extract_source_signature_is_unchanged()

### Community 156 - "TASK-010: Validation Screen, Assertions Only (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Data-fetch trade-off (N+1, explicitly authorized), Dependencies, Deviations from the ticket text (flagged, not silent), Files/modules concerned, Implementation notes (+8 more)

### Community 157 - "ingestion/test_provider_factory.py"
Cohesion: 0.39
Nodes (8): PekopekoConfig, build_configured_provider(), Provider, _config_with(), AC6/AC7/AC11: ingestion.providers.factory.build_configured_provider maps a…, test_build_configured_provider_raises_on_unknown_provider(), test_build_configured_provider_returns_ollama_provider(), test_ingest_source_signature_is_unchanged()

### Community 158 - "test_dotenv.py"
Cohesion: 0.29
Nodes (6): fixture, AC12: a companion .env file next to the resolved config.yaml is loaded into…, _restore_real_environ(), test_dotenv_value_applied_as_bounded_override(), test_missing_dotenv_file_is_not_an_error(), test_real_env_var_wins_over_dotenv_value()

### Community 159 - "test_loader_env_overrides.py"
Cohesion: 0.48
Nodes (6): AC5: each environment-variable override in the bounded list takes precedence…, test_empty_string_env_var_is_treated_as_unset(), test_provider_env_overrides_take_precedence_over_file(), test_retrieval_env_override_takes_precedence_over_file(), test_task_state_env_override_takes_precedence_over_file(), _write_config()

### Community 160 - "acceptance/conftest.py"
Cohesion: 0.47
Nodes (5): fixture, Shared fixtures for src/tests/acceptance/: tmp_path-rooted vault/state dirs for…, source_file(), state_dir(), vault_root()

### Community 161 - "test_loader_path_resolution.py"
Cohesion: 0.20
Nodes (10): _load_dotenv(), Path, Optional companion .env file, next to the resolved config.yaml, for…, _read_file(), _resolve_path(), AC3: PEKOPEKO_CONFIG_PATH makes load_config() read from that exact path instead…, test_default_path_used_when_no_arg_and_no_env_var(), test_env_config_path_is_used_when_no_explicit_path_given() (+2 more)

### Community 163 - "TASK-013: Proposal Edit Mode — API Endpoint and Frontend (V1)"
Cohesion: 0.12
Nodes (16): Acceptance criteria, Backend, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Frontend, Implementation notes (2026-09-04) (+8 more)

### Community 164 - "IngestionLogs.jsx"
Cohesion: 0.18
Nodes (10): actionLabel(), basename(), ensurePoolDepth(), formatTimestamp(), IngestionLogs(), mergedFromPool(), STATUS_OPTIONS, TaskRow() (+2 more)

### Community 165 - "TASK-001e: Extraction-Proposed Folder Path Segments (Assertions)"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Amendment (2026-09-04, same-day production verification): mandatory path, ADI-014, Amendment 2 (2026-09-04, same day): mandatory nomenclature + cross-proposal context, ADI-015, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Objective (+7 more)

### Community 166 - "TASK-011: Proposal Detail Screen, Assertions Only (V1)"
Cohesion: 0.12
Nodes (15): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Deviations from the ticket text (flagged, not silent), Files/modules concerned, Implementation notes, Objective (+7 more)

### Community 167 - "Validation"
Cohesion: 0.17
Nodes (9): packGroupsIntoPages(), jsonResponse(), makeFetchMock(), Validation(), handleAccept(), handlePathChange(), handleRejectConfirm(), setNotePathSegments() (+1 more)

### Community 168 - "TASK-001c: Fail Loudly on Zero-Output Provider Extraction (Ingestion + Extraction)"
Cohesion: 0.13
Nodes (14): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Implementation notes, Objective, Out of scope (+6 more)

### Community 169 - "Validation.jsx"
Cohesion: 0.21
Nodes (9): listOrganizationFolders(), SourceGroupHeader(), LABELS, TaskStatusBadge(), handleEditToggle(), fetchFolderOptionsByDomain(), filterByPeriod(), PERIOD_OPTIONS (+1 more)

### Community 170 - "TASK-001f: Automatic Folder-Watch Ingestion Trigger"
Cohesion: 0.15
Nodes (12): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Objective, Out of scope, Requirements (+4 more)

### Community 171 - "ProposalDetail"
Cohesion: 0.18
Nodes (6): capitalize(), ProposalDetail(), handleAccept(), handleRejectConfirm(), jsonResponse(), makeFetchMock()

### Community 172 - "ingest_source"
Cohesion: 0.06
Nodes (41): ingest_source(), IngestionResult, process_source(), Path, Provider, Represents the result of an ingestion operation., Process a source file (backward compatibility alias). Args: source_path: Path…, Ingest a single source file and extract assertions. Args: vault_root: Root… (+33 more)

### Community 173 - "test_duplicate_and_modified_ingestion.py"
Cohesion: 0.27
Nodes (9): _proposal_ids_on_disk(), UC-016 (Duplicate/Repeated Ingestion) and UC-003 (Novel Change & Staleness,…, TC-UC016-01 (ingestion): re-ingesting identical content is a no-op beyond the…, TC-UC016-02 (extraction): same guarantee as above, independent pipeline., TC-UC003-01: a modified source is treated as a brand new, independent source…, _source_ids_on_disk(), test_duplicate_extraction_creates_no_new_files_and_skips_provider_call(), test_duplicate_ingestion_creates_no_new_files_and_skips_provider_call() (+1 more)

### Community 174 - "ADI-011: Provider Zero-Output Contract"
Cohesion: 0.33
Nodes (5): ADI-011: Provider Zero-Output Contract, Alternatives considered, Consequences, Context, Decision

### Community 175 - "ADI-012: Folder-Path Organization (amends ADI-004)"
Cohesion: 0.33
Nodes (5): ADI-012: Folder-Path Organization (amends ADI-004), Alternatives considered, Consequences, Context, Decision

### Community 176 - "ADI-013: Automatic Folder-Watch Ingestion Trigger"
Cohesion: 0.33
Nodes (5): ADI-013: Automatic Folder-Watch Ingestion Trigger, Alternatives considered, Consequences, Context, Decision

### Community 177 - "ADI-014: Mandatory Extraction-Proposed Folder Path (amends ADI-012)"
Cohesion: 0.33
Nodes (5): ADI-014: Mandatory Extraction-Proposed Folder Path (amends ADI-012), Alternatives considered, Consequences, Context, Decision

### Community 178 - "ADI-015: Path-Segment Nomenclature Enforcement + Cross-Proposal Context (amends ADI-014)"
Cohesion: 0.33
Nodes (5): ADI-015: Path-Segment Nomenclature Enforcement + Cross-Proposal Context (amends ADI-014), Alternatives considered, Consequences, Context, Decision

### Community 182 - "TASK-003a: Extraction Proposal `id`/`type` Fields (V1)"
Cohesion: 0.13
Nodes (14): Acceptance criteria, Binding context (references, not duplicated here), Constraints, Dependencies, Files/modules concerned, Implementation notes, Objective, Out of scope (+6 more)

### Community 183 - "routes_extraction.py"
Cohesion: 0.23
Nodes (13): get_extraction(), list_extractions(), route, Extraction endpoints (async, ADI-010 SS2) - identical shape to…, start_extraction(), _state_dir(), _vault_root(), ExtractionError (+5 more)

### Community 184 - "load_task_state_resilient"
Cohesion: 0.26
Nodes (9): load_task_state_resilient(), Path, TaskState.save() (ingestion/extraction task_state.py) is not an atomic write -…, _CountingLoader, load_task_state_resilient: TaskState.save() (ingestion/extraction…, Simulates load_task_state: returns None a fixed number of times (as if racing a…, test_gives_up_after_max_attempts_if_still_unparseable(), test_retries_while_file_exists_until_it_parses() (+1 more)

### Community 185 - "TaskEvent"
Cohesion: 0.18
Nodes (6): Any, A single timestamped step recorded during an ingestion task attempt., Convert task state to dictionary., Create task state from dictionary. Tolerates a missing 'events' key (TaskState…, Save task state to disk. Args: state_dir: Directory where task state should be…, TaskEvent

### Community 186 - "test_proposal_id_type_fields.py"
Cohesion: 0.24
Nodes (10): _proposal_frontmatter(), TASK-003a: extraction-produced proposals must carry top-level `id`/`type`…, AC3: review/'s real validation helper, run directly against a proposal this…, AC4: no regression to fields already written before this ticket., test_entity_proposal_has_id_and_type(), test_entity_proposal_passes_reviews_own_required_fields_validation(), test_event_proposal_has_id_and_type(), test_pre_existing_fields_unchanged() (+2 more)

### Community 187 - "._parse_extraction_result"
Cohesion: 0.24
Nodes (4): ExtractionResult, Parse the JSON extraction result from the LLM response., Extract entities, events, and relationships from text using Ollama. Args: text:…, Build the prompt for extraction.

### Community 188 - ".extract"
Cohesion: 0.29
Nodes (4): ExtractionResult, Build the prompt for extraction., Parse assertions from LLM response., Extract assertions from text using Ollama. Args: text: The source text to…

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
- **1013 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+1008 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **36 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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
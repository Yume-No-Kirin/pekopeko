# Graph Report - pekopeko  (2026-08-23)

## Corpus Check
- 31 files · ~39,444 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 349 nodes · 672 edges · 32 communities (11 shown, 21 thin omitted)
- Extraction: 83% EXTRACTED · 15% INFERRED · 1% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.8)
- Token cost: 275,068 input · 0 output

## Community Hubs (Navigation)
- Canonical Storage Implementation
- Session Continuity & ADR Decisions
- Domain Isolation & Traceability Invariants
- KC-001 Ticket & Decision Rationale
- Product Use Cases & Capabilities
- Architecture Capabilities & Principles Catalog
- Product Vision & Scope
- Module System Design
- Task Lifecycle Conventions
- Retrieval & Performance Requirements
- Product Boundaries
- Knowledge Core Package Init
- Project Overview
- Knowledge Reasoning
- Scalability
- Review Queue UX
- Architecture Overview
- Architectural Pressure Points
- Graphify Integration Rule
- Language Convention
- Roadmap Update Discipline
- ADR Requirement Rule
- Source of Truth Rule
- Ticket Self-Containment Rule
- Domain Isolation Principle
- History Preservation Principle
- Human Validation Principle
- No Application-Code Principle
- No Premature Tech Selection
- Provenance Tracking Principle
- Provider Glossary Term
- Retrieval Glossary Term

## God Nodes (most connected - your core abstractions)
1. `KC-001 Canonical Item Storage Primitive` - 32 edges
2. `KC-001 Canonical Item Storage Primitive` - 30 edges
3. `write_canonical_item()` - 23 edges
4. `Knowledge Invariants Document` - 22 edges
5. `Knowledge Model Document` - 19 edges
6. `Generic Knowledge Core` - 19 edges
7. `Failure Scenarios` - 18 edges
8. `CAP-CORE-001 Knowledge Management` - 18 edges
9. `ValidationError` - 16 edges
10. `ADI-001: Canonical Persistence Model Decision` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Verification Discipline` --semantically_similar_to--> `KC-001 Independent Verification Review`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/ROADMAP.md
- `Verification Discipline` --semantically_similar_to--> `Structured Verification Report Discipline`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/ROADMAP.md
- `Rejection of Git-Based Historization` --semantically_similar_to--> `No Git-Based Historization Rule`  [INFERRED] [semantically similar]
  specs/decisions/ADI-001-canonical-persistence-model.md → CLAUDE.md
- `Technical Requirements Summary (81 Requirements, Corrected)` --conceptually_related_to--> `Roadmap de Reprise`  [AMBIGUOUS]
  specs/architecture/technical-requirements.md → docs/ROADMAP.md
- `ADR Format Specification` --semantically_similar_to--> `Structured Verification Report Discipline`  [INFERRED] [semantically similar]
  specs/decisions/README.md → docs/ROADMAP.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Canonical/Derived Storage Split Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_006_persistence_vs_recomputation_decision [INFERRED 0.85]
- **Obsidian Vault Sync-Conflict Avoidance Pattern** — specs_decisions_adi_001_canonical_persistence_model_decision, specs_decisions_adi_002_retrieval_system_decision, specs_decisions_adi_003_relationship_model_decision, specs_decisions_adi_005_sync_vs_async_decision, specs_decisions_adi_008_llm_provider_architecture_decision [INFERRED 0.85]
- **Session Continuity Discipline** — claude_first_thing_every_session, docs_roadmap_overview, specs_decisions_readme_adr_format [INFERRED 0.75]
- **Universal Human Validation Gate** — specs_domain_knowledge_invariants_inv_001_universal_human_validation, specs_modules_module_architecture_mod_001_modules_cannot_bypass_human_validation, specs_product_capabilities_cap_002_human_reviewed_knowledge_ingestion, specs_domain_knowledge_model_validation, specs_product_product_model_human_control [INFERRED 0.85]
- **Provenance and History Preservation** — specs_domain_knowledge_invariants_inv_003_provenance, specs_domain_knowledge_invariants_inv_004_history_is_never_silently_destroyed, specs_domain_knowledge_invariants_inv_012_derived_knowledge_is_traceable, specs_domain_knowledge_model_provenance, specs_tasks_backlog_kc_001_canonical_item_storage_ticket [INFERRED 0.85]
- **Domain Isolation and Explicit Cross-Domain Operations** — specs_domain_knowledge_invariants_inv_008_domain_isolation, specs_domain_knowledge_invariants_inv_009_explicit_cross_domain_operations, specs_modules_module_architecture_mod_002_modules_cannot_silently_cross_domain_boundaries, specs_domain_knowledge_model_domain, specs_domain_knowledge_model_cross_domain_task_operation [INFERRED 0.85]

## Communities (32 total, 21 thin omitted)

### Community 0 - "Canonical Storage Implementation"
Cohesion: 0.07
Nodes (52): Exception, _format_frontmatter(), _parse_frontmatter(), Canonical Item Storage Primitive for Knowledge Core Implements atomic…, Parse markdown content into frontmatter and body. Args: md_content (str): Full…, Format frontmatter dictionary into YAML string. Args: frontmatter (Dict):…, Write or update a canonical knowledge item. When updating an existing item, the…, Read the current ACTIVE version of a canonical knowledge item. Args: vault_root… (+44 more)

### Community 1 - "Session Continuity & ADR Decisions"
Cohesion: 0.07
Nodes (52): ADR Proposed Is Not Accepted, Read ROADMAP.md First (session start rule), No Git-Based Historization Rule, PROJECT_HANDOFF.md Staleness Warning, Pytest tmp_path Testing Convention, Python Backend Language Convention, Verification Discipline, Cleo (Project Owner) (+44 more)

### Community 2 - "Domain Isolation & Traceability Invariants"
Cohesion: 0.09
Nodes (40): Knowledge Invariants Document, INV-002 AI Inference Is Not Sourced Fact, INV-005 Rejected ≠ False ≠ Unknown, INV-006 Contradictions Are Not Automatically Resolved, INV-008 Domain Isolation, INV-009 Explicit Cross-Domain Operations, INV-011 Representations Are Not Canonical Truth, INV-012 Derived Knowledge Is Traceable (+32 more)

### Community 3 - "KC-001 Ticket & Decision Rationale"
Cohesion: 0.12
Nodes (36): AP-001 Structured Knowledge Representation, AP-002 Human Validation, AP-003 Provenance Tracking, AP-004 Historical States Preserved, AP-005 Domain Boundaries Enforced, ADI-001 Canonical Persistence Model, ADI-002 Retrieval Index, ADI-003 Relationship Adjacency / Traversal (+28 more)

### Community 4 - "Product Use Cases & Capabilities"
Cohesion: 0.23
Nodes (36): CAP-003 Knowledge Relationships and Reasoning, CAP-CORE-001 Knowledge Management, CAP-CORE-002 Human Review, CAP-CORE-003 Provenance, CAP-CORE-004 Knowledge History, CAP-CORE-005 Relationship Management, CAP-CORE-006 Temporal Reasoning, CAP-CORE-007 Contradiction Detection (+28 more)

### Community 5 - "Architecture Capabilities & Principles Catalog"
Cohesion: 0.08
Nodes (31): Complete Provenance Tracking Capability, Cross-Domain Authorization Capability, Derived Knowledge Tracking Capability, Domain Isolation Capability, Historical State Preservation Capability, Human Validation Capability, Knowledge Representation Capability, Relationship Traversal Capability (+23 more)

### Community 6 - "Product Vision & Scope"
Cohesion: 0.07
Nodes (31): INV-001 Universal Human Validation, MOD-001 Modules Cannot Bypass Human Validation, CAP-001 Persistent Knowledge Management, CAP-002 Human-Reviewed Knowledge Ingestion, Ingestion, Memory, Pekopeko, Pipeline (+23 more)

### Community 7 - "Module System Design"
Cohesion: 0.08
Nodes (29): INV-010 Modules Do Not Own the Core Knowledge Model, INV-017 Modules Remain Decoupled, Cross-Domain Operations, Shared Knowledge Core, MOD-003 Modules Do Not Own the Shared Knowledge Model, MOD-006 Modules Must Not Depend on Another Module's Internal Implementation, MOD-007 Module Removal Must Not Corrupt Unrelated Knowledge, MOD-008 Module-Specific Logic Must Remain Within the Module Boundary (+21 more)

### Community 8 - "Task Lifecycle Conventions"
Cohesion: 0.47
Nodes (6): active/, backlog/, completed/, Task Characteristics, Task Lifecycle, Task Structure

### Community 9 - "Retrieval & Performance Requirements"
Cohesion: 0.67
Nodes (3): Knowledge Search and Retrieval Capability, Performance Requirement Principle, Retrieval Requirements (RTR-001..003)

### Community 10 - "Product Boundaries"
Cohesion: 0.67
Nodes (3): Core Product Areas, Long-Term Direction, Product Boundaries

## Ambiguous Edges - Review These
- `Roadmap de Reprise` → `Technical Requirements Summary (81 Requirements, Corrected)`  [AMBIGUOUS]
  specs/architecture/technical-requirements.md · relation: conceptually_related_to
- `Module Structure` → `Fiction module`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Module Structure` → `Personal Planning module`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-001 Persistent Knowledge Management` → `CAP-CORE-001 Knowledge Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-002 Human-Reviewed Knowledge Ingestion` → `CAP-CORE-002 Human Review`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-002 Human-Reviewed Knowledge Ingestion` → `CAP-CORE-014 Source and Ingestion Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-005 Relationship Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-012 Reasoning and Analysis`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to

## Knowledge Gaps
- **59 isolated node(s):** `Source of Truth (ROADMAP.md + specs/)`, `Pytest tmp_path Testing Convention`, `French/English Language Convention`, `Graphify Usage Rules`, `Pekopeko Overview` (+54 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Roadmap de Reprise` and `Technical Requirements Summary (81 Requirements, Corrected)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Module Structure` and `Fiction module`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Module Structure` and `Personal Planning module`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-001 Persistent Knowledge Management` and `CAP-CORE-001 Knowledge Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-002 Human-Reviewed Knowledge Ingestion` and `CAP-CORE-002 Human Review`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-002 Human-Reviewed Knowledge Ingestion` and `CAP-CORE-014 Source and Ingestion Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-003 Knowledge Relationships and Reasoning` and `CAP-CORE-005 Relationship Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
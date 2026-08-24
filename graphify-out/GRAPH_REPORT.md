# Graph Report - pekopeko  (2026-08-23)

## Corpus Check
- 6 files · ~38,888 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 340 nodes · 623 edges · 37 communities (11 shown, 26 thin omitted)
- Extraction: 82% EXTRACTED · 17% INFERRED · 1% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Canonical Storage Implementation
- Domain Isolation & Traceability Invariants
- Session Continuity & ADR Decisions
- Product Use Cases & Capabilities
- Architecture Capabilities & Principles Catalog
- Product Vision & Scope
- Module System Design
- Relationship & Reasoning Capabilities
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
- Goal-Driven Execution Principle
- Graphify Integration Rule
- Language Convention
- Roadmap Update Discipline
- ADR Requirement Rule
- Simplicity First Principle
- Source of Truth Rule
- Surgical Changes Principle
- Think Before Coding Principle
- Ticket Self-Containment Rule
- Domain Isolation Principle
- History Preservation Principle
- Human Validation Principle
- No Application-Code Principle
- No Premature Tech Selection
- Provenance Tracking Principle
- Provider Glossary Term
- Retrieval Glossary Term
- Knowledge Health / Integrity Monitoring

## God Nodes (most connected - your core abstractions)
1. `write_canonical_item()` - 23 edges
2. `Knowledge Invariants Document` - 22 edges
3. `Knowledge Model Document` - 19 edges
4. `Generic Knowledge Core` - 19 edges
5. `KC-001 Canonical Item Storage Primitive` - 18 edges
6. `CAP-CORE-001 Knowledge Management` - 18 edges
7. `Failure Scenarios` - 18 edges
8. `ValidationError` - 16 edges
9. `ADI-001: Canonical Persistence Model Decision` - 16 edges
10. `CAP-CORE-003 Provenance` - 16 edges

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

## Communities (37 total, 26 thin omitted)

### Community 0 - "Canonical Storage Implementation"
Cohesion: 0.07
Nodes (52): Exception, _format_frontmatter(), _parse_frontmatter(), Canonical Item Storage Primitive for Knowledge Core Implements atomic…, Parse markdown content into frontmatter and body. Args: md_content (str): Full…, Format frontmatter dictionary into YAML string. Args: frontmatter (Dict):…, Write or update a canonical knowledge item. When updating an existing item, the…, Read the current ACTIVE version of a canonical knowledge item. Args: vault_root… (+44 more)

### Community 1 - "Domain Isolation & Traceability Invariants"
Cohesion: 0.08
Nodes (53): Knowledge Invariants Document, INV-002 AI Inference Is Not Sourced Fact, INV-003 Provenance, INV-004 History Is Never Silently Destroyed, INV-005 Rejected ≠ False ≠ Unknown, INV-006 Contradictions Are Not Automatically Resolved, INV-007 Temporal Validity, INV-008 Domain Isolation (+45 more)

### Community 2 - "Session Continuity & ADR Decisions"
Cohesion: 0.07
Nodes (52): ADR Proposed Is Not Accepted, Read ROADMAP.md First (session start rule), No Git-Based Historization Rule, PROJECT_HANDOFF.md Staleness Warning, Pytest tmp_path Testing Convention, Python Backend Language Convention, Verification Discipline, Cleo (Project Owner) (+44 more)

### Community 3 - "Product Use Cases & Capabilities"
Cohesion: 0.23
Nodes (37): CAP-CORE-001 Knowledge Management, CAP-CORE-002 Human Review, CAP-CORE-003 Provenance, CAP-CORE-004 Knowledge History, CAP-CORE-006 Temporal Reasoning, CAP-CORE-007 Contradiction Detection, CAP-CORE-008 Derived Knowledge Management, CAP-CORE-009 Domain and Context Isolation (+29 more)

### Community 4 - "Architecture Capabilities & Principles Catalog"
Cohesion: 0.08
Nodes (33): CAP-CORE-XXX Traceability Correction (2026-08-23), Gap Consigne (CAP-CORE Traceability, 3 Open Items), CAP-CORE-003 — Complete Provenance Tracking Capability, CAP-CORE-014 — Cross-Domain Authorization Capability, CAP-CORE-006 — Derived Knowledge Tracking Capability, CAP-CORE-005 — Domain Isolation Capability, CAP-CORE-004 — Historical State Preservation Capability, CAP-CORE-002 — Human Validation Capability (+25 more)

### Community 5 - "Product Vision & Scope"
Cohesion: 0.07
Nodes (30): INV-001 Universal Human Validation, MOD-001 Modules Cannot Bypass Human Validation, CAP-001 Persistent Knowledge Management, CAP-002 Human-Reviewed Knowledge Ingestion, Ingestion, Memory, Pekopeko, Pipeline (+22 more)

### Community 6 - "Module System Design"
Cohesion: 0.08
Nodes (30): INV-010 Modules Do Not Own the Core Knowledge Model, INV-017 Modules Remain Decoupled, Cross-Domain Operations, Shared Knowledge Core, MOD-003 Modules Do Not Own the Shared Knowledge Model, MOD-006 Modules Must Not Depend on Another Module's Internal Implementation, MOD-007 Module Removal Must Not Corrupt Unrelated Knowledge, MOD-008 Module-Specific Logic Must Remain Within the Module Boundary (+22 more)

### Community 7 - "Relationship & Reasoning Capabilities"
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

## Ambiguous Edges - Review These
- `CAP-002 Human-Reviewed Knowledge Ingestion` → `CAP-CORE-002 Human Review`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-002 Human-Reviewed Knowledge Ingestion` → `CAP-CORE-014 Source and Ingestion Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-005 Relationship Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-003 Knowledge Relationships and Reasoning` → `CAP-CORE-012 Reasoning and Analysis`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `CAP-001 Persistent Knowledge Management` → `CAP-CORE-001 Knowledge Management`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Module Structure` → `Fiction module`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Module Structure` → `Personal Planning module`  [AMBIGUOUS]
  specs/product/use-cases.md · relation: conceptually_related_to
- `Roadmap de Reprise` → `Technical Requirements Summary (81 Requirements, Corrected)`  [AMBIGUOUS]
  specs/architecture/technical-requirements.md · relation: conceptually_related_to

## Knowledge Gaps
- **65 isolated node(s):** `Cross-Module Communication Principle`, `Derived, Rebuildable Index Concept`, `Atomic Write Mechanism (Temp File + Rename)`, `extract(text, context) -> ExtractionResult Interface`, `Architecture Decision Records Purpose` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `CAP-002 Human-Reviewed Knowledge Ingestion` and `CAP-CORE-002 Human Review`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-002 Human-Reviewed Knowledge Ingestion` and `CAP-CORE-014 Source and Ingestion Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-003 Knowledge Relationships and Reasoning` and `CAP-CORE-005 Relationship Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-003 Knowledge Relationships and Reasoning` and `CAP-CORE-012 Reasoning and Analysis`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `CAP-001 Persistent Knowledge Management` and `CAP-CORE-001 Knowledge Management`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Module Structure` and `Fiction module`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Module Structure` and `Personal Planning module`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
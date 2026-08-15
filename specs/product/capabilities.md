# Product Capabilities

A capability describes something Pekopeko should be able to do from the user's perspective.

## CAP-001 — Persistent Knowledge Management

### Purpose
To provide a reliable, persistent system for storing and organizing personal knowledge that can evolve over time with proper versioning and historical tracking.

### User Value
Users can maintain a comprehensive, organized knowledge base that persists across time and allows them to understand how information evolved, trace its origins, and see the impact of changes.

### User Actions
- Add new pieces of information to their knowledge base
- Review proposed knowledge changes or additions
- Accept, reject, or modify knowledge propositions
- Query and retrieve information across different domains
- View historical versions and changes to important knowledge

### System Behavior
- Store knowledge with provenance tracking
- Maintain version history for important knowledge items
- Track relationships between different pieces of knowledge
- Provide historical change views and impact analysis

### Inputs
- User-provided information
- AI-generated knowledge propositions
- Source materials for knowledge extraction
- Historical knowledge data

### Outputs
- Organized knowledge database
- Versioned knowledge items
- Relationship maps between knowledge elements
- Historical change reports

### Dependencies
- Human validation workflow system
- Knowledge storage and retrieval infrastructure
- Provenance tracking mechanisms

### Constraints
- All canonical knowledge must be human-validated
- System must not automatically treat AI-derived information as canonical truth
- Versioning must preserve historical context

### Acceptance Criteria
- Users can store, retrieve, and track changes to knowledge over time
- System maintains clear provenance for important knowledge items
- Users can understand how knowledge was derived and when it changed

### Out of Scope
- Specific database implementation details
- Final schema design
- Performance optimization for large datasets

### Open Questions
- What level of granularity should be maintained in versioning?
- How should the system handle different types of knowledge relationships?
- What constitutes "important" knowledge that requires special handling?

## CAP-002 — Human-Reviewed Knowledge Ingestion

### Purpose
To enable users to bring information from various sources into the system while ensuring human validation before it becomes canonical knowledge.

### User Value
Users can leverage AI assistance for information ingestion and processing while maintaining complete control over what becomes part of their persistent knowledge base.

### User Actions
- Provide source materials (documents, audio, video, text)
- Review proposed extractions and classifications
- Accept or reject proposed knowledge items
- Correct or modify extracted information
- Batch-process multiple proposals

### System Behavior
- Extract information from various input formats
- Classify and structure extracted information
- Present proposals to users for review
- Store source materials separately from extracted knowledge
- Track provenance of all knowledge items

### Inputs
- Source materials (documents, audio, video, text)
- User preferences for ingestion processing
- Existing knowledge base for relationship mapping

### Outputs
- Structured knowledge propositions
- Extracted information with source attribution
- Classification and categorization results
- Review queue of proposed knowledge items

### Dependencies
- Knowledge storage system
- Review queue mechanism
- Ingestion pipeline infrastructure

### Constraints
- All canonical knowledge must be human-reviewed and accepted
- AI-generated information cannot automatically become canonical
- Source materials must be preserved independently

### Acceptance Criteria
- System can ingest multiple input formats
- Users can review proposed knowledge items efficiently
- Source materials are preserved separately from extracted knowledge
- Human validation is required for all canonical knowledge

### Out of Scope
- Specific ingestion pipeline implementation details
- Final technology choices for processing sources
- UI/UX design for ingestion workflows

### Open Questions
- What input formats should be supported in initial release?
- How should the review queue experience be designed for efficiency?
- What level of automation is appropriate for different types of extraction?

## CAP-003 — Knowledge Relationships and Reasoning

### Purpose
To enable users to understand connections between pieces of knowledge and support reasoning about relationships.

### User Value
Users can identify, explore, and reason about connections between their personal information, leading to better understanding and insights.

### User Actions
- Query relationships between different knowledge items
- Ask questions that require reasoning across related knowledge
- View dependency analysis for important knowledge items
- Identify potential contradictions or conflicts
- Understand impact of changes on related knowledge

### System Behavior
- Maintain relationship mappings between knowledge elements
- Detect and present potential contradictions
- Provide reasoning capabilities over interconnected knowledge
- Show impact analysis when knowledge changes
- Support temporal and semantic reasoning

### Inputs
- Knowledge base content
- User queries about relationships
- Existing relationship data
- Knowledge change events

### Outputs
- Relationship maps and visualizations
- Contradiction detection results
- Impact analysis reports
- Reasoning explanations for connections

### Dependencies
- Persistent knowledge storage
- Provenance tracking system
- Conflict detection mechanisms

### Constraints
- System must distinguish between direct facts and derived inferences
- Reasoning should be explainable and traceable to its source
- Derived information must not become authoritative without human validation

### Acceptance Criteria
- System can identify relationships between knowledge elements
- Users can query and explore knowledge connections
- Potential contradictions are detected and presented for review
- Impact analysis is available for important changes

### Out of Scope
- Specific database schema or graph structure
- Advanced reasoning algorithms implementation details
- Final architectural decisions for relationship storage

### Open Questions
- What types of relationships should be supported initially?
- How should different types of reasoning be prioritized?
- What constitutes a "potential contradiction" that requires user attention?
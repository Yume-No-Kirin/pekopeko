# Pekopeko Product Model

## 1. Product Definition

Pekopeko is a modular personal AI environment centered around a persistent, versioned, human-validated knowledge and memory system. It progressively becomes a personal AI environment in which specialized modules can consume shared knowledge, create new knowledge proposals, reason over existing knowledge, provide specialized functionality, and contribute knowledge back to the shared system.

## 2. Problem Statement

Pekopeko addresses the challenge of managing personal information across multiple domains and contexts while maintaining reliability and user control. It solves problems related to:
- Information fragmentation across different tools and platforms
- Difficulty in organizing and retrieving personal knowledge over time
- The need for reliable systems that don't automatically treat AI-generated information as canonical truth
- Managing complex relationships between different types of knowledge (personal, fictional, learning, research)
- Balancing automation with human control and validation

## 3. Target User

Pekopeko is designed for individuals who want to maintain a persistent, organized, and reliable personal knowledge system that evolves over time. This includes users who:
- Manage complex personal information across multiple domains
- Value reliability and traceability of their knowledge
- Want to leverage AI assistance while maintaining control over important decisions
- Work with multiple types of content (personal events, learning materials, research, fictional works)
- Seek tools that can help reason about relationships between different pieces of information

## 4. Primary User Goals

The user should ultimately be able to accomplish:
- Persistently maintain validated personal knowledge and memory
- Organize and retrieve information across multiple domains reliably
- Leverage AI assistance for analysis while maintaining human control over canonical knowledge
- Understand the provenance, reasoning, and evolution of important information
- Reason about relationships between different pieces of knowledge
- Identify contradictions and potential conflicts in their information
- Maintain clear boundaries between different knowledge domains (personal, fictional, learning, research)

## 5. Product Principles

Pekopeko should have these characteristics as a product:
- **Human Control**: AI proposes; human reviews; system commits. Reliability and traceability take priority over maximum automation.
- **Knowledge Integrity**: Canonical knowledge must be human-validated and maintain provenance, versioning, and historical recoverability.
- **Domain Separation**: The system must conceptually prevent accidental mixing of unrelated knowledge domains.
- **Modularity**: Support growing collection of modules without tight coupling between unrelated functionality.
- **Reliability**: Prioritize reliability over maximum automation, especially for important knowledge decisions.
- **Traceability**: Important knowledge should be explainable in terms of its source and reasoning.

## 6. Core Product Areas

Major functional areas that should exist:
- Persistent knowledge and memory system
- Human-reviewed knowledge ingestion pipeline
- Knowledge relationships and reasoning capabilities
- Domain separation mechanisms
- Review queue for proposed knowledge
- Provenance tracking and historical changes
- Conflict detection and contradiction analysis

## 7. Product Boundaries

What belongs inside Pekopeko:
- Persistent knowledge storage and management
- Human validation of knowledge propositions
- Knowledge relationships and reasoning capabilities
- Historical versioning and change tracking
- Provenance and source tracking
- Conflict detection and resolution

What does not belong inside Pekopeko:
- Specific implementation technologies (databases, vector stores, etc.)
- Final architecture decisions
- Mass-market consumer assistant features
- Unrestricted autonomous behavior for canonical knowledge
- Implementation details of modules

## 8. Long-Term Direction

Pekopeko could eventually become a highly reliable personal AI environment where:
- Information enters through many channels
- AI agents analyze and structure it
- Humans retain control over canonical knowledge
- Knowledge remains persistent and versioned
- Relationships between knowledge are preserved
- Agents can reason over the knowledge
- Specialized modules exploit the same knowledge foundation
- Changes can propagate through dependent knowledge
- Increasingly autonomous workflows can be built safely on top of the system

## 9. Open Product Questions

List unresolved questions that require human decisions:

- What exact initial V1 scope should be defined?
- What are the precise boundaries and interfaces for initial modules?
- Which types of AI-derived information require mandatory human review?
- Which future actions may eventually be autonomous?
- What are the exact rules for domain separation between knowledge types?
- What is the exact user experience of the review queue?
- How should different knowledge domains be conceptually separated?
- What level of automation is appropriate for different knowledge validation workflows?
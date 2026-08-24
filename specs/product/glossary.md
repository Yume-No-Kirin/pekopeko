# Glossary

## Pekopeko
The name of the personal AI environment project. Refers to the unified system that integrates multiple capabilities behind a single user interface.

## Module
A distinct functional component of the Pekopeko system with a specific responsibility and well-defined interface. Modules should be independently testable and maintain clear boundaries.

## Agent
An autonomous component or subsystem within Pekopeko that performs specific tasks or functions. Agents may interact with external providers and coordinate with other agents.

## Provider
A service or system that provides specific capabilities to Pekopeko, such as LLMs, speech engines, databases, or vector stores. Providers should be replaceable where reasonably practical.

## Memory
The persistent storage and management of information within Pekopeko. This includes both short-term and long-term data retention and retrieval capabilities.

## Knowledge
Information that has been processed, organized, and made available for retrieval and reasoning within the system. Knowledge is derived from sources and may be structured or unstructured.

## Domain
A category or classification of knowledge with shared characteristics and context (e.g. PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING). Domains provide conceptual boundaries for organizing knowledge and are isolated from one another by default; crossing that boundary requires an explicit cross-domain operation. See `specs/domain/knowledge-model.md` for the full domain model.

## Source
An origin of information or data that feeds into Pekopeko's knowledge base. Sources can include documents, databases, user input, or external APIs.

## Ingestion
The process of bringing information from various sources into the Pekopeko system for processing and storage.

## Retrieval
The process of finding and accessing stored information within Pekopeko based on user queries or system needs.

## Pipeline
A sequence of data processing steps that transform information from one form to another, typically as part of the ingestion or processing workflow.

## User Interface
The visual and interactive components through which users interact with the Pekopeko system. This includes both the frontend application and any command-line interfaces.

## Core
The shared infrastructure and foundational components that provide common capabilities to all modules within Pekopeko.

## Capability
A conceptual capability of the Pekopeko system, traceable to specific technical requirements and architectural components (e.g. Human Validation, Provenance Tracking). See `specs/architecture/capabilities.md` for the full capability catalog.

## Use Case
An end-to-end conceptual workflow — from user goal through processing stages to expected result — that validates the architecture supports a real scenario the system is intended to solve. See `specs/product/use-cases.md` for the full set of use cases.
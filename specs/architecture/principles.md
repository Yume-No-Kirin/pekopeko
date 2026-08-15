# Architectural Principles

These principles guide the design and development of Pekopeko. They are general guidelines rather than specific implementation decisions.

## 1. Modularity
Pekopeko is a single product composed of clearly separated modules. Modules must have explicit responsibilities and boundaries.

## 2. Shared Core
Cross-cutting capabilities should live in shared infrastructure/core components rather than being duplicated across modules.

## 3. Separation of Concerns
Product logic, domain logic, infrastructure, UI, and external providers should not become unnecessarily coupled.

## 4. Replaceability
External providers such as LLMs, speech engines, databases, vector stores, etc. should be replaceable where reasonably practical.
Do not over-engineer abstractions without a concrete need.

## 5. Source of Truth
The project must explicitly define authoritative data sources before implementing persistent knowledge.
Derived representations must not silently become authoritative.

## 6. Observability
Long-running or autonomous operations should eventually be observable and debuggable.

## 7. Testability
Core business behavior should be testable without requiring external AI providers whenever reasonably possible.

## 8. AI Safety / Reliability
AI-generated information must not automatically be treated as factual simply because an LLM produced it.
The system should preserve provenance for important information.
Agents must not silently invent, overwrite, or delete important persistent information.

## 9. Incremental Development
Prefer small independently testable increments over large implementations.

## 10. Documentation as a Contract
Specifications should describe intended behavior and constraints.
Implementation should follow the specifications rather than redefining product behavior implicitly.

## 11. Module Isolation
A module should depend on other modules through explicit interfaces rather than reaching directly into their internal implementation.

## 12. Single User Experience
Pekopeko should provide a unified GUI even though its internal functionality is modular.

## Additional Considerations

### Future-Proofing
The architecture should be designed to accommodate future expansion without requiring major rework or breaking changes.

### Scalability
While not immediately concerned with performance optimization, the architecture should allow for scaling as features are added and usage grows.

### Maintainability
The system should be structured in a way that makes it easy to understand, modify, and extend over time.

### Security
Security considerations should be integrated into the design from the beginning, even if specific implementations are deferred.

### Privacy
User data privacy should be a fundamental concern throughout the system design.
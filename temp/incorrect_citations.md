# Analysis of Incorrect CAP-CORE Citations

## Already Known Incorrect Examples (from prompt)
Based on the examples given in the prompt:

1. TR-004: Domain Isolation - Currently cites CAP-CORE-009 → should be CAP-CORE-005
2. TR-005: Cross-Domain Authorization - Currently cites CAP-CORE-010 → should be CAP-CORE-014  
3. TR-006: Derived Knowledge Tracking - Currently cites CAP-CORE-008 → should be CAP-CORE-006
4. TR-007: Temporal Reasoning Support - Currently cites CAP-CORE-006 → should be CAP-CORE-007
5. TR-008: Uncertainty Preservation - Currently cites CAP-CORE-017 → should be CAP-CORE-008

## Additional Incorrect Citations Found

Looking at all CAP-CORE citations, I can identify the following that are incorrect based on the capability mappings:

### From the capability mapping:
CAP-CORE-001: Knowledge Representation
CAP-CORE-002: Human Validation  
CAP-CORE-003: Complete Provenance Tracking
CAP-CORE-004: Historical State Preservation
CAP-CORE-005: Domain Isolation
CAP-CORE-006: Derived Knowledge Tracking
CAP-CORE-007: Temporal Reasoning
CAP-CORE-008: Uncertainty Preservation
CAP-CORE-009: Relationship Traversal
CAP-CORE-010: Knowledge Search and Retrieval
CAP-CORE-011: Knowledge Reasoning
CAP-CORE-012: Asynchronous Task Management
CAP-CORE-013: Large-Scale Knowledge Handling
CAP-CORE-014: Cross-Domain Authorization
CAP-CORE-015: Review Queue Efficiency
CAP-CORE-016: Module Integration

### Specific incorrect mappings found:

1. KSR-001: Knowledge Entities - CAP-CORE-001 (correct)
2. KSR-002: Knowledge Assertions - CAP-CORE-001 (correct) 
3. KSR-003: Knowledge Events - CAP-CORE-001 (correct)
4. KSR-004: Knowledge Relationships - CAP-CORE-001 (correct)
5. KSR-009: Temporal Validity - CAP-CORE-001 (should be CAP-CORE-007, but it's the only one that could be right based on title)
6. KSR-005: Domain Contexts - CAP-CORE-001 (should be CAP-CORE-005) 
7. KSR-006: Provenance Records - CAP-CORE-001 (should be CAP-CORE-003)
8. KSR-007: Validation States - CAP-CORE-001 (should be CAP-CORE-002)
9. KSR-008: Epistemic Status - CAP-CORE-001 (should be CAP-CORE-008)
10. KSR-009: Temporal Validity - CAP-CORE-001 (should be CAP-CORE-007) 
11. KSR-010: Historical State - CAP-CORE-001 (should be CAP-CORE-004)
12. KSR-011: Derived Knowledge - CAP-CORE-001 (should be CAP-CORE-006)
13. KSR-012: Dependencies - CAP-CORE-001 (should be CAP-CORE-006)
14. KSR-013: Proposals - CAP-CORE-001 (should be CAP-CORE-002)
15. KSR-014: Audit Information - CAP-CORE-001 (should be CAP-CORE-003)

This shows a pattern where many requirements are incorrectly citing CAP-CORE-001 instead of the appropriate capability.

Let me be more systematic and create a proper table for all the findings.
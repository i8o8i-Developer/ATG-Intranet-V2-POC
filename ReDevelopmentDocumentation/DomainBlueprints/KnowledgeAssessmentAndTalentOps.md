# Knowledge Assessment And Talent Ops

## Domain Summary

This Domain Groups Internal Knowledge, Learning Compliance, Recruitment Support, Offer Template Assets, And Talent Performance Utilities. In The New Platform These Capabilities Must Be Rebuilt As Deliberate Product Areas With Tenant-Aware Access And Clear Ownership.

## Current Capability Map

| Capability | Current Sources |
| --- | --- |
| Knowledge Publishing | atg_docs |
| Assessment And Compliance | assesment |
| Recruitment And Internship | l3 |
| Template Assets | Html_template |

## Current Risks

- Knowledge Metadata And External Document Storage Need Clearer Boundaries.
- Learning And Compliance Concepts Are Spread Across Separate Legacy Surfaces.
- Recruitment Workflow And Talent Performance Need Cleaner Product Separation.
- Template Assets Need Versioning, Review, And Better Governance.

## Target Product Areas

### Knowledge Hub

- Searchable Documentation.
- Ownership And Access Rules.
- Activity History.
- Internal Or External Rendering Strategy.

### Learning And Compliance Center

- Assessment Templates.
- Assignments.
- Completion Tracking.
- Compliance Signals.

### Talent Operations

- Recruitment Pipeline.
- Internship Workflow.
- Talent Performance Views.
- Candidate And College Tracking.

### Template Asset Studio

- Versioned Offer Templates.
- Variable Definitions.
- Preview And Approval.

## Target Aggregate Roots

- KnowledgeDocument.
- KnowledgePermission.
- KnowledgeActivity.
- LearningAssessment.
- LearningAssignment.
- LearningSubmission.
- Candidate.
- TalentAssignment.
- PerformanceSnapshot.
- ContentTemplate.
- ContentVariableDefinition.

## Multitenancy Rule

Knowledge, Assessments, Recruitment, And Templates Must Respect Tenant, Workspace, And Resource-Level Access Rules. Shared Internal Convenience Must Not Override Policy.

## Testing Priorities For The Rebuild

- Knowledge Permission Evaluation.
- Assessment Due Date And Completion Logic.
- Recruitment Workflow Integrity.
- Template Versioning And Variable Safety.
- Tenant Isolation Across Knowledge And Talent Data.

## Domain Rule For The Rewrite

Knowledge, Learning, And Talent Capabilities Must Be Treated As Real Product Domains With Search, Permissions, Workflow State, And Auditability. They Must Not Remain A Collection Of Utility Screens Wrapped Around External Tools.
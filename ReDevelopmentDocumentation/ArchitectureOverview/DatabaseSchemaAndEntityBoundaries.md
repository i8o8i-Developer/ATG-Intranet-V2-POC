# Database Schema And Entity Boundaries

## Purpose

This Document States How The Current Data Model Should Be Read During Discovery And What Rules Must Govern The New Multitenant Schema.

## What The Current Schema Proves

- The Repository Already Encodes Real Business Objects Across Identity, PeopleOps, Finance, Delivery, Revenue, Knowledge, Assessments, And Talent.
- Several Important Relationships Are Clear Enough To Use As Migration Inputs.
- Some High-Value Structures Are Still Stored In JSONField Or ArrayField Shapes That Need First-Class Modeling In The Rebuild.

## Current Schema Risks

- Shared User And Department Context Carry Too Much Cross-Domain Meaning.
- JSON Or List Fields Hide Queryable Business Relationships.
- Historical State And Transition Logic Are Not Consistently First-Class.
- There Is No Universal Tenant Key Across Core Data.

## Target Schema Rules

- Every Core Aggregate Must Be Tenant-Aware.
- Every Cross-Domain Reference Must Point To An Aggregate Root Or Explicit Contract.
- JSON Must Not Represent A First-Class Business Entity.
- Historical And Approval Flows Must Be Modeled Explicitly.
- External Artifact Metadata Must Stay Inside The ERP Even If The Artifact Lives Elsewhere.

## Recommended Aggregate Families

| Family | Target Aggregate Examples |
| --- | --- |
| Tenant And Identity | Tenant, Organization, Workspace, UserAccount, RoleAssignment, CapabilityGrant |
| People Operations | Employee, EmploymentAssignment, OnboardingOffer, LeaveRequest, SharedCredential |
| Finance | CompensationPlan, PayPeriod, PayrollRun, PayrollLineItem, PayoutExecution, PayslipDocument |
| Delivery | ProjectWorkspace, ProjectContact, TeamAssignment, DeliveryMilestone, DeliveryDocument, DeliveryAlert |
| Work | WorkItem, WorkEntry, DailyStatusEntry, ExternalWorkMapping |
| Revenue | LeadAccount, LeadContact, Opportunity, ProposalArtifact, AuditArtifact, ConversionRecord |
| Knowledge And Learning | KnowledgeDocument, KnowledgePermission, LearningAssessment, LearningAssignment |
| Talent | Candidate, CollegePipelineRecord, TalentAssignment, PerformanceSnapshot |

## Migration Rules

- Preserve Legacy Identifiers In Crosswalk Tables.
- Migrate Shared Identity And Tenant Foundations Before Transaction Domains.
- Normalize JSON-heavy Structures Before Building Dependent Feature Screens.
- Reconcile Financial, Access-Sensitive, And Client-Facing Records Before Cutover.

## Database First Rule

If The New Platform Cannot Explain Aggregate Ownership, Tenant Scope, Uniqueness, State Transitions, And Historical Audit At The Schema Level, Then The Rebuild Is Still Too Close To The Legacy Monolith.
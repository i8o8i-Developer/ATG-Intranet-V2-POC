# LMS And Lead Operations

## Domain Summary

The Revenue Side Of The Product Is Split Between Banao And LMS. Banao Is The Operational CRM And Lead Pipeline System. LMS Is The Analytical And BA Workload Layer. Together They Form The Revenue Operations Domain That Must Be Rebuilt As One Tenant-Aware Product Area.

## Current Capability Map

| Capability | Current Implementation |
| --- | --- |
| Lead Capture | Banao Lead Create Routes And Lead Model |
| Qualification | Workflow Status, Call Status, Follow-Up Date, Assignment |
| Collaboration | Lead Notes, Proposal Links, Audit Links |
| Analytics | LMS Dashboards, Workload, Closures, Performance Views |
| Classification | Tags, Industry, Origin, Type, Importance |

## What Real Usage Data Adds

Workflow Intelligence Confirms Revenue As An Active Domain, Not A Side Module.

- 699 Hits In The Measured Window.
- Active Routes Including `api/leads/`, `api/tags/`, `api/lead-dashboard/<int:lead_id>/`, And `banao/lead-create/`.

## Current Domain Risks

- CRM Operations And Analytics Share The Same Operational Tables Too Closely.
- Contact Methods Still Need Better Structure.
- Opportunity And Pricing Are Not First-Class Enough Yet.
- Conversion To Delivery Is Still Too Indirect.

## Target Revenue Architecture

### Subdomains

- Prospect Capture.
- Lead Qualification.
- Opportunity Management.
- Proposal And Audit Artifacts.
- BA Workload Planning.
- Revenue Analytics.
- Lead-To-Project Conversion.

### Target Aggregate Roots

- LeadAccount.
- LeadContact.
- LeadAssignment.
- LeadActivity.
- Opportunity.
- ProposalArtifact.
- AuditArtifact.
- ConversionRecord.
- AnalystCapacityPlan.

### Multitenancy Rule

Every Lead, Opportunity, Proposal, Audit Artifact, And Revenue Dashboard Must Be Tenant-Aware. Banao And LMS Must Stop Behaving Like Parallel Apps Sharing Loose Operational Meaning.

## Target UI Structure

- Personal Lead Queue.
- Team Revenue Board.
- Opportunity Timeline.
- Proposal And Audit Workspace.
- BA Workload Planner.
- Revenue Analytics Hub.

## MCP And External Agent Opportunities

This Domain Is A Strong Candidate For Read-Heavy MCP Tools Such As:

- Lead Summary.
- Opportunity Snapshot.
- Follow-Up Queue.
- BA Workload Summary.

Write Paths Should Only Be Exposed Later Under Explicit Approval And Audit.

## Testing Priorities For The Rebuild

- Lead Lifecycle Validation.
- Assignment And Reassignment Safety.
- Opportunity And Conversion Integrity.
- Proposal And Audit Artifact Linking.
- Analytics Consistency Against Transactional Truth.
- Tenant Isolation Across Revenue Data.

## Revenue Rule For The Rewrite

Do Not Rebuild Revenue Screens As Simple CRUD. The Domain Must First Define Lead, Opportunity, Conversion, And Analytics Semantics Clearly, Or The New Platform Will Repeat The Same Drift In Better-Looking Screens.
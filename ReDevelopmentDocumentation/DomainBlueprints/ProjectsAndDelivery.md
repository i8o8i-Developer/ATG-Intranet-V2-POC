# Projects And Delivery

## Domain Summary

The Delivery Domain Is One Of The Operational Centers Of The Product. It Owns Project Setup, Team Composition, Milestones, Budgets, Repositories, Documents, Delays, Alerts, And Compliance-Adjacent Workflows. In The New Platform It Must Become A Tenant-Aware Project Workspace Product, Not A Large Shared App.

## Current Capability Map

| Capability | Current Implementation |
| --- | --- |
| Project Creation | Project Onboarding Views And Project Model |
| Teaming | Team Members, Replacement History, Hat Types |
| Milestones | Project Milestones And Checkpoint Generation |
| Budgeting | Budget And Role-Based Budget Data |
| Repositories | Repository And User Repo Status |
| Documents | Project Document And Related Files |
| Delays And Alerts | Delay Model And Notification Surfaces |
| Compliance Support | Terms Acceptance And Anti-Phishing Assignment Support |

## What Real Usage Data Adds

Workflow Intelligence Confirms Delivery As A Core High-Traffic Area.

- 1765 Hits In The Measured Window.
- 19 Active Routes Observed.
- The Most Used Route In The Entire System Is Delivery-Related: `project/get_user_repo/<int:member_id>/<int:project_id>/`.

## Current Risks

- Project Carries Too Many Concerns At Once.
- Project And Task Context Are Too Tightly Coupled.
- Client Contacts And Some Structured Inputs Need Better Modeling.
- Dashboard Logic Pulls Too Many Concerns Into One Request Path.

## Target Delivery Architecture

### Subdomains

- Project Workspace.
- Team And Access.
- Delivery Planning.
- Work Execution.
- Repository Governance.
- Delivery Documents.
- Risk And Alerts.
- Compliance.

### Target Aggregate Roots

- ProjectWorkspace.
- ProjectContact.
- TeamAssignment.
- DeliveryMilestone.
- DeliveryCheckpoint.
- RepositoryGrant.
- DeliveryDocument.
- DeliveryAlert.
- ComplianceCampaign.

### Multitenancy Rule

Every Project Workspace Must Live Inside Tenant And Workspace Boundaries. Client Sharing, Repository Access, And Compliance Signals Must Respect That Scope Explicitly.

## Target UI Structure

- Overview.
- Timeline.
- Team.
- Work.
- Documents.
- Repositories.
- Risks And Alerts.
- Compliance.
- Settings.

## Integration Rule

GitHub, ClickUp, Slack, And Document Boundaries Must Sit Behind Adapters And Durable Worker Flows. No Project Screen Should Depend On Unmediated Integration Side Effects.

## Testing Priorities For The Rebuild

- Project Creation Validation.
- Milestone And Checkpoint Bootstrapping.
- Team Assignment And Replacement Audit.
- Repository Grant And Revoke Safety.
- Delay And Alert Integrity.
- Tenant Isolation For Project And Client Data.

## Delivery Rule For The Rewrite

Treat Every Project As A Real Workspace With Explicit Membership, Contracts, Documents, Risks, And Integrations. If Delivery Logic Still Depends On Shared Legacy Reads Across Apps, The Rebuild Is Incomplete.
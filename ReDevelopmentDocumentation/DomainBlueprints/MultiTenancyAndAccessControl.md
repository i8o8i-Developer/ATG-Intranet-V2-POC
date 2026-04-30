# Multitenancy And Access Control

## Current Reality

The Current Product Uses Logical Segmentation Across Departments, Roles, Projects, And Document Permissions, But It Is Not Truly Multitenant. That Current Reality Is Important As Discovery, But It Is Not The Target State.

## Rebuild Decision

True Multitenancy Is Required For The New Platform. The New Intranet Must Not Repeat The Current Pattern Of Broad Shared Tables With Runtime-Only Segmentation.

## Current Segmentation Layers

| Segmentation Layer | How It Works Today |
| --- | --- |
| Authentication Identity | Django User And Custom Login Backends |
| Group-Based Authorization | Group Membership Drives Many View Checks |
| Department Membership | Users Join Departments Through `Works_in` |
| Project Membership | Access To Delivery Surfaces Is Scoped By Team Membership |
| Document Visibility | Docs Use Permission Modes And Department Logic |
| Brand Or Business Line | Certain Offer And Finance Flows Distinguish Internal Brands |
| Client Sharing | Some External Access Uses Project Tokens |

## Why The Current Model Is Insufficient

- There Is No Tenant Root Aggregate.
- There Is No Universal Tenant Key Across Core Domain Data.
- Permission Rules Depend Too Much On View Logic.
- Search, Reporting, And Exports Are Not Tenant-Scoped By Design.
- Integration Credentials Are Not Governed By A Tenant-First Model.

## Target Tenancy Model

### Canonical Hierarchy

- Tenant.
- Organization.
- Business Unit.
- Workspace.
- Domain Aggregate.

### Rules

- Every Core Aggregate Must Belong To A Tenant Hierarchy.
- Every API Request Must Resolve Tenant Context Before Business Logic Runs.
- Every Search And Export Must Respect Tenant Scope.
- Every Integration Credential Must Be Tenant Or Workspace Scoped Where Applicable.
- Every Audit Record Must Include Tenant Context.

## Target Authorization Model

| Layer | Rule |
| --- | --- |
| Subject | User, Service Account, Or External Agent Principal |
| Tenant Membership | Defines Whether The Subject Belongs To The Tenant At All |
| Organization Or Business Unit Membership | Narrows Operational Ownership Scope |
| Workspace Membership | Controls Access To Projects, Leads, Knowledge Spaces, And Queues |
| Capability Grant | Defines Actions Such As View, Approve, Export, Create, Or Administer |
| Resource Policy | Applies Row-Level Or Entity-Level Rules Such As Ownership Or Sensitivity |

## Data Model Additions Required

- Tenant.
- Organization.
- BusinessUnit.
- Workspace.
- WorkspaceMembership.
- RoleAssignment.
- CapabilityGrant.
- ResourceAccessPolicy.
- AccessAuditLog.

## Migration Rules

- Build Tenant And Workspace Foundations Before Rebuilding Feature Modules.
- Map Existing Department, Project, And Brand Segmentation Into Tenant-Aware Workspaces.
- Replace Ad Hoc Group Checks With Policy Evaluation.
- Replace Token-Only External Sharing With Signed, Expiring, Audited Access Grants.

## Access Rule For MCP

MCP-Exposed Tools And Resources Must Inherit The Same Tenant, Workspace, And Capability Rules As Human Users. No Agent May Read Or Mutate Cross-Tenant Data Through Convenience Paths.

## Final Rule

The New Platform Must Treat Tenant Isolation As A Core Business Property, Not As An Optional Future Enhancement. If A Module Cannot Explain How It Stores, Filters, Audits, And Exposes Tenant Scope, It Is Not Ready To Ship.
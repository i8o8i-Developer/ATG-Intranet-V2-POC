# Test-Driven Development Plan

## Purpose

This Document Defines How The New Intranet Must Be Built From Scratch Using Test-First Discipline. It Is Paired With The Scope Of Work And Applies To The Entire Rebuild Program, Not Only To A Short-Term Overlay Or Pilot.

## Core TDD Rule For This Program

Every New Module, API, Tenant Rule, Integration Contract, Migration Mapper, And UX Surface Must Be Defined By Failing Evidence First, Implemented In The Smallest Passing Slice Next, And Refactored Only After That Evidence Exists.

### Red, Green, Refactor In This Repo Means

- Red: Define The Expected Behavior Through A Test, Contract, Or Validation Fixture Before Writing Production Logic.
- Green: Implement The Smallest Change That Makes The Expected Behavior Pass.
- Refactor: Improve Design Only After The Behavior Is Proved.

## What Must Be Proven Across The Rebuild

| Area | What TDD Must Prove |
| --- | --- |
| Multitenancy | Tenant Isolation Exists In Data, Queries, APIs, Search, And Access Policy |
| Identity And Access | Role, Workspace, And Capability Rules Are Enforced Consistently |
| Domain Logic | Each Domain Preserves The Current Business Behavior Without Carrying Legacy Coupling |
| Integrations | External Contracts Are Stable, Audited, Retriable, And Safe |
| Migration | Legacy Data Can Be Mapped, Reconciled, And Verified Before Cutover |
| UX | New Screens Render Correctly, Respect Permissions, And Support Real Workflows |
| MCP Exposure | Agent-Facing Tools, Resources, And Actions Are Permissioned, Tenant-Aware, And Audited |

## Build Order Under TDD

### Phase 1: Foundations First

Write Failing Tests First For:

- Tenant And Workspace Models.
- Identity And Access Policy Evaluation.
- Shared Audit And Outbox Primitives.
- Base API Authentication And Authorization.
- Design-System Shell And Navigation Permissions.

### Phase 2: Core Domains

Write Failing Tests First For:

- People Operations.
- Projects And Delivery.
- Work Management.
- Revenue And LMS.

### Phase 3: Support Domains

Write Failing Tests First For:

- Finance And Payroll.
- Knowledge And Documentation.
- Assessments And Compliance.
- Talent And Recruitment.

### Phase 4: Platform And AI Boundary

Write Failing Tests First For:

- External Integration Adapters.
- MCP Tool Exposure Rules.
- Agent Action Authorization.
- Tenant-Aware Tool Discovery And Audit Trails.

### Phase 5: Migration And Cutover

Write Failing Tests First For:

- Crosswalk Integrity.
- Record Count Reconciliation.
- Financial Reconciliation.
- Tenant Mapping Accuracy.
- Critical End-To-End User Journeys.

## Test Layers

| Layer | Purpose | Examples |
| --- | --- | --- |
| Unit Tests | Prove Isolated Domain Rules | Status Transitions, Validators, Calculators, Permission Predicates |
| Service Tests | Prove Module-Level Use Cases | Onboarding Flow, Payroll Run, Project Creation, Lead Stage Movement |
| API Contract Tests | Prove Stable Client Contracts | Create, Read, Update, Filter, Search, And Permissioned Actions |
| Tenant Isolation Tests | Prove Cross-Tenant Safety | Row Filtering, Search Scope, Export Scope, Workspace Membership Boundaries |
| Integration Contract Tests | Prove Adapter Correctness | GitHub, Slack, Razorpay, Google, ClickUp, Email, Mantis, S3 |
| UI Tests | Prove Real User Screens | Workbench Rendering, Empty States, Validation, Permission Gate, Navigation |
| MCP Contract Tests | Prove Agent Access Safety | Tool Visibility, Context Scoping, Action Authorization, Audit Trail |
| Migration Tests | Prove Legacy Mapping | Record Counts, Identifier Mapping, Historical Fidelity, Financial Accuracy |
| Smoke Tests | Prove Deployable Runtime | Startup, Background Workers, Tenant Bootstrapping, Critical Screens |

## Minimum Test Requirements Per Module

Every Module Must Define Before Coding:

- Acceptance Criteria.
- Required Domain Rules.
- Tenant Rules.
- Permission Rules.
- API Contract Surface.
- UI States.
- Integration Boundaries.
- Migration Impact.

## Canonical Test Matrix By Concern

### Multitenancy

- Tenant Creation And Isolation.
- Workspace Membership Filtering.
- Cross-Tenant Access Rejection.
- Tenant-Scoped Search And Export.
- Tenant-Scoped Integration Credential Resolution.

### Identity And Access

- Role Assignment Safety.
- Capability Grant Enforcement.
- Policy Evaluation On Read And Write Paths.
- Audit Record Creation For Sensitive Actions.

### Projects And Delivery

- Project Creation Validation.
- Milestone Bootstrapping.
- Team Membership Rules.
- Repository Access Granting.
- Delay And Risk Tracking.

### Revenue And LMS

- Lead Lifecycle Transition Rules.
- Assignment And Reassignment Logic.
- Opportunity And Conversion Integrity.
- Analytics Consistency Against Transaction Truth.

### Finance And Payroll

- Payroll Calculation Correctness.
- Approval Lane Integrity.
- Payout Idempotency.
- Payslip Immutability.
- Tenant-Scoped Financial Visibility.

### Knowledge, Assessments, And Talent

- Document Permission Evaluation.
- Assessment Assignment And Completion Logic.
- Recruitment Workflow Integrity.
- Template Rendering Safety.

### MCP Exposure

- Only Allowed Tools Are Visible To A Given Principal.
- Tool Calls Respect Tenant And Workspace Scope.
- Read Tools Do Not Leak Cross-Tenant Data.
- Write Tools Require Explicit Authorization And Audit.
- ERP Remains Correct Even If No Agent Is Connected.

## TDD Build Sequence Within A Feature Slice

1. Write The Acceptance Tests Or Validation Cases.
2. Write The Narrow Unit Or Service Tests For The Rule Being Added.
3. Implement The Smallest Passing Backend Change.
4. Add Or Update API Contract Tests.
5. Add Or Update UI Tests For The Affected Surface.
6. Run The Narrowest Possible Validation Immediately.
7. Refactor Only After The Slice Is Green.

## Dry Run Definition For The Rebuild

The Dry Run For Any Rebuild Slice Is Successful Only When:

- Application Imports Cleanly.
- Required Migrations Are Intentional And Reviewed.
- The Touched Test Suite Passes.
- Tenant Isolation Checks Pass For The Affected Module.
- No Live External Production Integration Is Called Unintentionally.
- The Touched UI Surface Loads In A Safe Environment.
- MCP Contract Checks Pass If The Slice Touches Agent-Facing APIs.

## CI Gate Order

1. Install Dependencies.
2. Load Settings And Run Framework Health Check.
3. Run Migration Drift Check.
4. Run Narrow Unit And Service Tests For Touched Modules.
5. Run Tenant Isolation And Access Tests For Touched Modules.
6. Run API Contract Tests.
7. Run UI Or Template Validation For Touched Screens.
8. Run Integration Adapter Tests If Boundaries Changed.
9. Run MCP Contract Tests If Agent-Facing APIs Changed.
10. Publish Logs And Artifacts For Review.

## Known Local Constraint

Full Local Django Test Execution Is Currently Affected By Settings Bootstrap Drift In The Existing Repository Environment. That Does Not Remove TDD. It Changes Where Some Checks Must Run Until The New Platform Runtime Is Stable.

### Practical Execution Rule

- Write The Test First In The Repo.
- Run Narrow Syntax And Import Validation Locally Where Possible.
- Run Full Django-Oriented Validation In Docker Or A Production-Like Environment When Local Bootstrap Limits Apply.

## Definition Of Done For A Rebuild Module

A Module Is Not Done Until:

- Its Domain Rules Are Covered By Tests.
- Its Tenant Rules Are Covered By Tests.
- Its Access Rules Are Covered By Tests.
- Its API Contract Is Tested.
- Its UI States Are Validated.
- Its Integration Boundaries Are Tested Or Safely Stubbed.
- Its Migration Impact Is Documented.
- Its MCP Exposure Rules Are Tested If It Publishes Agent-Facing APIs.

## Final TDD Rule

No Part Of The New Intranet Is Done Because It Looks Better Than The Old One. It Is Done Only When The Intended Behavior Was Defined First, Proven Narrowly, Revalidated After Change, And Shown To Be Safe For Multitenant, Production-Grade Use.
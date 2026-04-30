# Statement Of Work

## One Page Summary

| Topic | Statement |
| --- | --- |
| Product In Scope | A New Intranet Platform Built From Scratch That Recreates And Improves The Full Breadth Of The Current Internal ERP |
| Build Model | Greenfield Rebuild With Controlled Migration From The Current System |
| Target Tenancy | True Multitenant Architecture Across Modules, Data, Access, And Integrations |
| AI Position | AI Is Not Embedded Into Core ERP Logic; The ERP Exposes MCP-Compatible APIs For External Agents |
| Core Business Goal | Preserve Current Operational Breadth While Removing Coupling, UX Debt, Weak Data Shapes, And Access Ambiguity |
| Success Condition | The New Platform Can Replace The Current Intranet Across Identity, HR, Delivery, Revenue, Knowledge, Talent, And Finance With Stronger Design, Tenancy, And Contracts |

## Engagement Summary

This Statement Of Work Defines The Full Redevelopment Program For Rebuilding The Current Intranet From Scratch. The Existing Repository Already Proves Real Operational Coverage across HR, Payroll, Project Delivery, Work Tracking, Lead Operations, Documentation, Assessments, Recruitment, And Supporting Integrational Workflows. That Existing Breadth Is The Functional Baseline For The New Product.

The New Program Is Not A Partial Overlay On Top Of The Current Monolith. It Is A New Platform Build With New Design, New Data Contracts, New Access Architecture, And New Tenant Boundaries. The Current System Remains Critical As A Discovery Reference, Migration Source, And Validation Baseline Until Final Cutover.

## Scope Decision

The Scope Is Explicit:

- Rebuild The Full Current System Breadth From Scratch.
- Redesign The User Experience Across All Major Modules.
- Introduce True Multitenancy Across Core Domain Data And Access.
- Rebuild Integrations Behind Stable Adapters.
- Keep AI Outside The ERP Core And Publish Secure MCP-Compatible APIs For External Agents.

## Current Operational Footprint That Must Be Preserved

| Domain | Current Working Functionality | Primary Current Apps | Why It Must Be Preserved |
| --- | --- | --- | --- |
| Identity And Org | User Profiles, Departments, Skills, Employment Status, Role And Finance Context | users | Shared Identity And Access Backbone For All Other Modules |
| People Operations | Leave, Onboarding, Offer Generation, Certificates, Credentials, Notifications | mainapp, users, Html_template | Critical Employee Lifecycle And Internal Ops Flows |
| Payroll And Finance | Payroll Review, Approval, Payout Handling, Payslip Rendering, Bank Details | users, mainapp | High-Risk Financial Flows Must Survive Rebuild Cleanly |
| Projects And Delivery | Project Setup, Milestones, Teaming, Repositories, Documents, Delays, Anti-Phishing | project, git, Github_extension | Delivery Is One Of The Highest-Traffic Operational Areas |
| Work Management | Tasks, Subtasks, EOD, Slack Projection, External Work Mapping | Tasks_dashboard | Daily Execution And Reporting Depend On It |
| Revenue Operations | Lead Intake, BA Workload, Proposal Links, Audit Links, Analytics Dashboards | lms, banao | Live GTM And Delivery Conversion Flows Depend On It |
| Knowledge And Learning | Docs, Google-Backed Publishing, Assessments, Assignment Tracking | atg_docs, assesment | Internal Knowledge And Compliance Must Continue |
| Talent Operations | Internship, Recruitment, College Tracking, Performance Views | l3 | Hiring And Early-Career Ops Already Run Here |
| Platform Runtime | Auth Backends, Celery, Redis, Storage, Settings, URL Composition | Intranet | Current Runtime Constraints Inform The New Architecture |

## Program Objectives

- Build A New Intranet Platform From Scratch Without Losing Current Operational Capability.
- Remove Shared-Model Coupling And Replace It With Domain-Owned APIs, Events, And Read Models.
- Replace Weak JSON And Array Business Structures With First-Class Relational Or Explicitly Modeled Data.
- Redesign All Major Screens Into Coherent Product Surfaces Instead Of Organic Template Growth.
- Introduce Tenant-Aware Identity, Workspace, Data Ownership, And Access Policy Across The Product.
- Move All Third-Party System Boundaries Behind Durable Integration Contracts.
- Publish A Secure MCP-Compatible Agent Access Surface So AI Clients Can Use ERP Context Without Becoming ERP Runtime Logic.

## In Scope Workstreams

| Workstream | What It Covers | Primary Outputs |
| --- | --- | --- |
| Current-State Discovery | Validate Business Flows, Hidden Rules, Exception Paths, And Cross-App Dependencies | Capability Map, Current-State Gap Assessment, Migration Inventory |
| Product Architecture | Define New Target Architecture, Module Boundaries, Multitenant Model, Integration Strategy, And MCP Boundary | Technical Design Document, ADRs, Platform Contracts |
| Data Architecture | Define Target Schemas, Aggregate Roots, Tenant Keys, Historical Models, And Migration Strategy | Data Model Package, Migration Crosswalks, Reconciliation Rules |
| Identity And Access | Rebuild Authentication, Authorization, Role Assignment, Workspace Access, And Audit | Access Model, Role Catalog, Tenant And Workspace Policy Matrix |
| People Operations | Rebuild Onboarding, Leave, Credentials, Certificates, And Employee Lifecycle | PeopleOps APIs, UX Flows, Approval Rules |
| Projects And Delivery | Rebuild Project Workspace, Teaming, Milestones, Repositories, Documents, Delays, Risk And Compliance | Delivery Domain Design, APIs, UX Workbench, Integration Contracts |
| Work Management | Rebuild Tasks, EOD, Work Tracking, And External Mapping | Work Domain Model, APIs, Reporting Surfaces |
| Revenue Operations | Rebuild CRM, Opportunity Flow, BA Workload, Analytics, Proposals, And Conversion | Revenue APIs, Read Models, UX Workbench |
| Knowledge And Talent | Rebuild Docs, Assessments, Recruitment, Talent Tracking, And Template Assets | Knowledge And Talent Domain Models, UX Flows, Search And Permission Model |
| Finance And Payroll | Rebuild Payroll, Compensation, Approval, Payout, And Payslip Flows | Finance Domain Model, Gateway Adapters, Reconciliation Rules |
| Frontend Experience | Build A New Consistent Design System And Module UX | Design Tokens, Navigation Model, Screen Library |
| Integration And Platform | Rebuild External Boundaries For GitHub, ClickUp, Slack, Razorpay, Google, Mantis, Email, S3, And PostHog | Adapter Layer, Outbox Rules, Monitoring And Retry Strategy |
| MCP And External Agent Access | Expose Safe ERP Context, Tools, And Promptable Resources To External Agents | MCP Strategy, Tool Catalog, Auth Rules, Audit Policy |
| Quality And Cutover | Test Strategy, CI, UAT, Migration Rehearsal, Rollout, And Hypercare | TDD Plan, Validation Packs, Cutover Runbook |

## Functional Scope By Domain

### Identity And Access

- Tenant-Aware Authentication And Session Management.
- Organization, Business Unit, Workspace, Role, And Capability Assignment.
- Employee Profile, Position, Department, And Membership Modeling.
- Centralized Policy Evaluation And Access Audit.

### People Operations

- Offer Generation, Onboarding Acceptance, Employee Provisioning, And Status Transitions.
- Leave Request, Calendar, Approvals, And Manager Visibility.
- Credential Vault, Sharing Controls, And Auditability.
- Certificates, Feedback, Resignation, And Bench Tracking.

### Projects And Delivery

- Project Creation, Client Context, Technical Stack, Team Assignment, And Timeline Modeling.
- Milestones, Components, Checkpoints, Risk, Delays, And Notifications.
- Repository Access, Terms Handling, Documents, Client Sharing, And Compliance Signals.
- Delivery Workspace For Team, Work, Documents, Risks, And Repositories.

### Work Management

- Tasks, Subtasks, Work Links, PR Mapping, Assignment, And EOD.
- Manager And Team Execution Views.
- External Task System Mapping And Sync Boundaries.

### Revenue Operations

- Lead Capture, Qualification, Assignment, Notes, Proposals, Audits, And Stage History.
- Opportunity And Conversion Modeling.
- BA Workload And Revenue Analytics.
- Lead-To-Project Handoff Rules.

### Finance And Payroll

- Compensation Plans, Pay Periods, Payroll Runs, Approval Lanes, Payouts, And Payslips.
- Department, Role, And Tenant-Aware Finance Visibility.
- Gateway Execution And Reconciliation.

### Knowledge, Learning, And Talent

- Documentation Publishing, Permissions, Search, And Activity History.
- Assessments, Assignments, Completion, And Compliance.
- Recruitment, Internship, Performance, And Template Asset Management.

## AI Positioning Rule

The New ERP Is Not An AI Runtime. It Is A Deterministic Business System With Strong Domain Contracts, Clean Access Control, And Observable Integrations.

AI Enters Through An External Agent Boundary:

- The ERP Publishes Secure MCP-Compatible APIs And Tools.
- External Agents Consume ERP Context Through Those Contracts.
- Agent Actions Must Respect Tenant Scope, Role Scope, And Audit Requirements.
- No Core Business Flow Depends On Embedded Prompt Logic To Remain Correct.

## Multitenancy Rule

True Multitenancy Is In Scope For The New Build. This Is Not Optional Future Work.

That Means:

- Every Core Domain Record Must Belong To A Tenant Or Tenant-Scoped Hierarchy.
- Access Policy Must Be Tenant-Aware, Not Just Group-Aware.
- Integration Credentials Must Be Tenant Or Workspace Scoped Where Applicable.
- Search, Reporting, Exports, And APIs Must Respect Tenant Isolation By Design.

## Delivery Model

The Program Uses A Greenfield Build With Controlled Migration, Not A Cosmetic Refactor Of The Existing Codebase.

### Delivery Phases

| Phase | Primary Goal |
| --- | --- |
| Phase 0 | Finalize Discovery, Capability Inventory, And Target Product Contracts |
| Phase 1 | Build Shared Foundations: Tenancy, Identity, Access, Design System, Platform Runtime |
| Phase 2 | Build High-Traffic Core Domains: Projects, Work Management, Revenue, PeopleOps |
| Phase 3 | Build Finance, Knowledge, Assessment, Talent, And Remaining Support Domains |
| Phase 4 | Expose MCP-Compatible Agent APIs, Tool Catalog, And External Agent Governance |
| Phase 5 | Execute Data Migration, UAT, Parallel Validation, Cutover, And Hypercare |

## Deliverables

| Deliverable | Description | Acceptance Evidence |
| --- | --- | --- |
| Scope Of Work | Canonical Scope, Boundaries, And Program Goals | Stakeholder Approval |
| Test-Driven Development Plan | Build Order, Test Strategy, And Delivery Discipline | Engineering Approval |
| Technical Design Document | New Platform Architecture, Tenancy Model, Domain Boundaries, And Integration Design | Architecture Approval |
| MCP Agent Integration Strategy | External Agent Boundary, Tool Exposure Model, Auth And Audit Rules | Platform And Security Approval |
| Data Model Package | Target Entities, Tenant Keys, Migration Crosswalks, And History Models | Data Review Approval |
| UX Blueprint Package | Navigation, Design System, And Module-Level Screen Models | Product Approval |
| Migration Plan | Legacy Extraction, Mapping, Reconciliation, And Cutover Sequence | Migration Readiness Approval |
| Rollout Runbook | Release, Monitoring, Rollback, Hypercare, And Incident Procedures | Go-Live Readiness Approval |

## Acceptance Criteria

- The New Platform Covers The Full Operational Breadth Of The Current Intranet.
- True Multitenancy Exists In Data, Access Policy, And API Behavior.
- Major UX Surfaces Are Rebuilt With A Deliberate Product Design System.
- External Integrations Run Behind Stable Adapters And Observable Async Paths.
- MCP-Compatible APIs Expose ERP Context Safely Without Embedding AI Logic Inside Core Business Rules.
- Migration Rehearsals Prove That Current Records Can Be Mapped Into The New Platform Safely.
- Business Owners Can Recognize Their Existing Workflows In The New Product Model.

## Out Of Scope Unless Explicitly Added

- Replacing GitHub, Slack, ClickUp, Razorpay, Google, Mantis, Email, Or S3 As External Products Themselves.
- Building LLM Orchestration Logic Directly Into Every ERP Flow.
- Treating Prompt Templates As The Main Product Architecture.
- Cutting Over Without Migration Rehearsal And Reconciliation.

## Assumptions And Dependencies

- Current Product Behavior Is Business-Relevant Even Where Implementation Quality Is Weak.
- Domain Owners Can Help Confirm Hidden Rules, Exceptions, And Critical Reports.
- Legacy Data Is Accessible Enough For Mapping And Reconciliation.
- The Team Can Introduce New Runtime Boundaries, New Frontend Patterns, And New Database Structures Where Needed.
- AI Agent Connectivity Will Be Externalized Through MCP-Compatible APIs Rather Than Baked Into Core ERP Control Flow.

## Risks And Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Full Rebuild Scope Drifts Into Reimplementation Chaos | Delivery Delay And Incoherent Product Shape | Lock Domain Contracts, Build Order, And TDD Gates Before Major Coding |
| Tenant Design Is Added Too Late | Rework Across Every Domain | Build Tenancy Into Shared Foundations First |
| Legacy Rules Are Missed During Greenfield Build | Functional Regression | Use Current-State Docs, Real Data, And Domain Walkthroughs As Baselines |
| Embedded AI Logic Creeps Into Core ERP Paths | Correctness And Audit Risk | Keep AI Access Behind MCP-Compatible External Contracts Only |
| Integrations Reintroduce Coupling | Operational Fragility | Enforce Adapter And Outbox Rules Across Every External Boundary |
| Migration Quality Is Weak | Trust Failure At Cutover | Require Crosswalks, Reconciliation, And Cutover Rehearsals |

## Final Scope Rule

This Program Is A Full New-Intranet Build, Not A Light Cleanup Of The Current Monolith. The Current Repository Must Be Read As The Truth Source For What The Business Needs, While The New Platform Must Be Designed As A Better Product: Multitenant, Better Structured, Better Designed, Better Tested, And Safe For External MCP-Based AI Collaboration.
# Redevelopment Documentation Index

## Purpose

This Documentation Library Defines The Redevelopment Program For Building A New Intranet Platform From Scratch While Preserving The Full Operational Breadth Of The Current System. The Existing Repository Is The Discovery Source, Migration Source, And Capability Reference. It Is Not The Final Target Runtime.

The New Direction Is Explicit:

- Rebuild The Current Product Breadth From Scratch.
- Introduce True Multitenant Architecture Instead Of Continuing Logical Segmentation Only.
- Redesign All Major Frontend Surfaces With A Deliberate Product Experience Instead Of Organic Template Growth.
- Keep AI Outside The ERP Core And Expose Secure MCP-Compatible APIs For External Agents To Connect.
- Use The Current System For Discovery, Validation, And Migration, Not As The Long-Term Architecture Base.

## How To Use This Library

Read The Documentation In This Order:

1. [DeliveryArtifacts/StatementOfWork.md](DeliveryArtifacts/StatementOfWork.md) For Scope, Target Product Outcome, Program Boundaries, And Delivery Expectations.
2. [DeliveryArtifacts/TestDrivenDevelopmentPlan.md](DeliveryArtifacts/TestDrivenDevelopmentPlan.md) For How The New Intranet Must Be Built And Validated Module By Module.
3. [DeliveryArtifacts/TechnicalDesignDocument.md](DeliveryArtifacts/TechnicalDesignDocument.md) For The New Platform Architecture, Multitenant Model, Domain Boundaries, And Integration Strategy.
4. [DeliveryArtifacts/McpAgentIntegrationStrategy.md](DeliveryArtifacts/McpAgentIntegrationStrategy.md) For The AI Boundary, MCP Exposure Model, Security Rules, And Agent Access Design.
5. Architecture Overview And Domain Blueprint Documents For Current-State Truth And Domain-Level Design Guidance.
6. Workflow Intelligence Documents For Real Usage Evidence That Helps Prioritize The New Build.

## Documentation Categories

| Category | What It Answers |
| --- | --- |
| Delivery Artifacts | What Is Being Built, In What Order, With What Quality Gates |
| Architecture Overview | What The Current Repository Really Does And What Structural Problems Must Be Removed |
| Domain Blueprints | What Each Domain Must Preserve And How It Should Be Rebuilt In The New Platform |
| Workflow Intelligence Reports | What Real Usage Data Says About Current Business Priority |
| AI First Principles | How To Use AI To Build The New Platform Safely Without Embedding AI Logic Inside Core ERP Flows |

## Current System Summary

| Dimension | Current State |
| --- | --- |
| Runtime Model | Django Monolith With Shared App Boundaries |
| Primary Data Store | PostgreSQL |
| Async Processing | Celery Workers And Celery Beat With Redis |
| UI Model | Django Templates, Form Posts, JSON APIs, JWT Endpoints |
| Core Business Domains | People Operations, Delivery, Work Tracking, Payroll, Revenue, Documentation, Assessments, Talent |
| Integration Style | Direct View-Level Calls, Task Files, Shared Model Access |
| Access Model | Django Auth, Groups, Department Membership, Project Membership, Decorator-Led Checks |
| Multitenancy Reality | No True Tenant Isolation Yet |

## Target Platform Summary

| Dimension | Target Direction |
| --- | --- |
| Build Model | Greenfield Rebuild Of The Current Intranet Capability Set |
| Tenancy Model | True Multitenant Platform With Tenant-Aware Identity, Workspace, And Domain Records |
| Frontend | New Designed Product Experience Across All Major Modules |
| Backend | API-First Domain Platform With Clean Module Boundaries |
| AI Strategy | External AI Agents Connect Through MCP-Compatible APIs; No Embedded AI-Decision Core Inside ERP |
| Migration Model | Legacy System Used As Discovery And Migration Source Until Cutover |

## Documentation Map

| Document | Purpose |
| --- | --- |
| [DeliveryArtifacts/StatementOfWork.md](DeliveryArtifacts/StatementOfWork.md) | Canonical Scope, Full Rebuild Intent, And Delivery Boundaries |
| [DeliveryArtifacts/TestDrivenDevelopmentPlan.md](DeliveryArtifacts/TestDrivenDevelopmentPlan.md) | Canonical Test-First Build And Validation Strategy For The New Intranet |
| [DeliveryArtifacts/TechnicalDesignDocument.md](DeliveryArtifacts/TechnicalDesignDocument.md) | Canonical Technical Architecture For The New Multitenant Platform |
| [DeliveryArtifacts/McpAgentIntegrationStrategy.md](DeliveryArtifacts/McpAgentIntegrationStrategy.md) | Canonical AI Boundary And MCP Exposure Strategy |
| [DeliveryArtifacts/AIAgenticArchitectureDiscoveryAnswerPack.md](DeliveryArtifacts/AIAgenticArchitectureDiscoveryAnswerPack.md) | Repo-Grounded Discovery Facts And Historical AI-Vision Analysis |
| [ArchitectureOverview/SystemLandscape.md](ArchitectureOverview/SystemLandscape.md) | Current System Structure, Domain Breadth, And Rebuild Implications |
| [ArchitectureOverview/ModuleDependencyMap.md](ArchitectureOverview/ModuleDependencyMap.md) | Current Coupling Hotspots And Required Boundary Cleanup |
| [ArchitectureOverview/InfrastructureAndNetworking.md](ArchitectureOverview/InfrastructureAndNetworking.md) | Current Runtime Topology And Target Infrastructure Direction |
| [ArchitectureOverview/DataFlowAndRuntimeSequences.md](ArchitectureOverview/DataFlowAndRuntimeSequences.md) | Current Major Runtime Flows And Rebuild Rules |
| [ArchitectureOverview/DatabaseSchemaAndEntityBoundaries.md](ArchitectureOverview/DatabaseSchemaAndEntityBoundaries.md) | Schema Discovery Rules, Aggregate Families, And Migration Design Constraints |
| [ArchitectureOverview/PageInventoryAndUiUx.md](ArchitectureOverview/PageInventoryAndUiUx.md) | Current UX Surface Inventory And New UX Rebuild Direction |
| [DomainBlueprints/MultiTenancyAndAccessControl.md](DomainBlueprints/MultiTenancyAndAccessControl.md) | Current Access Reality And Target Multitenant Access Model |
| [DomainBlueprints/ProjectsAndDelivery.md](DomainBlueprints/ProjectsAndDelivery.md) | Delivery Domain Blueprint For The New Project Workspace Product |
| [DomainBlueprints/PaymentsAndPayroll.md](DomainBlueprints/PaymentsAndPayroll.md) | Finance And Payroll Rebuild Blueprint |
| [DomainBlueprints/LmsAndLeadOperations.md](DomainBlueprints/LmsAndLeadOperations.md) | Revenue Domain Truth And Rebuild Direction |
| [DomainBlueprints/KnowledgeAssessmentAndTalentOps.md](DomainBlueprints/KnowledgeAssessmentAndTalentOps.md) | Knowledge, Learning, Talent, And Template Domain Blueprint |
| [WorkflowIntelligenceReports/WorkflowIntelligenceImplementationPlan.md](WorkflowIntelligenceReports/WorkflowIntelligenceImplementationPlan.md) | Current Route-Usage Instrumentation Feature And Why It Matters For Rebuild Prioritization |
| [WorkflowIntelligenceReports/WorkflowIntelligenceRealDataRunbook.md](WorkflowIntelligenceReports/WorkflowIntelligenceRealDataRunbook.md) | How Real Usage Evidence Is Collected And Interpreted |
| [AiFirstPrinciples/DatabaseAndArchitectureFirstAllAiBestPractisesInVibeSolutioning.md](AiFirstPrinciples/DatabaseAndArchitectureFirstAllAiBestPractisesInVibeSolutioning.md) | How AI Should Be Used To Design And Build The New Platform |
| [AiFirstPrinciples/VibeCodingAndAgentSolutioningWithCurrentTechnology.md](AiFirstPrinciples/VibeCodingAndAgentSolutioningWithCurrentTechnology.md) | Safe Vibe-Coding Delivery Model For Building The New Intranet |

## Historical Note

Older Operator-Layer Pilot Artifacts Such As [DeliveryArtifacts/ApprovedForcedExecutionPlan.md](DeliveryArtifacts/ApprovedForcedExecutionPlan.md) And [DeliveryArtifacts/WednesdayToSaturdayDeliveryPlan.md](DeliveryArtifacts/WednesdayToSaturdayDeliveryPlan.md) Are Retained As Historical Phase-Zero References Only. They Are Not The Canonical Plan For The Current Full Rebuild Program.

## Current Application Inventory

- `mainapp` Owns HR Utilities, Leave, Notifications, Credential Flows, Payroll Views, And Offer Workflows.
- `users` Owns Profiles, Departments, Skills, Status, Payments, HRMS Views, And Access-Related Context.
- `project` Owns Project Setup, Team Membership, Milestones, Budgets, Repositories, Documents, Delays, And Anti-Phishing Support.
- `Tasks_dashboard` Owns Tasks, EOD, Slack Mappings, And ClickUp Mappings.
- `lms` Owns BA Workload, Lead Analytics, Performance Views, And Lead Dashboards.
- `banao` Owns Operational CRM Flow, Lead Notes, Proposal Links, Audit Links, And Workflow History.
- `atg_docs` Owns Knowledge Publishing And Google-Backed Documentation Flow.
- `assesment` Owns Assessment Templates, Assignments, And Completion Tracking.
- `l3` Owns Recruitment, College Tracking, Internship Utilities, And Talent Performance Views.
- `Github_extension`, `Html_template`, And `git` Support Delivery, Offer Rendering, And Repository-Related Utilities.

## Reading Paths By Question

- For Full Rebuild Scope: Start With [DeliveryArtifacts/StatementOfWork.md](DeliveryArtifacts/StatementOfWork.md).
- For Build Execution Discipline: Start With [DeliveryArtifacts/TestDrivenDevelopmentPlan.md](DeliveryArtifacts/TestDrivenDevelopmentPlan.md).
- For New Platform Architecture: Start With [DeliveryArtifacts/TechnicalDesignDocument.md](DeliveryArtifacts/TechnicalDesignDocument.md).
- For MCP And AI-Agent Access: Start With [DeliveryArtifacts/McpAgentIntegrationStrategy.md](DeliveryArtifacts/McpAgentIntegrationStrategy.md).
- For Current-System Truth: Start With [ArchitectureOverview/SystemLandscape.md](ArchitectureOverview/SystemLandscape.md) And [ArchitectureOverview/ModuleDependencyMap.md](ArchitectureOverview/ModuleDependencyMap.md).
- For Real Business Priority From Usage: Start With [WorkflowIntelligenceReports/WorkflowIntelligenceImplementationPlan.md](WorkflowIntelligenceReports/WorkflowIntelligenceImplementationPlan.md) And [WorkflowIntelligenceReports/WorkflowIntelligenceRealDataRunbook.md](WorkflowIntelligenceReports/WorkflowIntelligenceRealDataRunbook.md).

## Primary Rebuild Thesis

The New Intranet Should Not Be A Cleaned-Up Copy Of The Existing Monolith. It Should Be A New Multitenant Product Platform That Preserves The Current Domain Breadth, Removes Hidden Coupling, Rebuilds UX Intentionally, Centralizes Access Policy, Normalizes Core Data, And Exposes Secure MCP-Compatible APIs So External AI Agents Can Work With ERP Context Without Embedding Agent Logic Into The ERP Core Itself.
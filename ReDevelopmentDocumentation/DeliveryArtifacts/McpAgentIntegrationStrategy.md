# MCP Agent Integration Strategy

## Purpose

This Document Defines How External AI Agents Will Connect To The New Intranet Through MCP-Compatible APIs Without Embedding AI Runtime Logic Inside Core ERP Transactions.

## Core Principle

The ERP Core Must Remain A Deterministic Business System. AI Agents Are External Clients That Consume Approved Tools And Context Through A Controlled Boundary.

## Architectural Rule

- ERP Owns Business Rules, Data Integrity, Access Policy, And Audit.
- MCP Gateway Owns Tool Exposure, Resource Exposure, Prompt Exposure, And Agent Session Mediation.
- External Agents Own Reasoning And LLM Execution.

## Why MCP Instead Of Embedded AI Logic

- It Prevents Prompt Logic From Becoming Hidden Business Logic.
- It Keeps The Core ERP Provider-Neutral.
- It Allows Multiple Agent Clients To Connect Without Rewriting Domain Rules.
- It Preserves Tenant, Role, And Workspace Security Inside ERP-Owned Policies.

## Target MCP Exposure Model

### Tools

Expose Safe Task-Oriented Actions Such As:

- Get Project Summary.
- Get Lead Timeline.
- Search Knowledge Documents.
- Fetch Payroll Review Context.
- List Workspace Tasks.
- Create Draft Note Or Draft Summary Where Explicitly Allowed.

### Resources

Expose Readable ERP Context Such As:

- Project Metadata.
- Lead Status History.
- Workspace Policy Summaries.
- Knowledge Article Metadata.
- Audit-Friendly Read Models.

### Prompts

Prompts May Be Published As Optional Guidance Artifacts, But They Must Never Replace ERP Validation Rules Or Access Policy.

## Security Model

Every MCP Request Must Resolve:

- Agent Principal Identity.
- Tenant Context.
- Workspace Context.
- Allowed Tool Scope.
- Allowed Resource Scope.
- Audit Logging Requirements.

## Write Path Rules

- Read Access Can Be Broader But Still Tenant-Scoped.
- Write Access Through MCP Must Be Explicitly Allowed Per Action.
- All MCP Writes Must Pass Through The Same ERP Validation And Audit Layers As Human UI Writes.
- No Agent Gets Direct Database Access.

## Multitenancy Rules For MCP

- Tool Discovery Must Be Tenant-Aware.
- Resource Responses Must Never Leak Cross-Tenant Data.
- Integration Credentials Resolved Through MCP Paths Must Respect Tenant And Workspace Ownership.
- Audit Logs Must Include Agent Principal Plus Tenant Scope.

## Example MCP-Ready Domain Surfaces

| Domain | Candidate Tool Surface |
| --- | --- |
| Projects And Delivery | Project Status, Milestone Risk, Team Membership, Document Listing |
| Revenue Operations | Lead Timeline, Assignment Summary, Follow-Up Queue, Opportunity Snapshot |
| People Operations | Employee Lifecycle Summary, Leave Status, Credential Metadata |
| Finance | Payroll Run Summary, Payout Status, Approval Queue Context |
| Knowledge | Search Documents, Get Metadata, List Permissioned Articles |
| Talent | Candidate Summary, Assignment Status, Performance Snapshot |

## Non-Goals

- No Generic Embedded Agent Framework Inside ERP.
- No LLM Provider Lock-In Inside Domain Modules.
- No Prompt Chains Hidden In Controllers Or Model Methods.
- No Agent Logic That Bypasses Domain Validation.

## Delivery Order

1. Build Stable ERP Domain APIs First.
2. Build Tenant-Aware Auth And Access First.
3. Publish Read-Only MCP Tools First.
4. Publish Controlled Drafting Or Mutation Tools Later Under Explicit Approval.

## Final MCP Rule

AI Must Consume ERP Capability Through Contracts, Not Through Hidden Backdoors. If An Agent Can Do Something A Human Cannot Audit, Scope, Or Revoke, Then The MCP Design Has Failed.
# Page Inventory And Uiux

## Current UX Shape

The Existing Product Uses Server-Rendered Django Templates With Shared Layouts, Sidebars, Form Pages, Tables, Dashboards, And Modal-Heavy Project Screens. It Is Functionally Rich But Structurally Uneven. The New Intranet Must Preserve Capability Breadth While Rebuilding The Product Experience Deliberately.

## Current UX Problems That Must Not Be Carried Forward

- Read, Write, Approval, And Integration Side Effects Often Sit On The Same Screen.
- Persona Navigation Is Implicit Rather Than Explicit.
- Large Context Dictionaries Power Too Many Screens.
- Tables, Filters, Empty States, And Error States Are Not Standardized.
- Cross-domain Context Exists, But It Is Not Presented In A Product-Coherent Way.

## Target UX System

### Core Product Principles

- Every Major Domain Gets A Workbench, Not A Pile Of Pages.
- Tenant And Workspace Context Must Be Visible In Navigation And Access.
- High-Context Entities Use Timeline And Detail Views.
- Actions Are Separate From Analytics Where Possible.
- Integrations, Audit, And Status Must Be Visible Where Side Effects Matter.

### Primary Workbench Areas

| Workbench | Primary Persona |
| --- | --- |
| Home | Employee, Manager |
| People Ops | HR, Manager |
| Payroll | Finance, HR |
| Projects | Project Manager, Delivery Lead |
| Work | Team Lead, Individual Contributor |
| Revenue | BA, Sales, Revenue Ops |
| Knowledge | Documentation Author, Employee |
| Learning | Compliance And Assessment Users |
| Talent | Recruiter, Internship Ops |
| Admin And Integrations | Platform And Security Owners |

## Current Screen Inventory To Preserve Functionally

### Employee And Manager Core

- Home Dashboard Must Become A Personalized Workbench.
- Profile Detail And Edit Must Become Structured, Audit-Friendly Profile Centers.
- Hierarchy Must Become A Searchable Org Explorer.
- Documentation Landing Must Merge Into The Dedicated Knowledge Product Area.

### Payroll And Finance

- Manage Payroll Must Become A Review Queue.
- Finance Payments Must Separate Review From Payout Execution.
- Employee Payments And Payslips Must Become A Self-Service Payroll Center.
- Bank Details Must Include Verification And Sensitive Data Masking.

### People Operations

- Leave List, Form, And Calendar Must Become A Unified Leave Experience.
- Track My Reportee Must Become A Manager Cockpit.
- Offer Generation Must Become A Guided Onboarding Wizard.
- Credential Vault Must Become A Secure Audited Product Surface.

### Project And Delivery

- Project Onboarding Must Become A Guided Wizard.
- Project Dashboard Must Be Rebuilt As A Flagship Workspace With Overview, Timeline, Team, Work, Documents, Repositories, Risks, And Compliance.
- Task Dashboard Must Become A Consistent Work Management Surface.

### Revenue And LMS

- LMS Landing And Dashboard Must Become Revenue Workbenches.
- Lead Detail Must Become A Timeline-Based CRM Detail Screen.
- Add Lead Must Be Split Between Capture And Qualification.
- Banao And LMS UX Must Merge Into One Revenue Product Surface.

### Knowledge, Learning, And Talent

- Docs Home Must Gain Search, Ownership, Recency, And Permission Signals.
- Assessment Views Must Become A Compliance And Learning Center.
- l3 Surfaces Must Become Separate Talent Workflow Boards And Analytics.

## New UX Requirements For The Rebuild

- Shared Design Tokens, Typography, Layout, And Interaction Rules.
- Consistent Filter, Search, Table, Empty-State, Error-State, And Timeline Components.
- Responsive Layouts For Desktop And Mobile Review Paths.
- Clear Support For Tenant, Business Unit, And Workspace Switching Where Allowed.
- Optional AI Assistant Panels Must Be Contextual Helpers Through MCP, Not Core Workflow Dependencies.

## UI First Rule For The Rebuild

Every Screen In The New Product Must Answer Three Questions Immediately: What Is Happening, What Needs Attention, And What Can This Persona Do Next. If A Screen Still Forces Users To Reconstruct Context From Multiple Legacy Patterns, The UX Rebuild Has Failed.
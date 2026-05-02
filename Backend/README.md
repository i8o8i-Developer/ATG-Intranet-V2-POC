# Backend

This Folder Is The Isolated Backend-First Rebuild Scaffold For The New Intranet ERP. It Does Not Modify The Legacy Django Apps Or Frontend Templates.

## Design Rules

- Every Business Record Is Tenant-Aware From The Start.
- React And Future Frontend Clients Consume APIs Only; Templates Are Not Part Of This Backend Layer.
- Domains Expose Explicit Serializers, Viewsets, Services, And Routes.
- Cross-Domain Writes Should Happen Through Services Or Events, Not Direct Table Mutation.
- External Systems And AI Agents Connect Through IntegrationHub And McpAccessLayer Contracts.

## Current Legacy App Coverage

| Legacy App | New PascalCase Backend App | Target Ownership |
| --- | --- | --- |
| users | Users | Identity-Adjacent Employee Profile, Skills, Departments, Status |
| mainapp | MainApp | Notifications, Onboarding, Leave, Credentials, Shared Operations |
| project | Project | Delivery Projects, Milestones, Repositories, Documents, Risk |
| Tasks_dashboard | TasksDashboard | Work Items, EOD, Activities, ClickUp And Slack Work Signals |
| banao | Banao | Revenue Leads, Proposals, Audits, Workflow History |
| lms | Lms | Sales/Revenue Learning And Performance Views |
| atg_docs | AtgDocs | Knowledge Documents And Permissions |
| assesment | Assesment | Assessment Templates, Assignments, Submissions |
| l3 | L3 | College And Talent Pipeline Operations |
| Github_extension | GithubExtension | GitHub Branch Review And Testing Workflow |
| git | Git | Git Utility/Read Model Workflows |
| Html_template | HtmlTemplate | Reusable HTML And Offer Templates |
| workflow_intelligence | WorkflowIntelligence | Route/Workflow Analytics Read Models |

## Platform Apps Added For The Rebuild

- EnterpriseCore: Tenancy, Workspace, Access, Audit, Outbox, Shared API Primitives.
- FinanceAndPayroll: Payroll, Compensation, Payouts, Bank Details, Payslips.
- IntegrationHub: Provider Connections, Webhook Intake, Adapter Calls, Sync Jobs.
- McpAccessLayer: MCP Tools, Resources, Grants, Invocation Audit, Controlled Agent Drafts.
- LegacyBridge: Migration Crosswalks And Old-To-New Module Mapping.

## API Mounting

The API Root Is `Backend.ApiUrls`. It Is Intentionally Separate From The Legacy `Intranet.urls` Until The New Backend Is Ready To Be Registered Behind A Versioned Route Such As `/api/v2/`.

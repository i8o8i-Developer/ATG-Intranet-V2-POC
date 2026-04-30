# Backend

This folder is the isolated backend-first rebuild scaffold for the new intranet ERP. It does not modify the legacy Django apps or frontend templates.

## Design Rules

- Every business record is tenant-aware from the start.
- React and future frontend clients consume APIs only; templates are not part of this backend layer.
- Domains expose explicit serializers, viewsets, services, and routes.
- Cross-domain writes should happen through services or events, not direct table mutation.
- External systems and AI agents connect through IntegrationHub and McpAccessLayer contracts.

## Current Legacy App Coverage

| Legacy App | New PascalCase Backend App | Target Ownership |
| --- | --- | --- |
| users | Users | Identity-adjacent employee profile, skills, departments, status |
| mainapp | MainApp | Notifications, onboarding, leave, credentials, shared operations |
| project | Project | Delivery projects, milestones, repositories, documents, risk |
| Tasks_dashboard | TasksDashboard | Work items, EOD, activities, ClickUp and Slack work signals |
| banao | Banao | Revenue leads, proposals, audits, workflow history |
| lms | Lms | Sales/revenue learning and performance views |
| atg_docs | AtgDocs | Knowledge documents and permissions |
| assesment | Assesment | Assessment templates, assignments, submissions |
| l3 | L3 | College and talent pipeline operations |
| Github_extension | GithubExtension | GitHub branch review and testing workflow |
| git | Git | Git utility/read model workflows |
| Html_template | HtmlTemplate | Reusable HTML and offer templates |
| workflow_intelligence | WorkflowIntelligence | Route/workflow analytics read models |

## Platform Apps Added For The Rebuild

- EnterpriseCore: tenancy, workspace, access, audit, outbox, shared API primitives.
- FinanceAndPayroll: payroll, compensation, payouts, bank details, payslips.
- IntegrationHub: provider connections, webhook intake, adapter calls, sync jobs.
- McpAccessLayer: MCP tools, resources, grants, invocation audit, controlled agent drafts.
- LegacyBridge: migration crosswalks and old-to-new module mapping.

## API Mounting

The API root is `Backend.ApiUrls`. It is intentionally separate from the legacy `Intranet.urls` until the new backend is ready to be registered behind a versioned route such as `/api/v2/`.

# MCP Access Layer - AI-First ERP Integration

## Overview

The MCP (Model Context Protocol) Access Layer provides a secure, tenant-aware interface for AI agents to interact with the ERP system. It implements a tool-based architecture where each business operation is exposed as a discrete, audited, and permission-controlled tool.

## Architecture

```
AI Agent
   ↓
MCP Client (OpenCode, Claude Desktop, etc.)
   ↓
MCP Server (HTTP/WebSocket API)
   ↓
MCP Tools (Business Operations)
   ↓
Service Layer (Business Logic)
   ↓
Database (Tenant-scoped)
```

## Key Features

✅ **Multi-tenant by design**: All operations are tenant-scoped  
✅ **Permission-based**: RBAC enforced at tool level  
✅ **Fully audited**: All invocations logged with input/output  
✅ **Type-safe**: JSON schema validation for tool inputs  
✅ **Event-driven**: Integration with outbox pattern  
✅ **Real-time capable**: WebSocket support for streaming  

## Core Models

### AgentPrincipal
Represents an AI agent that can invoke tools.

```python
{
    "name": "Sales Assistant Bot",
    "principal_key": "opencode-agent-123",
    "status": "Active",
    "owner_id": <employee_id>,
    "metadata": {}
}
```

### McpToolDefinition
Defines an available tool with input/output schema.

```python
{
    "name": "List Employees",
    "slug": "list_employees",
    "owning_module": "McpAccessLayer",
    "description": "List all employees...",
    "input_schema": {...},
    "is_mutating": false,
    "status": "Active"
}
```

### McpAccessGrant
Grants permission for an agent to use a tool or resource.

```python
{
    "agent_id": <agent_id>,
    "tool_id": <tool_id>,
    "permission": "Read",
    "constraints": {"department_id": 5},
    "expires_at": null
}
```

### McpInvocationAudit
Records every tool invocation for compliance.

```python
{
    "agent_id": <agent_id>,
    "tool_id": <tool_id>,
    "action": "Invoke",
    "decision": "Allowed",
    "input_payload": {...},
    "output_payload": {...},
    "reason": ""
}
```

## Available Tools

### 1. list_employees
List all employees with optional filtering.

**Parameters:**
```json
{
    "department_id": 5,
    "status": "Active",
    "has_skill": "Python",
    "limit": 50
}
```

**Response:**
```json
{
    "employees": [
        {
            "id": 123,
            "name": "John Doe",
            "email": "john@company.com",
            "department": "Engineering",
            "position": "Senior Developer",
            "status": "Active",
            "joined_on": "2023-01-15"
        }
    ],
    "count": 1
}
```

### 2. get_employee_details
Get comprehensive details about a specific employee.

**Parameters:**
```json
{
    "employee_id": 123
}
```

**Response:**
```json
{
    "id": 123,
    "name": "John Doe",
    "email": "john@company.com",
    "department": "Engineering",
    "position": "Senior Developer",
    "status": "Active",
    "joined_on": "2023-01-15",
    "skills": [
        {"name": "Python", "category": "Programming", "proficiency_level": "Advanced"}
    ],
    "active_projects": [
        {"project__name": "Project Alpha", "role": "Tech Lead", "joined_on": "2024-01-01"}
    ],
    "recent_leaves": [],
    "leaves_balance": 12.5
}
```

### 3. list_projects
List all projects with optional filtering.

**Parameters:**
```json
{
    "status": "Active",
    "client_name": "Acme Corp",
    "has_team_member_id": 123,
    "limit": 50
}
```

### 4. get_project_details
Get comprehensive details about a specific project.

**Parameters:**
```json
{
    "project_id": 456
}
```

### 5. list_leads
List CRM leads with optional filtering.

**Parameters:**
```json
{
    "status": "ProposalSent",
    "source": "LinkedIn",
    "assigned_to_id": 123,
    "limit": 50
}
```

### 6. get_analytics_summary
Get high-level analytics summary for the tenant.

**Parameters:** None

**Response:**
```json
{
    "tenant": "Acme Corp",
    "workspace": "HQ",
    "timestamp": "2026-05-04T14:30:00Z",
    "employees": {
        "total": 150,
        "active": 145,
        "on_bench": 5,
        "on_notice": 2,
        "exited": 3
    },
    "projects": {
        "total": 45,
        "active": 30,
        "completed": 12,
        "on_hold": 3
    },
    "leads": {
        "total": 200,
        "new": 50,
        "engaged": 80,
        "proposal_sent": 30,
        "won": 25,
        "lost": 15
    },
    "payroll": {
        "runs_this_month": 1,
        "pending_approval": 0,
        "approved": 1
    }
}
```

### 7. list_notifications
List recent notifications for a user.

**Parameters:**
```json
{
    "user_id": 123,
    "unread_only": true,
    "limit": 20
}
```

### 8. search
Universal search across employees, projects, and leads.

**Parameters:**
```json
{
    "query": "john",
    "search_in": ["employees", "projects", "leads"]
}
```

## Setup & Usage

### 1. Bootstrap MCP Tools

```bash
python manage.py bootstrap_mcp_tools --tenant=acme-corp --workspace=hq
```

This creates McpToolDefinition records for all available tools.

### 2. Create Agent Principal

```bash
# Via API
POST /api/mcp/agents/
{
    "name": "OpenCode Assistant",
    "principal_key": "opencode-unique-key",
    "status": "Active"
}
```

### 3. Grant Permissions

```bash
# Via API
POST /api/mcp/access-grants/
{
    "agent_id": <agent_id>,
    "tool_id": <tool_id>,
    "permission": "Read"
}
```

### 4. Invoke Tools

#### Via API (HTTP):

```bash
POST /api/mcp/tools/<tool_id>/invoke/
Headers:
    X-Tenant-Id: <tenant_id>
    X-Workspace-Id: <workspace_id>
    Authorization: Basic <base64_credentials>
Body:
{
    "params": {
        "department_id": 5,
        "status": "Active"
    },
    "agent_id": <agent_id>
}
```

#### Via MCP Server (Python):

```python
from Backend.Apps.McpAccessLayer.mcp_server import mcp_server

result = mcp_server.invoke_tool(
    context,
    tool_name="list_employees",
    params={"department_id": 5, "status": "Active"}
)

if result.ok:
    print(result.data)
else:
    print(result.errors)
```

## Security

### Permission Model

1. **Agent Principal** must exist and be Active
2. **Access Grant** must link agent to tool
3. **Tenant Context** must match
4. **Invocation** is audited with full I/O

### Example Access Grant:

```python
{
    "agent": <sales_bot>,
    "tool": <list_leads>,
    "permission": "Read",
    "constraints": {
        "assigned_to_id": <current_user_id>  # Can only see own leads
    },
    "expires_at": "2026-12-31T23:59:59Z"
}
```

### Audit Trail

All invocations are recorded:

```sql
SELECT
    agent.name,
    tool.slug,
    audit.action,
    audit.decision,
    audit.created_at
FROM mcp_invocation_audit audit
JOIN mcp_agent_principal agent ON agent.id = audit.agent_id
JOIN mcp_tool_definition tool ON tool.id = audit.tool_id
WHERE audit.tenant_id = <tenant_id>
ORDER BY audit.created_at DESC
LIMIT 100;
```

## Extending with Custom Tools

### 1. Create Tool Class

```python
from Backend.Apps.McpAccessLayer.mcp_server import McpTool

class MyCustomTool(McpTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Does something amazing",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "..."}
                },
                "required": ["param1"]
            },
            is_mutating=False
        )
    
    def execute(self, context, params):
        # Your logic here
        result = do_something(params["param1"])
        return ServiceResult.success(result)
```

### 2. Register Tool

```python
from Backend.Apps.McpAccessLayer.mcp_server import MCP_TOOLS_REGISTRY

MCP_TOOLS_REGISTRY["my_custom_tool"] = MyCustomTool()
```

### 3. Re-run Bootstrap

```bash
python manage.py bootstrap_mcp_tools --tenant=acme-corp
```

## Integration with OpenCode

### 1. Add MCP Server to OpenCode

In OpenCode settings, add MCP server:

```json
{
    "mcpServers": {
        "intranet-erp": {
            "url": "http://localhost:8000/api/mcp/",
            "headers": {
                "X-Tenant-Id": "1",
                "X-Workspace-Id": "1",
                "Authorization": "Basic dXNlcjpwYXNz"
            }
        }
    }
}
```

### 2. Use Tools in OpenCode

```
User: "Show me all active employees in Engineering"

OpenCode Agent:
1. Invokes: list_employees(department_id=5, status="Active")
2. Formats response
3. Displays: "Here are 25 active employees in Engineering..."
```

## API Endpoints

### Agent Principals
- `GET /api/mcp/agents/` - List agents
- `POST /api/mcp/agents/` - Create agent
- `GET /api/mcp/agents/{id}/` - Get agent
- `PUT /api/mcp/agents/{id}/` - Update agent
- `DELETE /api/mcp/agents/{id}/` - Delete agent
- `POST /api/mcp/agents/{id}/can-invoke/` - Check permission
- `POST /api/mcp/agents/{id}/record-invocation/` - Record audit
- `POST /api/mcp/agents/{id}/draft-action/` - Create draft action

### Tools
- `GET /api/mcp/tools/` - List tool definitions
- `GET /api/mcp/tools/available/` - List available tools from server
- `POST /api/mcp/tools/{id}/invoke/` - Invoke tool

### Access Grants
- `GET /api/mcp/access-grants/` - List grants
- `POST /api/mcp/access-grants/` - Create grant

### Invocation Audits
- `GET /api/mcp/invocation-audits/` - List audits

## Best Practices

1. **Always check permissions** before invoking tools
2. **Use descriptive agent names** for audit clarity
3. **Set expiry dates** on access grants when appropriate
4. **Monitor audit logs** for anomalies
5. **Use workspace constraints** for multi-team tenants
6. **Implement rate limiting** for public-facing agents
7. **Rotate principal keys** regularly
8. **Test tools thoroughly** before granting access

## Monitoring

### Metrics to Track

- Invocations per agent per hour
- Failed invocations (permission denied)
- Tool execution time
- Error rates per tool
- Agent activity patterns

### Alerting

- Failed permission checks > 10/min
- Error rate > 5%
- Execution time > 5s
- Suspicious access patterns

## Troubleshooting

### Tool not found
- Run `bootstrap_mcp_tools` command
- Check tool slug matches registry

### Permission denied
- Verify Access Grant exists
- Check grant hasn't expired
- Confirm tenant/workspace match

### Invocation fails
- Check input schema validation
- Review audit log for details
- Check service layer logs

## Future Enhancements

- [ ] WebSocket support for real-time streaming
- [ ] GraphQL interface for complex queries
- [ ] Tool chaining (one tool calls another)
- [ ] Conditional access grants (time-based, IP-based)
- [ ] Tool usage quotas
- [ ] Custom tool marketplace
- [ ] Auto-generated OpenAPI spec
- [ ] Integration with LangChain, AutoGPT, etc.

## Support

For questions or issues:
- GitHub: https://github.com/your-org/intranet-rebuild
- Email: dev@atg.world
- Slack: #mcp-integration

---

**Version**: 1.0.0  
**Last Updated**: 2026-05-04  
**Author**: ATG Development Team

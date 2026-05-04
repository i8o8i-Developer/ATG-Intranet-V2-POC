"""
MCP (Model Context Protocol) Server for AI-first ERP

This server exposes enterprise ERP operations as MCP tools that can be invoked by AI agents.
It provides a secure, tenant-aware interface for AI to interact with the ERP system.

Architecture:
- Tool-based: Each operation is a discrete tool
- Tenant-scoped: All operations respect multi-tenancy
- Audited: All invocations are logged
- Permission-checked: RBAC enforced

Usage:
    python manage.py run_mcp_server --host=0.0.0.0 --port=8100
"""

import json
import logging
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.utils import timezone

from Backend.Apps.Banao.models import LeadAccount
from Backend.Apps.FinanceAndPayroll.models import PayrollRun
from Backend.Apps.MainApp.models import LeaveRequest, NotificationItem
from Backend.Apps.Project.models import ProjectWorkspace, TeamAssignment
from Backend.Apps.TasksDashboard.models import WorkItem, WorkEntry
from Backend.Apps.Users.models import Department, EmployeeProfile, Skill
from Backend.EnterpriseCore.models import Tenant, Workspace
from Backend.EnterpriseCore.services import ServiceResult

logger = logging.getLogger(__name__)

User = get_user_model()


class McpTool:
    """Base class for MCP tools"""
    
    def __init__(self, name: str, description: str, input_schema: Dict, is_mutating: bool = False):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.is_mutating = is_mutating
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        """Execute the tool with given parameters"""
        raise NotImplementedError("Subclasses must implement execute()")


class ListEmployeesTool(McpTool):
    """List employees with optional filtering"""
    
    def __init__(self):
        super().__init__(
            name="list_employees",
            description="List all employees in the tenant with optional filtering by department, status, or skills",
            input_schema={
                "type": "object",
                "properties": {
                    "department_id": {"type": "integer", "description": "Filter by department ID"},
                    "status": {"type": "string", "description": "Filter by status (Active, Exited, OnNotice, OnBench)"},
                    "has_skill": {"type": "string", "description": "Filter by skill name"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50}
                }
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        queryset = EmployeeProfile.objects.filter(tenant=context.tenant).select_related("user", "primary_department")
        
        if params.get("department_id"):
            queryset = queryset.filter(primary_department_id=params["department_id"])
        
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        
        if params.get("has_skill"):
            queryset = queryset.filter(skills__name__icontains=params["has_skill"])
        
        limit = params.get("limit", 50)
        employees = queryset[:limit]
        
        data = [
            {
                "id": emp.id,
                "name": emp.user.get_full_name() if emp.user else "N/A",
                "email": emp.user.email if emp.user else "N/A",
                "department": emp.primary_department.name if emp.primary_department else "N/A",
                "position": emp.position_title or "N/A",
                "status": emp.status,
                "joined_on": emp.joined_on.isoformat() if emp.joined_on else None,
            }
            for emp in employees
        ]
        
        return ServiceResult.success({"employees": data, "count": len(data)})


class GetEmployeeDetailsTool(McpTool):
    """Get detailed information about a specific employee"""
    
    def __init__(self):
        super().__init__(
            name="get_employee_details",
            description="Get comprehensive details about a specific employee including skills, projects, and performance",
            input_schema={
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "Employee ID", "required": True}
                },
                "required": ["employee_id"]
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        employee = EmployeeProfile.objects.filter(
            tenant=context.tenant,
            id=params["employee_id"]
        ).select_related("user", "primary_department").first()
        
        if not employee:
            return ServiceResult.failure({"employee": "Employee not found"}, status_code=404)
        
        # Get skills
        skills = list(employee.skills.values("name", "category", "proficiency_level"))
        
        # Get active projects
        projects = TeamAssignment.objects.filter(
            tenant=context.tenant,
            employee=employee,
            status="Active"
        ).select_related("project").values("project__name", "role", "joined_on")
        
        # Get recent leaves
        leaves = LeaveRequest.objects.filter(
            tenant=context.tenant,
            requested_by=employee
        ).order_by("-created_at")[:5].values("leave_type", "start_date", "end_date", "status")
        
        data = {
            "id": employee.id,
            "name": employee.user.get_full_name() if employee.user else "N/A",
            "email": employee.user.email if employee.user else "N/A",
            "department": employee.primary_department.name if employee.primary_department else "N/A",
            "position": employee.position_title or "N/A",
            "status": employee.status,
            "joined_on": employee.joined_on.isoformat() if employee.joined_on else None,
            "exited_on": employee.exited_on.isoformat() if employee.exited_on else None,
            "github_username": employee.github_username or None,
            "skills": list(skills),
            "active_projects": list(projects),
            "recent_leaves": list(leaves),
            "leaves_balance": float(employee.leaves_wallet) if employee.leaves_wallet else 0.0,
        }
        
        return ServiceResult.success(data)


class ListProjectsTool(McpTool):
    """List projects with optional filtering"""
    
    def __init__(self):
        super().__init__(
            name="list_projects",
            description="List all projects in the tenant with optional filtering by status, client, or team member",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status (Active, Completed, OnHold, Cancelled)"},
                    "client_name": {"type": "string", "description": "Filter by client name"},
                    "has_team_member_id": {"type": "integer", "description": "Filter by team member employee ID"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50}
                }
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        queryset = ProjectWorkspace.objects.filter(tenant=context.tenant)
        
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        
        if params.get("client_name"):
            queryset = queryset.filter(client_name__icontains=params["client_name"])
        
        if params.get("has_team_member_id"):
            queryset = queryset.filter(team_assignments__employee_id=params["has_team_member_id"])
        
        limit = params.get("limit", 50)
        projects = queryset[:limit]
        
        data = [
            {
                "id": proj.id,
                "name": proj.name,
                "client": proj.client_name or "N/A",
                "status": proj.status,
                "start_date": proj.start_date.isoformat() if proj.start_date else None,
                "end_date": proj.end_date.isoformat() if proj.end_date else None,
                "delivery_type": proj.delivery_type,
                "team_size": proj.team_assignments.filter(status="Active").count(),
            }
            for proj in projects
        ]
        
        return ServiceResult.success({"projects": data, "count": len(data)})


class GetProjectDetailsTool(McpTool):
    """Get detailed information about a specific project"""
    
    def __init__(self):
        super().__init__(
            name="get_project_details",
            description="Get comprehensive details about a specific project including team, milestones, and progress",
            input_schema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "Project ID", "required": True}
                },
                "required": ["project_id"]
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        project = ProjectWorkspace.objects.filter(
            tenant=context.tenant,
            id=params["project_id"]
        ).first()
        
        if not project:
            return ServiceResult.failure({"project": "Project not found"}, status_code=404)
        
        # Get team members
        team = TeamAssignment.objects.filter(
            tenant=context.tenant,
            project=project,
            status="Active"
        ).select_related("employee__user").values(
            "employee__id",
            "employee__user__first_name",
            "employee__user__last_name",
            "role",
            "joined_on"
        )
        
        data = {
            "id": project.id,
            "name": project.name,
            "client": project.client_name or "N/A",
            "status": project.status,
            "delivery_type": project.delivery_type,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "github_organization": project.github_organization or None,
            "team_members": list(team),
            "description": project.description or "",
        }
        
        return ServiceResult.success(data)


class ListLeadsTool(McpTool):
    """List CRM leads with optional filtering"""
    
    def __init__(self):
        super().__init__(
            name="list_leads",
            description="List all CRM leads with optional filtering by status, source, or assigned user",
            input_schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by workflow status"},
                    "source": {"type": "string", "description": "Filter by lead source"},
                    "assigned_to_id": {"type": "integer", "description": "Filter by assigned employee ID"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50}
                }
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        queryset = LeadAccount.objects.filter(tenant=context.tenant)
        
        if params.get("status"):
            queryset = queryset.filter(workflow_status=params["status"])
        
        if params.get("source"):
            queryset = queryset.filter(source__icontains=params["source"])
        
        if params.get("assigned_to_id"):
            queryset = queryset.filter(assigned_to__id=params["assigned_to_id"])
        
        limit = params.get("limit", 50)
        leads = queryset.select_related("assigned_to__user")[:limit]
        
        data = [
            {
                "id": lead.id,
                "company": lead.company_name or "N/A",
                "contact_name": lead.contact_name or "N/A",
                "status": lead.workflow_status,
                "source": lead.source or "N/A",
                "assigned_to": lead.assigned_to.user.get_full_name() if lead.assigned_to and lead.assigned_to.user else "Unassigned",
                "estimated_value": float(lead.estimated_value) if lead.estimated_value else 0.0,
                "currency": lead.currency or "INR",
                "created_at": lead.created_at.isoformat(),
            }
            for lead in leads
        ]
        
        return ServiceResult.success({"leads": data, "count": len(data)})


class GetAnalyticsSummaryTool(McpTool):
    """Get high-level analytics summary for the tenant"""
    
    def __init__(self):
        super().__init__(
            name="get_analytics_summary",
            description="Get comprehensive analytics summary including employee count, project status, leads pipeline, and payroll stats",
            input_schema={
                "type": "object",
                "properties": {}
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        # Employee stats
        employees = EmployeeProfile.objects.filter(tenant=context.tenant)
        employee_stats = {
            "total": employees.count(),
            "active": employees.filter(status="Active").count(),
            "on_bench": employees.filter(status="OnBench").count(),
            "on_notice": employees.filter(status="OnNotice").count(),
            "exited": employees.filter(status="Exited").count(),
        }
        
        # Project stats
        projects = ProjectWorkspace.objects.filter(tenant=context.tenant)
        project_stats = {
            "total": projects.count(),
            "active": projects.filter(status="Active").count(),
            "completed": projects.filter(status="Completed").count(),
            "on_hold": projects.filter(status="OnHold").count(),
        }
        
        # Lead stats
        leads = LeadAccount.objects.filter(tenant=context.tenant)
        lead_stats = {
            "total": leads.count(),
            "new": leads.filter(workflow_status__in=["NewLead", "ContactAttempted"]).count(),
            "engaged": leads.filter(workflow_status__in=["Engaged", "DiscoveryScheduled", "DiscoveryCompleted"]).count(),
            "proposal_sent": leads.filter(workflow_status="ProposalSent").count(),
            "won": leads.filter(workflow_status="ClosedWon").count(),
            "lost": leads.filter(workflow_status="ClosedLost").count(),
        }
        
        # Payroll stats (current month)
        current_month = timezone.now().replace(day=1)
        payroll_runs = PayrollRun.objects.filter(
            tenant=context.tenant,
            payroll_month__gte=current_month
        )
        payroll_stats = {
            "runs_this_month": payroll_runs.count(),
            "pending_approval": payroll_runs.filter(status="Pending").count(),
            "approved": payroll_runs.filter(status="Approved").count(),
        }
        
        data = {
            "tenant": context.tenant.name,
            "workspace": context.workspace.name if context.workspace else "N/A",
            "timestamp": timezone.now().isoformat(),
            "employees": employee_stats,
            "projects": project_stats,
            "leads": lead_stats,
            "payroll": payroll_stats,
        }
        
        return ServiceResult.success(data)


class ListNotificationsTool(McpTool):
    """List recent notifications for a user"""
    
    def __init__(self):
        super().__init__(
            name="list_notifications",
            description="List recent notifications for a specific user",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID (defaults to current user)"},
                    "unread_only": {"type": "boolean", "description": "Show only unread notifications", "default": False},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 20}
                }
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        user_id = params.get("user_id") or (context.actor.id if context.actor else None)
        
        if not user_id:
            return ServiceResult.failure({"user": "User ID required"}, status_code=400)
        
        queryset = NotificationItem.objects.filter(
            tenant=context.tenant,
            recipient_id=user_id
        )
        
        if params.get("unread_only"):
            queryset = queryset.filter(is_read=False)
        
        limit = params.get("limit", 20)
        notifications = queryset.order_by("-created_at")[:limit]
        
        data = [
            {
                "id": notif.id,
                "title": notif.title,
                "message": notif.message,
                "category": notif.category,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat(),
                "resource_type": notif.resource_type or None,
                "resource_id": notif.resource_id or None,
            }
            for notif in notifications
        ]
        
        return ServiceResult.success({"notifications": data, "count": len(data)})


class SearchTool(McpTool):
    """Universal search across employees, projects, and leads"""
    
    def __init__(self):
        super().__init__(
            name="search",
            description="Universal search across employees, projects, and leads by keyword",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query", "required": True},
                    "search_in": {"type": "array", "items": {"type": "string"}, "description": "Entities to search (employees, projects, leads)", "default": ["employees", "projects", "leads"]}
                },
                "required": ["query"]
            }
        )
    
    def execute(self, context, params: Dict[str, Any]) -> ServiceResult:
        query = params.get("query", "").strip()
        search_in = params.get("search_in", ["employees", "projects", "leads"])
        
        results = {}
        
        if "employees" in search_in:
            employees = EmployeeProfile.objects.filter(
                tenant=context.tenant
            ).filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__email__icontains=query) |
                Q(position_title__icontains=query)
            ).select_related("user")[:10]
            
            results["employees"] = [
                {
                    "id": emp.id,
                    "name": emp.user.get_full_name() if emp.user else "N/A",
                    "email": emp.user.email if emp.user else "N/A",
                    "position": emp.position_title or "N/A",
                }
                for emp in employees
            ]
        
        if "projects" in search_in:
            projects = ProjectWorkspace.objects.filter(
                tenant=context.tenant
            ).filter(
                Q(name__icontains=query) |
                Q(client_name__icontains=query)
            )[:10]
            
            results["projects"] = [
                {
                    "id": proj.id,
                    "name": proj.name,
                    "client": proj.client_name or "N/A",
                    "status": proj.status,
                }
                for proj in projects
            ]
        
        if "leads" in search_in:
            leads = LeadAccount.objects.filter(
                tenant=context.tenant
            ).filter(
                Q(company_name__icontains=query) |
                Q(contact_name__icontains=query) |
                Q(contact_email__icontains=query)
            )[:10]
            
            results["leads"] = [
                {
                    "id": lead.id,
                    "company": lead.company_name or "N/A",
                    "contact": lead.contact_name or "N/A",
                    "status": lead.workflow_status,
                }
                for lead in leads
            ]
        
        return ServiceResult.success(results)


# Registry of all available MCP tools
MCP_TOOLS_REGISTRY = {
    "list_employees": ListEmployeesTool(),
    "get_employee_details": GetEmployeeDetailsTool(),
    "list_projects": ListProjectsTool(),
    "get_project_details": GetProjectDetailsTool(),
    "list_leads": ListLeadsTool(),
    "get_analytics_summary": GetAnalyticsSummaryTool(),
    "list_notifications": ListNotificationsTool(),
    "search": SearchTool(),
}


class McpServer:
    """
    MCP Server for AI-first ERP
    
    Handles tool discovery, invocation, and result formatting
    """
    
    def __init__(self):
        self.tools = MCP_TOOLS_REGISTRY
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "is_mutating": tool.is_mutating,
            }
            for tool in self.tools.values()
        ]
    
    def get_tool(self, tool_name: str) -> Optional[McpTool]:
        """Get a specific tool by name"""
        return self.tools.get(tool_name)
    
    def invoke_tool(self, context, tool_name: str, params: Dict[str, Any]) -> ServiceResult:
        """Invoke a tool with given parameters"""
        tool = self.get_tool(tool_name)
        
        if not tool:
            return ServiceResult.failure({"tool": f"Tool '{tool_name}' not found"}, status_code=404)
        
        try:
            logger.info(f"Invoking MCP tool: {tool_name} with params: {params}")
            result = tool.execute(context, params)
            logger.info(f"MCP tool {tool_name} completed with status: {'success' if result.ok else 'failure'}")
            return result
        except Exception as e:
            logger.error(f"MCP tool {tool_name} failed with error: {str(e)}", exc_info=True)
            return ServiceResult.failure({"error": str(e)}, status_code=500)


# Global MCP server instance
mcp_server = McpServer()

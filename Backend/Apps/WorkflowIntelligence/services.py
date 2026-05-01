from django.db.models import Sum

from Backend.Apps.WorkflowIntelligence.models import RouteUsageAggregate, WorkflowReport
from Backend.EnterpriseCore.services import ServiceResult


class WorkflowInsightService:
    @staticmethod
    def summarize_route_usage(context, start_date=None, end_date=None):
        queryset = RouteUsageAggregate.objects.filter(tenant=context.tenant)
        if start_date:
            queryset = queryset.filter(usage_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(usage_date__lte=end_date)
        rows = queryset.values("workflow_name", "route_pattern", "username").annotate(hit_count=Sum("hit_count")).order_by("workflow_name", "route_pattern")
        return ServiceResult.success(list(rows))

    @staticmethod
    def top_workflows(context, start_date=None, end_date=None, limit=10):
        queryset = RouteUsageAggregate.objects.filter(tenant=context.tenant)
        if start_date:
            queryset = queryset.filter(usage_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(usage_date__lte=end_date)
        rows = list(
            queryset.values("workflow_name")
            .annotate(hit_count=Sum("hit_count"))
            .order_by("-hit_count", "workflow_name")[: int(limit or 10)]
        )
        return ServiceResult.success(rows)

    @staticmethod
    def generate_report(context, title="", start_date=None, end_date=None, report_type="Manual"):
        summary = WorkflowInsightService.summarize_route_usage(context, start_date=start_date, end_date=end_date)
        top_workflows = WorkflowInsightService.top_workflows(context, start_date=start_date, end_date=end_date)
        if not summary.ok:
            return summary
        if not top_workflows.ok:
            return top_workflows
        report_title = title or "Workflow Intelligence Report"
        markdown_lines = [f"# {report_title}", "", "## Top Workflows"]
        for row in top_workflows.data:
            markdown_lines.append(f"- {row['workflow_name']}: {row['hit_count']} hits")
        report = WorkflowReport.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            title=report_title,
            report_type=report_type,
            status="Generated",
            generated_for=f"{start_date or ''}:{end_date or ''}".strip(":"),
            markdown_body="\n".join(markdown_lines),
            data_payload={"summary": summary.data, "top_workflows": top_workflows.data},
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(report, status_code=201)

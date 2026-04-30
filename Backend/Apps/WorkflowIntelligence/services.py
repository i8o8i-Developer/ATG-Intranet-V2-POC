from django.db.models import Sum

from Backend.Apps.WorkflowIntelligence.models import RouteUsageAggregate
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

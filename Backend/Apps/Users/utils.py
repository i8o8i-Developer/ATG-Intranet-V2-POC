from django.db.models import Count, Sum

from Backend.Apps.Users.models import EmployeePaymentSnapshot, EmployeeProfile, UserEffortReport


def summarize_headcount(tenant):
    return list(EmployeeProfile.objects.filter(tenant=tenant, is_active=True).values("status").annotate(count=Count("id")).order_by("status"))


def summarize_effort(tenant, report_month=None, report_year=None):
    queryset = UserEffortReport.objects.filter(tenant=tenant)
    if report_month:
        queryset = queryset.filter(report_month=report_month)
    if report_year:
        queryset = queryset.filter(report_year=report_year)
    return list(queryset.values("employee_id", "report_month", "report_year").annotate(total_effort=Sum("effort_percent")))


def summarize_payments(tenant, month=None, year=None):
    queryset = EmployeePaymentSnapshot.objects.filter(tenant=tenant)
    if month:
        queryset = queryset.filter(month=month)
    if year:
        queryset = queryset.filter(year=year)
    return queryset.aggregate(normal_pay=Sum("normal_pay"), bonus=Sum("bonus"), deduction=Sum("deduction"), bounty=Sum("bounty"))

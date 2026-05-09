import calendar
from datetime import date, timedelta
from django.db.models import Count, Sum

from Backend.Apps.Users.models import EmployeePaymentSnapshot, EmployeeProfile, UserEffortReport


def summarize_headcount(tenant):
    """Summarize Employee Headcount By Status"""
    return list(EmployeeProfile.objects.filter(tenant=tenant, is_active=True).values("status").annotate(count=Count("id")).order_by("status"))


def summarize_effort(tenant, report_month=None, report_year=None):
    """Summarize Effort Reports For A Tenant"""
    queryset = UserEffortReport.objects.filter(tenant=tenant)
    if report_month:
        queryset = queryset.filter(report_month=report_month)
    if report_year:
        queryset = queryset.filter(report_year=report_year)
    return list(queryset.values("employee_id", "report_month", "report_year").annotate(total_effort=Sum("effort_percent")))


def summarize_payments(tenant, month=None, year=None):
    """Summarize Payment Data For A Tenant"""
    queryset = EmployeePaymentSnapshot.objects.filter(tenant=tenant)
    if month:
        queryset = queryset.filter(month=month)
    if year:
        queryset = queryset.filter(year=year)
    return queryset.aggregate(normal_pay=Sum("normal_pay"), bonus=Sum("bonus"), deduction=Sum("deduction"), bounty=Sum("bounty"))


# ============================================================================
# TASK & BOUNTY METRICS - Migrated From Old utils.py
# ============================================================================

def get_grouped_task_metrics(user_ids, start_date=None, end_date=None):
    """
    Calculate Task And Bounty Metrics Grouped By User.
    
    Metrics:
    - BA (Bounties Allocated): All Tasks Allocated In The Period
    - BC (Bounties Completed): All Tasks Completed In The Period
    - Brought Down: Incomplete Tasks Still Assigned By End Of Period
    
    Args:
        user_ids: List Of User IDs To Calculate Metrics For
        start_date: Optional Start Date Filter
        end_date: Optional End Date Filter (Exclusive)
    
    Returns:
        Dictionary Mapping user_id To Metrics dict With:
        - allocated_bounties: Sum Of Bounties For Allocated Tasks
        - allocated_tasks: Count Of Allocated Tasks
        - completed_bounties: Sum Of Bounties For Completed Tasks
        - completed_tasks: Count Of Completed Tasks
        - brought_down_bounties: Sum Of Bounties For Incomplete Tasks
        - brought_down_tasks: Count Of Incomplete Tasks
    """
    # Import Here To Avoid Circular Dependency
    from Backend.Apps.TasksDashboard.models import Task
    
    if not user_ids:
        return {}

    base_queryset = Task.objects.filter(assignee_id__in=user_ids)

    # Allocated Tasks: Created In The Period
    allocated_queryset = base_queryset
    if start_date:
        allocated_queryset = allocated_queryset.filter(created_at__date__gte=start_date)
    if end_date:
        allocated_queryset = allocated_queryset.filter(created_at__date__lt=end_date)

    # Completed Tasks: Marked Completed In The Period
    completed_queryset = base_queryset.filter(status='C', completed_on__isnull=False)
    if start_date:
        completed_queryset = completed_queryset.filter(completed_on__date__gte=start_date)
    if end_date:
        completed_queryset = completed_queryset.filter(completed_on__date__lt=end_date)

    # Brought Down: Incomplete Tasks Created Before Period End
    brought_down_queryset = base_queryset.filter(status='I')
    if end_date:
        brought_down_queryset = brought_down_queryset.filter(created_at__date__lt=end_date)

    # Initialize Metrics For All Users
    metrics = {
        user_id: {
            'allocated_bounties': 0,
            'allocated_tasks': 0,
            'completed_bounties': 0,
            'completed_tasks': 0,
            'brought_down_bounties': 0,
            'brought_down_tasks': 0,
        }
        for user_id in user_ids
    }

    # Aggregate Allocated Metrics
    for row in allocated_queryset.values('assignee_id').annotate(
        allocated_bounties=Sum('bounty'),
        allocated_tasks=Count('id'),
    ):
        metrics[row['assignee_id']].update({
            'allocated_bounties': row['allocated_bounties'] or 0,
            'allocated_tasks': row['allocated_tasks'] or 0,
        })

    # Aggregate Completed Metrics
    for row in completed_queryset.values('assignee_id').annotate(
        completed_bounties=Sum('bounty'),
        completed_tasks=Count('id'),
    ):
        metrics[row['assignee_id']].update({
            'completed_bounties': row['completed_bounties'] or 0,
            'completed_tasks': row['completed_tasks'] or 0,
        })

    # Aggregate Brought Down Metrics
    for row in brought_down_queryset.values('assignee_id').annotate(
        brought_down_bounties=Sum('bounty'),
        brought_down_tasks=Count('id'),
    ):
        metrics[row['assignee_id']].update({
            'brought_down_bounties': row['brought_down_bounties'] or 0,
            'brought_down_tasks': row['brought_down_tasks'] or 0,
        })

    return metrics


def get_grouped_eod_bounty_metrics(user_ids, start_date=None, end_date=None):
    
    # Import Here To Avoid Circular Dependency
    from Backend.Apps.TasksDashboard.models import EOD
    
    if not user_ids:
        return {}

    queryset = EOD.objects.filter(
        user_id__in=user_ids,
        task__isnull=False,
        task__bounty__gt=0,
        task__assignee_id__in=user_ids,
    )

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lt=end_date)

    # Initialize Metrics
    metrics = {
        user_id: {
            'allocated_bounties': 0,
            'allocated_tasks': 0,
            'completed_bounties': 0,
            'completed_tasks': 0,
            'brought_down_bounties': 0,
            'brought_down_tasks': 0,
        }
        for user_id in user_ids
    }

    # Get Distinct Tasks From EOD Entries
    distinct_task_rows = queryset.values(
        'user_id',
        'task_id',
        'task__bounty',
        'task__status',
    ).distinct()

    # Accumulate Metrics
    for row in distinct_task_rows:
        user_metrics = metrics[row['user_id']]
        bounty = row['task__bounty'] or 0

        # All Tasks In EOD Are "allocated"
        user_metrics['allocated_bounties'] += bounty
        user_metrics['allocated_tasks'] += 1

        # Check If Completed
        if row['task__status'] == 'C':
            user_metrics['completed_bounties'] += bounty
            user_metrics['completed_tasks'] += 1
        else:
            user_metrics['brought_down_bounties'] += bounty
            user_metrics['brought_down_tasks'] += 1

    return metrics


# ============================================================================
# PAYMENT & PAYROLL UTILITIES - Migrated From Old utils.py
# ============================================================================

def get_previous_payment_data(employee_profile, month, year, num_months=3):
    
    payment_data_list = []
    
    for i in range(1, num_months + 1):
        target_month = (month - i) % 12 or 12
        target_year = year if (month - i) > 0 else year - 1
        
        payment_data = EmployeePaymentSnapshot.objects.filter(
            employee=employee_profile,
            month=target_month,
            year=target_year
        ).values()
        
        payment_data_list.extend(payment_data)

    return payment_data_list


def get_ptrc_deduction(normal_pay, bonus):
    
    total_pay = normal_pay + bonus
    return 200 if total_pay >= 25000 else 0


def flatten_leave_dates(leaves):
    
    date_list = []
    for leave in leaves:
        current_date = leave.date_from
        while current_date <= leave.date_to:
            date_list.append(current_date.strftime("%d-%m-%Y"))
            current_date += timedelta(days=1)
    return list(set(date_list))


def calculate_working_days(year, month, start_date=None, end_date=None, exclude_dates=None):
    
    total_days = calendar.monthrange(year, month)[1]
    first_day = date(year, month, 1)
    last_day = date(year, month, total_days)
    
    # Adjust For Employee Start/End Dates
    if start_date and start_date > first_day:
        first_day = start_date
    if end_date and end_date < last_day:
        last_day = end_date
    
    # Calculate Total Days in Range
    working_days = (last_day - first_day).days + 1
    
    # Subtract Excluded Dates (Leaves, Bench, etc.)
    if exclude_dates:
        for exclude_date in exclude_dates:
            if first_day <= exclude_date <= last_day:
                working_days -= 1
    
    return max(0, working_days)


def calculate_prorated_salary(base_salary, working_days, total_days_in_month):
    
    if total_days_in_month == 0:
        return 0
    return (base_salary / total_days_in_month) * working_days


# ============================================================================
# BENCH PERIOD & LEAVE CALCULATIONS
# ============================================================================

def get_bench_days_in_month(employee_profile, year, month):
    
    from Backend.Apps.Users.models import BenchPeriod
    
    first_day = date(year, month, 1)
    total_days = calendar.monthrange(year, month)[1]
    last_day = date(year, month, total_days)
    
    bench_periods = BenchPeriod.objects.filter(
        employee=employee_profile,
        start_date__lte=last_day,
        end_date__gte=first_day
    )
    
    bench_days = 0
    for period in bench_periods:
        period_start = max(period.start_date, first_day)
        period_end = min(period.end_date, last_day) if period.end_date else last_day
        bench_days += (period_end - period_start).days + 1
    
    return bench_days


def get_leave_days_in_month(employee_profile, year, month):
    
    from Backend.Apps.MainApp.models import Leave
    
    first_day = date(year, month, 1)
    total_days = calendar.monthrange(year, month)[1]
    last_day = date(year, month, total_days)
    
    leaves = Leave.objects.filter(
        user=employee_profile.user,
        tenant=employee_profile.tenant,
        status='A',  # Approved
        date_from__lte=last_day,
        date_to__gte=first_day
    )
    
    leave_days = 0
    for leave in leaves:
        leave_start = max(leave.date_from, first_day)
        leave_end = min(leave.date_to, last_day)
        leave_days += (leave_end - leave_start).days + 1
    
    return leave_days

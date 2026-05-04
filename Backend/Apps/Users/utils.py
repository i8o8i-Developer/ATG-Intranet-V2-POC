import calendar
from datetime import date, timedelta
from django.db.models import Count, Sum

from Backend.Apps.Users.models import EmployeePaymentSnapshot, EmployeeProfile, UserEffortReport


def summarize_headcount(tenant):
    """Summarize employee headcount by status"""
    return list(EmployeeProfile.objects.filter(tenant=tenant, is_active=True).values("status").annotate(count=Count("id")).order_by("status"))


def summarize_effort(tenant, report_month=None, report_year=None):
    """Summarize effort reports for a tenant"""
    queryset = UserEffortReport.objects.filter(tenant=tenant)
    if report_month:
        queryset = queryset.filter(report_month=report_month)
    if report_year:
        queryset = queryset.filter(report_year=report_year)
    return list(queryset.values("employee_id", "report_month", "report_year").annotate(total_effort=Sum("effort_percent")))


def summarize_payments(tenant, month=None, year=None):
    """Summarize payment data for a tenant"""
    queryset = EmployeePaymentSnapshot.objects.filter(tenant=tenant)
    if month:
        queryset = queryset.filter(month=month)
    if year:
        queryset = queryset.filter(year=year)
    return queryset.aggregate(normal_pay=Sum("normal_pay"), bonus=Sum("bonus"), deduction=Sum("deduction"), bounty=Sum("bounty"))


# ============================================================================
# TASK & BOUNTY METRICS - Migrated from old utils.py
# ============================================================================

def get_grouped_task_metrics(user_ids, start_date=None, end_date=None):
    """
    Calculate task and bounty metrics grouped by user.
    
    Metrics:
    - BA (Bounties Allocated): All tasks allocated in the period
    - BC (Bounties Completed): All tasks completed in the period
    - Brought Down: Incomplete tasks still assigned by end of period
    
    Args:
        user_ids: List of user IDs to calculate metrics for
        start_date: Optional start date filter
        end_date: Optional end date filter (exclusive)
    
    Returns:
        Dictionary mapping user_id to metrics dict with:
        - allocated_bounties: Sum of bounties for allocated tasks
        - allocated_tasks: Count of allocated tasks
        - completed_bounties: Sum of bounties for completed tasks
        - completed_tasks: Count of completed tasks
        - brought_down_bounties: Sum of bounties for incomplete tasks
        - brought_down_tasks: Count of incomplete tasks
    """
    # Import here to avoid circular dependency
    from Backend.Apps.TasksDashboard.models import Task
    
    if not user_ids:
        return {}

    base_queryset = Task.objects.filter(assignee_id__in=user_ids)

    # Allocated tasks: created in the period
    allocated_queryset = base_queryset
    if start_date:
        allocated_queryset = allocated_queryset.filter(created_at__date__gte=start_date)
    if end_date:
        allocated_queryset = allocated_queryset.filter(created_at__date__lt=end_date)

    # Completed tasks: marked completed in the period
    completed_queryset = base_queryset.filter(status='C', completed_on__isnull=False)
    if start_date:
        completed_queryset = completed_queryset.filter(completed_on__date__gte=start_date)
    if end_date:
        completed_queryset = completed_queryset.filter(completed_on__date__lt=end_date)

    # Brought down: incomplete tasks created before period end
    brought_down_queryset = base_queryset.filter(status='I')
    if end_date:
        brought_down_queryset = brought_down_queryset.filter(created_at__date__lt=end_date)

    # Initialize metrics for all users
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

    # Aggregate allocated metrics
    for row in allocated_queryset.values('assignee_id').annotate(
        allocated_bounties=Sum('bounty'),
        allocated_tasks=Count('id'),
    ):
        metrics[row['assignee_id']].update({
            'allocated_bounties': row['allocated_bounties'] or 0,
            'allocated_tasks': row['allocated_tasks'] or 0,
        })

    # Aggregate completed metrics
    for row in completed_queryset.values('assignee_id').annotate(
        completed_bounties=Sum('bounty'),
        completed_tasks=Count('id'),
    ):
        metrics[row['assignee_id']].update({
            'completed_bounties': row['completed_bounties'] or 0,
            'completed_tasks': row['completed_tasks'] or 0,
        })

    # Aggregate brought down metrics
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
    """
    Calculate EOD-based bounty metrics grouped by user.
    
    This mirrors the bounty calculation used in EOD summary modal.
    Only counts bounty tasks that appear in EOD reports.
    
    Metrics:
    - BA: Count and bounty sum of distinct bounty tasks in EOD for the period
    - BC: Count and bounty sum of those tasks that are completed
    
    Args:
        user_ids: List of user IDs
        start_date: Optional start date filter
        end_date: Optional end date filter (exclusive)
    
    Returns:
        Dictionary mapping user_id to metrics dict
    """
    # Import here to avoid circular dependency
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

    # Initialize metrics
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

    # Get distinct tasks from EOD entries
    distinct_task_rows = queryset.values(
        'user_id',
        'task_id',
        'task__bounty',
        'task__status',
    ).distinct()

    # Accumulate metrics
    for row in distinct_task_rows:
        user_metrics = metrics[row['user_id']]
        bounty = row['task__bounty'] or 0

        # All tasks in EOD are "allocated"
        user_metrics['allocated_bounties'] += bounty
        user_metrics['allocated_tasks'] += 1

        # Check if completed
        if row['task__status'] == 'C':
            user_metrics['completed_bounties'] += bounty
            user_metrics['completed_tasks'] += 1
        else:
            user_metrics['brought_down_bounties'] += bounty
            user_metrics['brought_down_tasks'] += 1

    return metrics


# ============================================================================
# PAYMENT & PAYROLL UTILITIES - Migrated from old utils.py
# ============================================================================

def get_previous_payment_data(employee_profile, month, year, num_months=3):
    """
    Get payment data for previous N months.
    
    Args:
        employee_profile: EmployeeProfile instance
        month: Current month (1-12)
        year: Current year
        num_months: Number of previous months to fetch (default 3)
    
    Returns:
        List of payment data dictionaries
    """
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
    """
    Calculate Professional Tax (PTRC) deduction.
    
    PTRC is ₹200 if total pay >= ₹25,000, else ₹0
    
    Args:
        normal_pay: Base salary amount
        bonus: Bonus amount
    
    Returns:
        PTRC deduction amount
    """
    total_pay = normal_pay + bonus
    return 200 if total_pay >= 25000 else 0


def flatten_leave_dates(leaves):
    """
    Convert leave objects to flat list of dates.
    
    Args:
        leaves: QuerySet or list of Leave objects with date_from and date_to
    
    Returns:
        List of unique date strings in "DD-MM-YYYY" format
    """
    date_list = []
    for leave in leaves:
        current_date = leave.date_from
        while current_date <= leave.date_to:
            date_list.append(current_date.strftime("%d-%m-%Y"))
            current_date += timedelta(days=1)
    return list(set(date_list))


def calculate_working_days(year, month, start_date=None, end_date=None, exclude_dates=None):
    """
    Calculate working days in a month, excluding leaves and bench periods.
    
    Args:
        year: Year
        month: Month (1-12)
        start_date: Optional employee start date
        end_date: Optional employee end date
        exclude_dates: Optional list of dates to exclude (leaves, bench, etc.)
    
    Returns:
        Number of working days
    """
    total_days = calendar.monthrange(year, month)[1]
    first_day = date(year, month, 1)
    last_day = date(year, month, total_days)
    
    # Adjust for employee start/end dates
    if start_date and start_date > first_day:
        first_day = start_date
    if end_date and end_date < last_day:
        last_day = end_date
    
    # Calculate total days in range
    working_days = (last_day - first_day).days + 1
    
    # Subtract excluded dates (leaves, bench, etc.)
    if exclude_dates:
        for exclude_date in exclude_dates:
            if first_day <= exclude_date <= last_day:
                working_days -= 1
    
    return max(0, working_days)


def calculate_prorated_salary(base_salary, working_days, total_days_in_month):
    """
    Calculate prorated salary based on actual working days.
    
    Args:
        base_salary: Monthly base salary
        working_days: Actual working days
        total_days_in_month: Total days in the month
    
    Returns:
        Prorated salary amount
    """
    if total_days_in_month == 0:
        return 0
    return (base_salary / total_days_in_month) * working_days


# ============================================================================
# BENCH PERIOD & LEAVE CALCULATIONS
# ============================================================================

def get_bench_days_in_month(employee_profile, year, month):
    """
    Calculate bench days for an employee in a specific month.
    
    Args:
        employee_profile: EmployeeProfile instance
        year: Year
        month: Month (1-12)
    
    Returns:
        Number of bench days
    """
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
    """
    Calculate leave days for an employee in a specific month.
    
    Args:
        employee_profile: EmployeeProfile instance
        year: Year
        month: Month (1-12)
    
    Returns:
        Number of leave days
    """
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

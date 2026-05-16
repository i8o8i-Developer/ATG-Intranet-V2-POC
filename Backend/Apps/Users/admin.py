from django.contrib import admin

from Backend.Apps.Users import models


@admin.register(models.Domain, models.Department, models.SubDepartment, models.Skill)
class DirectoryAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "name", "is_active", "created_at")
    list_filter = ("tenant", "is_active")
    search_fields = ("name", "code")


@admin.register(models.Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "title", "code", "is_active", "created_at")
    list_filter = ("tenant", "is_active")
    search_fields = ("title", "code")


@admin.register(models.EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "employee_code", "display_name", "department", "position", "slack_username", "status")
    list_filter = ("tenant", "status", "department", "employment_type")
    search_fields = ("employee_code", "display_name", "user__username", "user__email", "github_username", "slack_username")


@admin.register(
    models.DepartmentMembership,
    models.UserSkill,
    models.Goal,
    models.GoalFeedback,
    models.UserStatusSnapshot,
    models.BenchPeriod,
    models.EmployeeRating,
    models.EmployeeCertificate,
    models.EmployeeFeedback,
    models.PayProfile,
    models.EmployeeBankAccount,
    models.EmployeePaymentSnapshot,
    models.LeavePolicy,
    models.LeaveBalance,
    models.LeaveTransaction,
    models.ResignationRequest,
    models.UserEffortReport,
    models.InterviewProgress,
)
class UsersWorkflowAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "is_active", "created_at")
    list_filter = ("tenant", "is_active")

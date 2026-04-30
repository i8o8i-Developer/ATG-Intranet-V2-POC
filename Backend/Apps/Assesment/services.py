from decimal import Decimal

from django.db import models
from django.utils import timezone

from Backend.Apps.Assesment.models import AssessmentActivity, AssessmentAssignment, AssessmentSubmission, AssessmentTemplate
from Backend.Apps.Assesment.provider import ExternalAssessmentProviderClient
from Backend.Apps.Users.models import EmployeeProfile
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class AssessmentTemplateService:
    @staticmethod
    def activate(context, template_id):
        template = AssessmentTemplate.objects.filter(tenant=context.tenant, id=template_id).first()
        if not template:
            return ServiceResult.failure({"template": "Assessment template not found."}, status_code=404)
        template.status = AssessmentTemplate.STATUS_ACTIVE
        template.updated_by = context.actor
        template.save(update_fields=["status", "updated_by", "updated_at"])
        return ServiceResult.success(template)

    @staticmethod
    def archive(context, template_id):
        template = AssessmentTemplate.objects.filter(tenant=context.tenant, id=template_id).first()
        if not template:
            return ServiceResult.failure({"template": "Assessment template not found."}, status_code=404)
        template.status = AssessmentTemplate.STATUS_ARCHIVED
        template.is_active = False
        template.updated_by = context.actor
        template.save(update_fields=["status", "is_active", "updated_by", "updated_at"])
        return ServiceResult.success(template)


class AssessmentAssignmentService:
    @staticmethod
    def assign_to_employee(context, assessment_id, employee_id, due_at=None):
        assessment = AssessmentTemplate.objects.filter(tenant=context.tenant, id=assessment_id, is_active=True).first()
        if not assessment:
            return ServiceResult.failure({"assessment": "Active assessment template not found."}, status_code=404)
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id, is_active=True).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile not found."}, status_code=404)
        assignment = AssessmentAssignment.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            assessment=assessment,
            employee=employee,
            due_at=due_at,
            created_by=context.actor,
            updated_by=context.actor,
        )
        AssessmentActivityService.record(context, assignment, "Assigned", "Assessment assigned")
        OutboxService.publish(context, "AssessmentAssignment", assignment.id, "AssessmentAssigned", {"employeeId": employee.id, "assessmentId": assessment.id})
        return ServiceResult.success(assignment, status_code=201)

    @staticmethod
    def bulk_assign(context, assessment_id, employee_ids, due_at=None):
        assignments = []
        errors = []
        for employee_id in employee_ids:
            result = AssessmentAssignmentService.assign_to_employee(context, assessment_id, employee_id, due_at=due_at)
            if result.ok:
                assignments.append(result.data)
            else:
                errors.append({"employee": employee_id, "errors": result.errors})
        return ServiceResult.success({"created": [item.id for item in assignments], "errors": errors}, status_code=201)

    @staticmethod
    def get_assignment(context, assignment_id):
        assignment = AssessmentAssignment.objects.filter(tenant=context.tenant, id=assignment_id).select_related("assessment", "employee").first()
        if not assignment:
            return None
        return assignment

    @staticmethod
    def start_assignment(context, assignment_id):
        assignment = AssessmentAssignmentService.get_assignment(context, assignment_id)
        if not assignment:
            return ServiceResult.failure({"assignment": "Assessment assignment not found."}, status_code=404)
        if assignment.status in {AssessmentAssignment.STATUS_PASSED, AssessmentAssignment.STATUS_FAILED, AssessmentAssignment.STATUS_CANCELLED}:
            return ServiceResult.failure({"status": "Completed or cancelled assignments cannot be started."}, status_code=409)
        assignment.status = "InProgress"
        assignment.started_at = assignment.started_at or timezone.now()
        assignment.updated_by = context.actor
        assignment.save(update_fields=["status", "started_at", "updated_by", "updated_at"])
        AssessmentActivityService.record(context, assignment, "Started", "Assessment started")
        return ServiceResult.success(assignment)

    @staticmethod
    def record_provider_link(context, assignment_id, external_user_id="", assessment_url="", provider_payload=None):
        assignment = AssessmentAssignmentService.get_assignment(context, assignment_id)
        if not assignment:
            return ServiceResult.failure({"assignment": "Assessment assignment not found."}, status_code=404)
        assignment.external_user_id = external_user_id or assignment.external_user_id
        assignment.assessment_url = assessment_url or assignment.assessment_url
        assignment.provider_payload = provider_payload or assignment.provider_payload
        assignment.status = AssessmentAssignment.STATUS_LINK_GENERATED if assignment.assessment_url else AssessmentAssignment.STATUS_SENT
        assignment.updated_by = context.actor
        assignment.save(update_fields=["external_user_id", "assessment_url", "provider_payload", "status", "updated_by", "updated_at"])
        AssessmentActivityService.record(context, assignment, "ProviderLinkRecorded", "Assessment provider link recorded", assignment.provider_payload)
        return ServiceResult.success(assignment)

    @staticmethod
    def generate_provider_link(context, assignment_id, client=None):
        assignment = AssessmentAssignmentService.get_assignment(context, assignment_id)
        if not assignment:
            return ServiceResult.failure({"assignment": "Assessment assignment not found."}, status_code=404)
        email = assignment.employee.user.email
        if not email:
            return ServiceResult.failure({"employee": "Employee email is required to generate an assessment link."}, status_code=400)
        provider_assessment_id = assignment.assessment.provider_template_id or assignment.assessment.external_id or assignment.assessment.code
        client = client or ExternalAssessmentProviderClient()
        try:
            generated_payload = client.generate_link(email, provider_assessment_id)
            sent_payload = client.send_link(generated_payload)
        except Exception as exc:
            return ServiceResult.failure({"provider": str(exc)}, status_code=502)
        external_user_id = generated_payload.get("user_id") or generated_payload.get("external_user_id") or generated_payload.get("data", {}).get("user_id") or ""
        assessment_url = generated_payload.get("assessment_url") or generated_payload.get("link") or generated_payload.get("url") or ""
        assignment.external_user_id = external_user_id
        assignment.assessment_url = assessment_url
        assignment.provider_payload = {"generated": generated_payload, "sent": sent_payload}
        assignment.status = AssessmentAssignment.STATUS_SENT
        assignment.updated_by = context.actor
        assignment.save(update_fields=["external_user_id", "assessment_url", "provider_payload", "status", "updated_by", "updated_at"])
        AssessmentActivityService.record(context, assignment, "ProviderLinkSent", "Assessment provider link generated and sent", assignment.provider_payload)
        return ServiceResult.success(assignment)

    @staticmethod
    def submit_assignment(context, assignment_id, score=0, percentage=None, answer_payload=None, evaluated_payload=None, provider_attempt_id="", status=""):
        assignment = AssessmentAssignmentService.get_assignment(context, assignment_id)
        if not assignment:
            return ServiceResult.failure({"assignment": "Assessment assignment not found."}, status_code=404)
        if assignment.status == AssessmentAssignment.STATUS_CANCELLED:
            return ServiceResult.failure({"status": "Cancelled assignments cannot be submitted."}, status_code=409)
        score = AssessmentAssignmentService._decimal(score)
        percentage = AssessmentAssignmentService._decimal(percentage if percentage is not None else score)
        passed = percentage >= assignment.assessment.passing_score
        attempt_number = assignment.submissions.count() + 1
        submission = AssessmentSubmission.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            assignment=assignment,
            attempt_number=attempt_number,
            provider_attempt_id=provider_attempt_id,
            score=score,
            percentage=percentage,
            passed=passed,
            status=status or AssessmentAssignment.STATUS_SUBMITTED,
            answer_payload=answer_payload or {},
            evaluated_payload=evaluated_payload or {},
            created_by=context.actor,
            updated_by=context.actor,
        )
        assignment.status = AssessmentAssignment.STATUS_PASSED if passed else AssessmentAssignment.STATUS_FAILED
        assignment.note = "Completed" if passed else "Failed"
        assignment.is_pass = passed
        assignment.score = score
        assignment.percentage = percentage
        assignment.attempts_count = attempt_number
        assignment.submitted_at = submission.submitted_at
        assignment.completed_at = submission.submitted_at
        assignment.updated_by = context.actor
        assignment.save(update_fields=["status", "note", "is_pass", "score", "percentage", "attempts_count", "submitted_at", "completed_at", "updated_by", "updated_at"])
        AssessmentActivityService.record(context, assignment, "Submitted", "Assessment submitted", {"submissionId": submission.id, "passed": passed})
        OutboxService.publish(context, "AssessmentAssignment", assignment.id, "AssessmentSubmitted", {"submissionId": submission.id, "passed": passed})
        return ServiceResult.success(submission, status_code=201)

    @staticmethod
    def sync_provider_status(context, assignment_id, provider_payload):
        assignment = AssessmentAssignmentService.get_assignment(context, assignment_id)
        if not assignment:
            return ServiceResult.failure({"assignment": "Assessment assignment not found."}, status_code=404)
        attempts = provider_payload.get("attempts") or provider_payload.get("assessments", [{}])[0].get("attempts", [])
        assignment.provider_payload = provider_payload
        assignment.last_synced_at = timezone.now()
        if attempts:
            best_percentage = max(AssessmentAssignmentService._decimal(AssessmentAssignmentService._extract_percentage(attempt)) for attempt in attempts)
            assignment.attempts_count = len(attempts)
            assignment.percentage = best_percentage
            assignment.score = best_percentage
            assignment.is_pass = best_percentage >= assignment.assessment.passing_score
            assignment.status = AssessmentAssignment.STATUS_PASSED if assignment.is_pass else AssessmentAssignment.STATUS_FAILED
            assignment.note = "Completed" if assignment.is_pass else "Failed"
            assignment.completed_at = assignment.completed_at or timezone.now()
            assignment.submitted_at = assignment.submitted_at or timezone.now()
        assignment.updated_by = context.actor
        assignment.save(update_fields=["provider_payload", "last_synced_at", "attempts_count", "percentage", "score", "is_pass", "status", "note", "completed_at", "submitted_at", "updated_by", "updated_at"])
        AssessmentActivityService.record(context, assignment, "ProviderStatusSynced", "Assessment provider status synced", provider_payload)
        return ServiceResult.success(assignment)

    @staticmethod
    def _extract_percentage(attempt):
        score_details = attempt.get("score_details") or attempt.get("scoreDetails") or {}
        return score_details.get("total_percentage") or score_details.get("totalPercentage") or attempt.get("percentage") or attempt.get("score") or 0

    @staticmethod
    def _decimal(value):
        if value in (None, ""):
            return Decimal("0")
        return Decimal(str(value))

    @staticmethod
    def mark_overdue(context, assignment_id):
        assignment = AssessmentAssignmentService.get_assignment(context, assignment_id)
        if not assignment:
            return ServiceResult.failure({"assignment": "Assessment assignment not found."}, status_code=404)
        assignment.status = AssessmentAssignment.STATUS_OVERDUE
        assignment.note = "Incomplete"
        assignment.updated_by = context.actor
        assignment.save(update_fields=["status", "note", "updated_by", "updated_at"])
        AssessmentActivityService.record(context, assignment, "Overdue", "Assessment marked overdue")
        return ServiceResult.success(assignment)

    @staticmethod
    def auto_assign_next(context, employee_id):
        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).select_related("department").first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile not found."}, status_code=404)
        latest_assignment = AssessmentAssignment.objects.filter(tenant=context.tenant, employee=employee).select_related("assessment").order_by("-assigned_at").first()
        if latest_assignment and not latest_assignment.is_pass:
            return ServiceResult.failure({"assignment": "Latest assessment is not passed yet."}, status_code=409)
        next_sequence = latest_assignment.assessment.sequence_number + 1 if latest_assignment else 1
        template = AssessmentTemplate.objects.filter(
            tenant=context.tenant,
            department=employee.department,
            sequence_number=next_sequence,
            status=AssessmentTemplate.STATUS_ACTIVE,
            is_active=True,
        ).first()
        if not template:
            return ServiceResult.failure({"assessment": "No next active assessment found for employee department."}, status_code=404)
        return AssessmentAssignmentService.assign_to_employee(context, template.id, employee.id)


class AssessmentQueryService:
    @staticmethod
    def dashboard(context, department_id=None, search="", status="", ordering=""):
        assignments = AssessmentAssignment.objects.filter(tenant=context.tenant).select_related("assessment", "employee", "employee__department")
        if department_id:
            assignments = assignments.filter(employee__department_id=department_id)
        if status:
            assignments = assignments.filter(status=status)
        if search:
            assignments = assignments.filter(models.Q(employee__display_name__icontains=search) | models.Q(employee__employee_code__icontains=search))
        grouped = {}
        for assignment in assignments.order_by("employee_id", "-assigned_at"):
            employee = assignment.employee
            employee_row = grouped.setdefault(
                employee.id,
                {
                    "employee_id": employee.id,
                    "employee_code": employee.employee_code,
                    "employee_name": employee.display_name,
                    "department": employee.department.name if employee.department else "",
                    "assessments": [],
                },
            )
            weeks_since_join = None
            if employee.joined_on:
                weeks_since_join = (assignment.assigned_at.date() - employee.joined_on).days // 7
            employee_row["assessments"].append(
                {
                    "assignment_id": assignment.id,
                    "assessment_id": assignment.assessment_id,
                    "assessment_title": assignment.assessment.title,
                    "sequence_number": assignment.assessment.sequence_number,
                    "status": assignment.status,
                    "note": assignment.note,
                    "is_pass": assignment.is_pass,
                    "percentage": str(assignment.percentage),
                    "assigned_at": assignment.assigned_at.isoformat(),
                    "due_at": assignment.due_at.isoformat() if assignment.due_at else None,
                    "weeks_since_join": weeks_since_join,
                }
            )
        rows = list(grouped.values())
        if ordering == "weeks_since_join":
            rows.sort(key=lambda row: row["assessments"][0].get("weeks_since_join") or 0)
        elif ordering == "status":
            rows.sort(key=lambda row: row["assessments"][0]["status"])
        return ServiceResult.success(rows)

    @staticmethod
    def overdue(context, grace_days=5, as_of=None):
        as_of = as_of or timezone.now()
        cutoff = as_of - timezone.timedelta(days=grace_days)
        assignments = AssessmentAssignment.objects.filter(
            tenant=context.tenant,
            status__in=[AssessmentAssignment.STATUS_ASSIGNED, AssessmentAssignment.STATUS_LINK_GENERATED, AssessmentAssignment.STATUS_SENT, AssessmentAssignment.STATUS_IN_PROGRESS],
        ).filter(models.Q(due_at__lt=as_of) | models.Q(due_at__isnull=True, assigned_at__lte=cutoff))
        return ServiceResult.success(assignments.select_related("assessment", "employee"))

    @staticmethod
    def create_overdue_reminders(context, grace_days=5):
        result = AssessmentQueryService.overdue(context, grace_days=grace_days)
        activities = []
        for assignment in result.data:
            activities.append(
                AssessmentActivityService.record(
                    context,
                    assignment,
                    "ReminderCreated",
                    "Assessment reminder created",
                    {"daysOverdue": max((timezone.now() - assignment.assigned_at).days, 0)},
                )
            )
            OutboxService.publish(context, "AssessmentAssignment", assignment.id, "AssessmentReminderCreated", {"assignmentId": assignment.id})
        return ServiceResult.success({"count": len(activities), "activityIds": [activity.id for activity in activities]})


class AssessmentAutomationService:
    @staticmethod
    def run_assessment_check(context, sync_provider=False, auto_assign_next=True, create_reminders=True, grace_days=5, client=None):
        assignments = AssessmentAssignment.objects.filter(tenant=context.tenant, is_active=True).select_related("assessment", "employee", "workspace")
        provider_synced = 0
        provider_errors = []
        auto_assigned = []
        auto_assign_errors = []

        if sync_provider:
            client = client or ExternalAssessmentProviderClient()
            sync_candidates = assignments.exclude(external_user_id="").filter(
                status__in=[
                    AssessmentAssignment.STATUS_ASSIGNED,
                    AssessmentAssignment.STATUS_LINK_GENERATED,
                    AssessmentAssignment.STATUS_SENT,
                    AssessmentAssignment.STATUS_IN_PROGRESS,
                ]
            )
            for assignment in sync_candidates:
                provider_assessment_id = assignment.assessment.provider_template_id or assignment.assessment.external_id or assignment.assessment.code
                try:
                    payload = client.fetch_status(assignment.external_user_id, provider_assessment_id, assignment.id)
                except Exception as exc:
                    provider_errors.append({"assignment": assignment.id, "error": str(exc)})
                    AssessmentActivityService.record(context, assignment, "ProviderStatusSyncFailed", "Assessment provider status sync failed", {"error": str(exc)})
                    continue
                result = AssessmentAssignmentService.sync_provider_status(context, assignment.id, payload)
                if result.ok:
                    provider_synced += 1
                else:
                    provider_errors.append({"assignment": assignment.id, "error": result.errors})

        if auto_assign_next:
            passed_assignments = AssessmentAssignment.objects.filter(tenant=context.tenant, is_pass=True).select_related("employee", "assessment")
            for assignment in passed_assignments:
                has_next_assignment = AssessmentAssignment.objects.filter(
                    tenant=context.tenant,
                    employee=assignment.employee,
                    assessment__department=assignment.assessment.department,
                    assessment__sequence_number__gt=assignment.assessment.sequence_number,
                ).exists()
                if has_next_assignment:
                    continue
                result = AssessmentAssignmentService.auto_assign_next(context, assignment.employee_id)
                if result.ok:
                    auto_assigned.append(result.data.id)
                elif result.status_code not in {404, 409}:
                    auto_assign_errors.append({"employee": assignment.employee_id, "errors": result.errors})

        reminder_result = ServiceResult.success({"count": 0, "activityIds": []})
        if create_reminders:
            reminder_result = AssessmentQueryService.create_overdue_reminders(context, grace_days=grace_days)

        return ServiceResult.success(
            {
                "providerSynced": provider_synced,
                "providerErrors": provider_errors,
                "autoAssigned": auto_assigned,
                "autoAssignErrors": auto_assign_errors,
                "reminders": reminder_result.data,
            }
        )


class AssessmentActivityService:
    @staticmethod
    def record(context, assignment, activity_type, title, payload=None, message=""):
        return AssessmentActivity.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            assignment=assignment,
            activity_type=activity_type,
            title=title,
            message=message,
            payload=payload or {},
            created_by=context.actor,
            updated_by=context.actor,
        )

from django.db.models import Count
from django.utils import timezone

from Backend.Apps.L3.models import CandidateProfile, CollegeAssignment, CollegeEmailTemplate, CollegePipelineRecord, TalentAssignment, TalentEmail
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class TalentPipelineService:
    @staticmethod
    def import_colleges(context, rows):
        created = []
        for row in rows:
            name = row.get("college_name") or row.get("name")
            if not name:
                continue
            college, _created = CollegePipelineRecord.objects.update_or_create(
                tenant=context.tenant,
                college_name=name,
                defaults={
                    "workspace": context.workspace,
                    "city": row.get("city", ""),
                    "state": row.get("state", ""),
                    "category": row.get("category", ""),
                    "contact_email": row.get("email", row.get("contact_email", "")),
                    "contact_phone": row.get("phone", row.get("contact_phone", "")),
                    "source_system": row.get("source_system", "LegacyL3"),
                    "external_id": str(row.get("external_id", "")),
                    "metadata": row.get("metadata", {}),
                    "updated_by": context.actor,
                },
            )
            created.append(college.id)
        return ServiceResult.success({"count": len(created), "collegeIds": created}, status_code=201)

    @staticmethod
    def assign_candidate(context, candidate_id, employee, assignment_type="Review"):
        candidate = CandidateProfile.objects.filter(tenant=context.tenant, id=candidate_id).first()
        if not candidate:
            return ServiceResult.failure({"candidate": "Candidate not found."}, status_code=404)
        assignment = TalentAssignment.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            candidate=candidate,
            assigned_to=employee,
            assignment_type=assignment_type,
            created_by=context.actor,
        )
        return ServiceResult.success(assignment, status_code=201)

    @staticmethod
    def assign_colleges(context, employee_id, college_ids=None, limit=None, workflow_status="Assigned"):
        from Backend.Apps.Users.models import EmployeeProfile

        employee = EmployeeProfile.objects.filter(tenant=context.tenant, id=employee_id).first()
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile not found."}, status_code=404)
        colleges = CollegePipelineRecord.objects.filter(tenant=context.tenant, is_archived=False)
        if college_ids:
            colleges = colleges.filter(id__in=college_ids)
        else:
            colleges = colleges.filter(assignments__isnull=True).order_by("id")
        if limit:
            colleges = colleges[: int(limit)]
        rows = []
        for college in colleges:
            assignment, _created = CollegeAssignment.objects.update_or_create(
                tenant=context.tenant,
                college=college,
                assigned_to=employee,
                is_archived=False,
                defaults={
                    "workspace": context.workspace or college.workspace,
                    "workflow_status": workflow_status,
                    "assigned_at": timezone.now(),
                    "updated_by": context.actor,
                    "created_by": context.actor,
                },
            )
            college.owner = employee
            college.workflow_status = workflow_status
            college.updated_by = context.actor
            college.save(update_fields=["owner", "workflow_status", "updated_by", "updated_at"])
            rows.append(assignment.id)
        OutboxService.publish(context, "CollegeAssignment", 0, "CollegeBatchAssigned", {"employeeId": employee.id, "count": len(rows)})
        return ServiceResult.success({"count": len(rows), "assignmentIds": rows}, status_code=201)

    @staticmethod
    def update_workflow_status(context, assignment_id=None, college_id=None, workflow_status="Follow up", notes="", follow_up_at=None):
        assignment = None
        if assignment_id:
            assignment = CollegeAssignment.objects.filter(tenant=context.tenant, id=assignment_id).select_related("college").first()
        elif college_id:
            assignment = CollegeAssignment.objects.filter(tenant=context.tenant, college_id=college_id, is_archived=False).select_related("college").order_by("-created_at").first()
        if not assignment:
            return ServiceResult.failure({"assignment": "College assignment not found."}, status_code=404)
        assignment.workflow_status = workflow_status
        assignment.notes = notes or assignment.notes
        assignment.follow_up_at = follow_up_at or assignment.follow_up_at
        if workflow_status in {"Completed", "Data received", "Not interested", "Wrong call"}:
            assignment.completed_at = timezone.now()
        assignment.updated_by = context.actor
        assignment.save(update_fields=["workflow_status", "notes", "follow_up_at", "completed_at", "updated_by", "updated_at"])
        assignment.college.workflow_status = workflow_status
        assignment.college.follow_up_at = assignment.follow_up_at
        assignment.college.updated_by = context.actor
        assignment.college.save(update_fields=["workflow_status", "follow_up_at", "updated_by", "updated_at"])
        OutboxService.publish(context, "CollegeAssignment", assignment.id, "CollegeWorkflowStatusChanged", {"status": workflow_status})
        return ServiceResult.success(assignment)

    @staticmethod
    def send_college_email(context, college_id, template_id=None, subject="", body="", path="", assignment_id=None, live=False):
        college = CollegePipelineRecord.objects.filter(tenant=context.tenant, id=college_id).first()
        if not college:
            return ServiceResult.failure({"college": "College record not found."}, status_code=404)
        template = CollegeEmailTemplate.objects.filter(tenant=context.tenant, id=template_id).first() if template_id else None
        email = TalentEmail.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or college.workspace,
            college=college,
            subject=subject or (template.subject if template else "College outreach"),
            sent_to=college.contact_email,
            status="Sent" if live else "Queued",
            payload={"body": body or (template.body_html if template else ""), "path": path, "dry_run": not live, "assignment_id": assignment_id},
            created_by=context.actor,
            updated_by=context.actor,
        )
        if assignment_id:
            TalentPipelineService.update_workflow_status(context, assignment_id=assignment_id, workflow_status="Email sent")
        else:
            college.workflow_status = "Email sent"
            college.updated_by = context.actor
            college.save(update_fields=["workflow_status", "updated_by", "updated_at"])
        OutboxService.publish(context, "TalentEmail", email.id, "CollegeEmailQueued", {"collegeId": college.id, "dryRun": not live})
        return ServiceResult.success(email, status_code=201)

    @staticmethod
    def performance_summary(context, employee_id=None):
        assignments = CollegeAssignment.objects.filter(tenant=context.tenant, is_archived=False)
        if employee_id:
            assignments = assignments.filter(assigned_to_id=employee_id)
        by_status = list(assignments.values("assigned_to_id", "workflow_status").annotate(count=Count("id")).order_by("assigned_to_id", "workflow_status"))
        email_count = TalentEmail.objects.filter(tenant=context.tenant, college__isnull=False).count()
        return ServiceResult.success({"assignments": by_status, "emailCount": email_count})

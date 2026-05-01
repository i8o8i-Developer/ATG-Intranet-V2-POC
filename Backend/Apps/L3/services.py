from django.db.models import Count
from django.utils import timezone

from Backend.Apps.L3.models import CandidateProfile, CollegeAssignment, CollegeEmailTemplate, CollegePipelineRecord, TalentAssignment, TalentEmail
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class TalentPipelineService:
    @staticmethod
    def _resolve_employee(context, employee_id=None, username=""):
        from Backend.Apps.Users.models import EmployeeProfile

        employees = EmployeeProfile.objects.filter(tenant=context.tenant).select_related("user")
        if employee_id:
            return employees.filter(id=employee_id).first()
        if username:
            return employees.filter(user__username=username).first()
        actor = getattr(context, "actor", None)
        return employees.filter(user=actor).first() if actor else None

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
    def assign_batch_by_username(context, username, limit=10):
        employee = TalentPipelineService._resolve_employee(context, username=username)
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile not found."}, status_code=404)
        return TalentPipelineService.assign_colleges(context, employee.id, limit=limit, workflow_status="Assigned")

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

    @staticmethod
    def list_assignments(context, username="", bucket="new"):
        employee = TalentPipelineService._resolve_employee(context, username=username)
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile not found."}, status_code=404)
        assignments = CollegeAssignment.objects.filter(tenant=context.tenant, assigned_to=employee, is_archived=False).select_related("college", "assigned_to", "assigned_to__user")
        if bucket == "pending":
            assignments = assignments.exclude(workflow_status__in=["Assigned", "New", ""]).filter(completed_at__isnull=True)
        elif bucket == "manager":
            assignments = assignments.filter(workflow_status__in=["Wrong email", "Manager Action", "Data received", "Not interested"])
        elif bucket == "wrong":
            assignments = assignments.filter(workflow_status="Wrong call")
        else:
            assignments = assignments.filter(workflow_status__in=["Assigned", "New", ""])
        rows = [
            {
                "assignment_id": assignment.id,
                "college_id": assignment.college_id,
                "college_name": assignment.college.college_name,
                "workflow_status": assignment.workflow_status,
                "contact_email": assignment.college.contact_email,
                "contact_phone": assignment.college.contact_phone,
                "notes": assignment.notes,
                "is_archived": assignment.is_archived,
            }
            for assignment in assignments.order_by("created_at")
        ]
        return ServiceResult.success({"employee": employee.user.username, "count": len(rows), "rows": rows})

    @staticmethod
    def set_hold_status(context, username, is_paused):
        employee = TalentPipelineService._resolve_employee(context, username=username)
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile not found."}, status_code=404)
        employee.profile_payload = {**employee.profile_payload, "l3_is_paused": bool(is_paused)}
        employee.updated_by = context.actor
        employee.save(update_fields=["profile_payload", "updated_by", "updated_at"])
        return ServiceResult.success({"username": employee.user.username, "is_paused": bool(is_paused)})

    @staticmethod
    def update_college_contact(context, college_id, contact_email="", contact_phone=""):
        college = CollegePipelineRecord.objects.filter(tenant=context.tenant, id=college_id).first()
        if not college:
            return ServiceResult.failure({"college": "College record not found."}, status_code=404)
        update_fields = ["updated_by", "updated_at"]
        if contact_email:
            college.contact_email = contact_email
            update_fields.append("contact_email")
        if contact_phone:
            college.contact_phone = contact_phone
            update_fields.append("contact_phone")
        college.updated_by = context.actor
        if len(update_fields) > 2:
            college.save(update_fields=update_fields)
        return ServiceResult.success(college)

    @staticmethod
    def archive_assignment(context, assignment_id):
        assignment = CollegeAssignment.objects.filter(tenant=context.tenant, id=assignment_id).select_related("college").first()
        if not assignment:
            return ServiceResult.failure({"assignment": "College assignment not found."}, status_code=404)
        assignment.is_archived = True
        assignment.updated_by = context.actor
        assignment.save(update_fields=["is_archived", "updated_by", "updated_at"])
        return ServiceResult.success({"assignment_id": assignment.id, "archived": True, "college_name": assignment.college.college_name})

    @staticmethod
    def performance_list(context, days=7):
        assignments = CollegeAssignment.objects.filter(tenant=context.tenant, is_archived=False, created_at__gte=timezone.now() - timezone.timedelta(days=int(days))).select_related("assigned_to", "assigned_to__user")
        grouped = {}
        for assignment in assignments:
            username = assignment.assigned_to.user.username
            row = grouped.setdefault(username, {"pending_colleges": 0, "completed_colleges": 0})
            if assignment.completed_at:
                row["completed_colleges"] += 1
            else:
                row["pending_colleges"] += 1
        return ServiceResult.success({"day": int(days), "data": grouped})

    @staticmethod
    def performance_detail(context, username):
        employee = TalentPipelineService._resolve_employee(context, username=username)
        if not employee:
            return ServiceResult.failure({"employee": "Employee profile not found."}, status_code=404)
        pending = TalentPipelineService.list_assignments(context, username=username, bucket="pending").data
        manager = TalentPipelineService.list_assignments(context, username=username, bucket="manager").data
        return ServiceResult.success(
            {
                "intern": username,
                "pending_colleges": pending["rows"],
                "pending_colleges_count": pending["count"],
                "manager_colleges": manager["rows"],
                "manager_college_count": manager["count"],
                "intern_obj": {
                    "username": employee.user.username,
                    "display_name": employee.display_name,
                    "is_pause": bool(employee.profile_payload.get("l3_is_paused", False)),
                },
            }
        )

    @staticmethod
    def performance_analytics(context, part_1_day=30, part_2_day=30, part_3_day=30):
        assignments = CollegeAssignment.objects.filter(tenant=context.tenant, is_archived=False, created_at__gte=timezone.now() - timezone.timedelta(days=int(part_3_day))).select_related("assigned_to", "assigned_to__user")
        college_contact = assignments.filter(workflow_status="Follow up").count()
        college_left = assignments.filter(workflow_status="Not interested").count()
        college_new = assignments.filter(workflow_status__in=["Assigned", "New", ""]).count()
        top_users = list(
            assignments.filter(created_at__gte=timezone.now() - timezone.timedelta(days=int(part_2_day)))
            .values("assigned_to__user__username")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )
        user_arr = [item["assigned_to__user__username"] for item in top_users]
        follow_arr = [assignments.filter(assigned_to__user__username=username, workflow_status="Follow up").count() for username in user_arr]
        email_sent_arr = [assignments.filter(assigned_to__user__username=username, workflow_status="Email sent").count() for username in user_arr]
        data_list_arr = [assignments.filter(assigned_to__user__username=username, workflow_status="Data received").count() for username in user_arr]
        work_flow_arr = [
            assignments.filter(workflow_status__in=["Wrong call", "Wrong email"]).count(),
            assignments.filter(workflow_status="Data received").count(),
            assignments.filter(workflow_status="Follow up").count(),
            assignments.filter(workflow_status="Not interested").count(),
        ]
        return ServiceResult.success(
            {
                "college_contact": college_contact,
                "college_left": college_left,
                "college_new": college_new,
                "total_college": assignments.count(),
                "user_arr": user_arr,
                "follow_arr": follow_arr,
                "email_sent_arr": email_sent_arr,
                "data_list_arr": data_list_arr,
                "work_flow_arr": work_flow_arr,
            }
        )

    @staticmethod
    def dataentry_dashboard(context, rows=None):
        created = None
        if rows:
            created = TalentPipelineService.import_colleges(context, rows)
        wrong_colleges = CollegeAssignment.objects.filter(tenant=context.tenant, workflow_status="Wrong call", is_archived=False).select_related("college").order_by("college__college_name")
        return ServiceResult.success(
            {
                "wrong_colleges": [
                    {
                        "assignment_id": item.id,
                        "college_id": item.college_id,
                        "college_name": item.college.college_name,
                    }
                    for item in wrong_colleges
                ],
                "colleges_count": wrong_colleges.count(),
                "imported": created.data if created else None,
            }
        )

from django.db.models import Count
from django.utils import timezone
from django.utils.crypto import get_random_string

from Backend.Apps.Project.models import ComplianceAssignment, ComplianceCampaign, DefaultCheckpoint, DeliveryAlert, DeliveryDocument, DeliveryMilestone, MilestoneComponent, ProjectWorkspace, RepositoryLink, TeamAssignment
from Backend.Apps.Project.provider import ProjectIntegrationProvider
from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, WorkItem
from Backend.Apps.TasksDashboard.services import WorkManagementService
from Backend.EnterpriseCore.services import OutboxService, ServiceResult


class ProjectDeliveryService:
    @staticmethod
    def create_default_checkpoints(context, project_id):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        defaults = DefaultCheckpoint.objects.filter(tenant=context.tenant).filter(project_type__in=[project.project_type, ""]).order_by("sequence")
        if not defaults.exists():
            seed_titles = ["Discovery", "Planning", "Implementation", "Review", "Handover"]
            for index, title in enumerate(seed_titles, start=1):
                defaults = list(defaults) + [DefaultCheckpoint.objects.create(tenant=context.tenant, workspace=context.workspace, title=title, sequence=index, project_type=project.project_type, created_by=context.actor)]
        created = []
        for checkpoint in defaults:
            milestone, _created = DeliveryMilestone.objects.get_or_create(
                tenant=context.tenant,
                project=project,
                title=checkpoint.title,
                defaults={
                    "workspace": context.workspace or project.workspace,
                    "sequence": checkpoint.sequence,
                    "bounty": checkpoint.bounty,
                    "acceptance_criteria": checkpoint.acceptance_criteria,
                    "created_by": context.actor,
                    "updated_by": context.actor,
                },
            )
            created.append(milestone.id)
        return ServiceResult.success({"count": len(created), "milestoneIds": created}, status_code=201)

    @staticmethod
    def mark_milestone_complete(context, milestone_id, completed_on=None):
        milestone = DeliveryMilestone.objects.filter(tenant=context.tenant, id=milestone_id).first()
        if not milestone:
            return ServiceResult.failure({"milestone": "Milestone not found."}, status_code=404)
        milestone.status = "Completed"
        if completed_on:
            milestone.completed_on = completed_on
        milestone.updated_by = context.actor
        milestone.save(update_fields=["status", "completed_on", "updated_by", "updated_at"])
        OutboxService.publish(context, "DeliveryMilestone", milestone.id, "MilestoneCompleted", {"projectId": milestone.project_id})
        return ServiceResult.success(milestone)

    @staticmethod
    def calculate_health(context, project_id):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        milestones = DeliveryMilestone.objects.filter(tenant=context.tenant, project=project)
        total = milestones.count()
        completed = milestones.filter(status="Completed").count()
        overdue = milestones.filter(status__in=["Open", "InProgress"], due_on__lt=timezone.localdate()).count()
        if overdue:
            health = "Escalated"
        elif total and completed == total:
            health = "Completed"
        else:
            health = "OnTrack"
        project.health = health
        project.updated_by = context.actor
        project.save(update_fields=["health", "updated_by", "updated_at"])
        return ServiceResult.success({"projectId": project.id, "health": health, "total": total, "completed": completed, "overdue": overdue})

    @staticmethod
    def raise_delivery_alert(context, project_id, severity, title, description="", metadata=None):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        alert = DeliveryAlert.objects.create(
            tenant=context.tenant,
            workspace=context.workspace,
            project=project,
            severity=severity,
            title=title,
            description=description,
            metadata=metadata or {},
            created_by=context.actor,
        )
        return ServiceResult.success(alert, status_code=201)

    @staticmethod
    def add_team_member(context, project_id, employee_id, role="Member", allocation_percent=100):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        assignment, _created = TeamAssignment.objects.update_or_create(
            tenant=context.tenant,
            project=project,
            employee_id=employee_id,
            defaults={"workspace": context.workspace or project.workspace, "role": role, "allocation_percent": allocation_percent, "status": "Active", "updated_by": context.actor},
        )
        OutboxService.publish(context, "TeamAssignment", assignment.id, "ProjectMemberAdded", {"projectId": project.id, "employeeId": employee_id})
        return ServiceResult.success(assignment, status_code=201)

    @staticmethod
    def remove_team_member(context, assignment_id, reason=""):
        assignment = TeamAssignment.objects.filter(tenant=context.tenant, id=assignment_id).first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Team assignment not found."}, status_code=404)
        assignment.status = "Removed"
        assignment.ends_on = timezone.localdate()
        assignment.metadata = {**assignment.metadata, "remove_reason": reason}
        assignment.updated_by = context.actor
        assignment.save(update_fields=["status", "ends_on", "metadata", "updated_by", "updated_at"])
        return ServiceResult.success(assignment)

    @staticmethod
    def accept_terms(context, assignment_id):
        assignment = TeamAssignment.objects.filter(tenant=context.tenant, id=assignment_id).first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Team assignment not found."}, status_code=404)
        assignment.terms_accepted_at = timezone.now()
        assignment.updated_by = context.actor
        assignment.save(update_fields=["terms_accepted_at", "updated_by", "updated_at"])
        return ServiceResult.success(assignment)

    @staticmethod
    def create_repository_link(context, project_id, name, owner="", provider="GitHub", default_branch="main", live=False):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        owner = owner or project.github_organization
        provider_payload = ProjectIntegrationProvider(live=live).create_repository(owner, name, private=True)
        full_name = provider_payload.get("full_name") or (f"{owner}/{name}" if owner else name)
        repository, _created = RepositoryLink.objects.update_or_create(
            tenant=context.tenant,
            project=project,
            name=name,
            defaults={"workspace": context.workspace or project.workspace, "owner": provider_payload.get("owner", owner), "full_name": full_name, "provider": provider, "default_branch": provider_payload.get("default_branch", default_branch), "access_status": "Created" if live else "DryRunCreated", "metadata": provider_payload, "updated_by": context.actor},
        )
        OutboxService.publish(context, "RepositoryLink", repository.id, "ProjectRepositoryLinked", {"fullName": full_name, "dryRun": not live})
        return ServiceResult.success(repository, status_code=201)

    @staticmethod
    def update_repository_access(context, repository_id, employee_id, access_status="AccessRequested"):
        repository = RepositoryLink.objects.filter(tenant=context.tenant, id=repository_id).first()
        if not repository:
            return ServiceResult.failure({"repository": "Repository link not found."}, status_code=404)
        TeamAssignment.objects.filter(tenant=context.tenant, project=repository.project, employee_id=employee_id).update(github_access_status=access_status, updated_by=context.actor)
        repository.access_status = access_status
        repository.updated_by = context.actor
        repository.save(update_fields=["access_status", "updated_by", "updated_at"])
        return ServiceResult.success(repository)

    @staticmethod
    def record_document(context, project_id, title, document_type="General", storage_reference="", file_id=""):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        document = DeliveryDocument.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or project.workspace,
            project=project,
            title=title,
            document_type=document_type,
            storage_reference=storage_reference,
            file_id=file_id,
            created_by=context.actor,
            updated_by=context.actor,
        )
        return ServiceResult.success(document, status_code=201)

    @staticmethod
    def pin_document(context, document_id, is_pinned=True):
        document = DeliveryDocument.objects.filter(tenant=context.tenant, id=document_id).first()
        if not document:
            return ServiceResult.failure({"document": "Delivery document not found."}, status_code=404)
        document.is_pinned = is_pinned
        document.updated_by = context.actor
        document.save(update_fields=["is_pinned", "updated_by", "updated_at"])
        return ServiceResult.success(document)

    @staticmethod
    def launch_compliance_campaign(context, project_id, name="Anti phishing assessment", employee_ids=None):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        campaign = ComplianceCampaign.objects.create(
            tenant=context.tenant,
            workspace=context.workspace or project.workspace,
            project=project,
            name=name,
            campaign_type="AntiPhishing",
            status="Scheduled",
            scheduled_for=timezone.now(),
            created_by=context.actor,
            updated_by=context.actor,
        )
        if not employee_ids:
            employee_ids = list(TeamAssignment.objects.filter(tenant=context.tenant, project=project, status="Active").values_list("employee_id", flat=True))
        assignments = []
        for employee_id in employee_ids:
            assignment, _created = ComplianceAssignment.objects.get_or_create(
                tenant=context.tenant,
                campaign=campaign,
                employee_id=employee_id,
                defaults={"workspace": context.workspace or project.workspace, "token": get_random_string(32), "created_by": context.actor, "updated_by": context.actor},
            )
            assignments.append(assignment.id)
        OutboxService.publish(context, "ComplianceCampaign", campaign.id, "ComplianceCampaignLaunched", {"assignmentCount": len(assignments)})
        return ServiceResult.success({"campaignId": campaign.id, "assignmentIds": assignments}, status_code=201)

    @staticmethod
    def complete_compliance_assignment(context, assignment_id, score=0, evidence=None):
        assignment = ComplianceAssignment.objects.filter(tenant=context.tenant, id=assignment_id).first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Compliance assignment not found."}, status_code=404)
        assignment.status = "Completed"
        assignment.score = score or 0
        assignment.evidence = evidence or {}
        assignment.completed_at = timezone.now()
        assignment.updated_by = context.actor
        assignment.save(update_fields=["status", "score", "evidence", "completed_at", "updated_by", "updated_at"])
        return ServiceResult.success(assignment)

    @staticmethod
    def daily_notifications(context):
        rows = list(ProjectWorkspace.objects.filter(tenant=context.tenant).values("status", "health").annotate(count=Count("id")).order_by("status", "health"))
        OutboxService.publish(context, "ProjectWorkspace", 0, "ProjectDailyNotificationQueued", {"rows": rows})
        return ServiceResult.success({"rows": rows})

    @staticmethod
    def onboarding_summary(context):
        projects = ProjectWorkspace.objects.filter(tenant=context.tenant).annotate(
            milestone_count=Count("milestones", distinct=True),
            member_count=Count("team_assignments", distinct=True),
            repository_count=Count("repositories", distinct=True),
        )
        rows = [
            {
                "id": project.id,
                "project_name": project.name,
                "project_type": project.project_type,
                "status": project.status,
                "health": project.health,
                "terms_required": project.terms_required,
                "anti_phishing_enabled": project.anti_phishing_enabled,
                "milestone_count": project.milestone_count,
                "member_count": project.member_count,
                "repository_count": project.repository_count,
            }
            for project in projects.order_by("name")
        ]
        return ServiceResult.success({"count": len(rows), "projects": rows})

    @staticmethod
    def project_dashboard(context, project_id):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        milestones = DeliveryMilestone.objects.filter(tenant=context.tenant, project=project).order_by("sequence", "due_on")
        assignments = TeamAssignment.objects.filter(tenant=context.tenant, project=project).select_related("employee", "employee__user")
        repositories = RepositoryLink.objects.filter(tenant=context.tenant, project=project).order_by("name")
        documents = DeliveryDocument.objects.filter(tenant=context.tenant, project=project, status="Active").order_by("-is_pinned", "title")
        alerts = DeliveryAlert.objects.filter(tenant=context.tenant, project=project).order_by("-created_at")
        work_items = WorkItem.objects.filter(tenant=context.tenant, project=project).order_by("order_index", "id")
        return ServiceResult.success(
            {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "code": project.code,
                    "project_type": project.project_type,
                    "status": project.status,
                    "health": project.health,
                    "starts_on": project.starts_on.isoformat() if project.starts_on else None,
                    "ends_on": project.ends_on.isoformat() if project.ends_on else None,
                    "terms_required": project.terms_required,
                    "anti_phishing_enabled": project.anti_phishing_enabled,
                },
                "milestones": [
                    {
                        "id": milestone.id,
                        "title": milestone.title,
                        "status": milestone.status,
                        "due_on": milestone.due_on.isoformat() if milestone.due_on else None,
                        "completed_on": milestone.completed_on.isoformat() if milestone.completed_on else None,
                        "delayed_days": milestone.delayed_days,
                    }
                    for milestone in milestones
                ],
                "team": [
                    {
                        "id": assignment.id,
                        "employee_id": assignment.employee_id,
                        "employee_name": assignment.employee.display_name,
                        "role": assignment.role,
                        "status": assignment.status,
                        "github_access_status": assignment.github_access_status,
                        "is_absent": assignment.is_absent,
                    }
                    for assignment in assignments
                ],
                "repositories": [
                    {
                        "id": repository.id,
                        "name": repository.name,
                        "full_name": repository.full_name,
                        "access_status": repository.access_status,
                    }
                    for repository in repositories
                ],
                "documents": [
                    {
                        "id": document.id,
                        "title": document.title,
                        "document_type": document.document_type,
                        "file_id": document.file_id,
                        "is_pinned": document.is_pinned,
                        "metadata": document.metadata,
                    }
                    for document in documents
                ],
                "alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity,
                        "title": alert.title,
                        "status": alert.status,
                    }
                    for alert in alerts
                ],
                "tasks": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "status": item.status,
                        "priority": item.priority,
                        "owner_id": item.owner_id,
                    }
                    for item in work_items
                ],
            }
        )

    @staticmethod
    def project_terms(context, project_id, employee_id=None, accept=False):
        from Backend.Apps.Users.models import EmployeeProfile

        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        actor_employee = EmployeeProfile.objects.filter(tenant=context.tenant, user=context.actor).first() if context.actor else None
        employee_id = employee_id or (actor_employee.id if actor_employee else None)
        assignment = TeamAssignment.objects.filter(tenant=context.tenant, project=project, employee_id=employee_id).first()
        if accept and assignment:
            return ProjectDeliveryService.accept_terms(context, assignment.id)
        return ServiceResult.success(
            {
                "project_id": project.id,
                "terms_required": project.terms_required,
                "anti_phishing_enabled": project.anti_phishing_enabled,
                "accepted": bool(assignment and assignment.terms_accepted_at),
            }
        )

    @staticmethod
    def check_repository_exists(context, name="", project_id=None, full_name=""):
        repositories = RepositoryLink.objects.filter(tenant=context.tenant)
        if project_id:
            repositories = repositories.filter(project_id=project_id)
        if full_name:
            repositories = repositories.filter(full_name__iexact=full_name)
        elif name:
            repositories = repositories.filter(name__iexact=name)
        repository = repositories.first()
        return ServiceResult.success({"exists": bool(repository), "repository_id": repository.id if repository else None})

    @staticmethod
    def get_user_organizations(context):
        organizations = set(ProjectWorkspace.objects.filter(tenant=context.tenant).exclude(github_organization="").values_list("github_organization", flat=True))
        organizations.update(RepositoryLink.objects.filter(tenant=context.tenant).exclude(owner="").values_list("owner", flat=True))
        return ServiceResult.success({"organizations": sorted(org for org in organizations if org)})

    @staticmethod
    def get_user_repositories(context, member_id, project_id):
        assignment = TeamAssignment.objects.filter(tenant=context.tenant, project_id=project_id, employee_id=member_id).first()
        repositories = RepositoryLink.objects.filter(tenant=context.tenant, project_id=project_id).order_by("name")
        return ServiceResult.success(
            {
                "member_id": member_id,
                "project_id": project_id,
                "repositories": [
                    {
                        "id": repository.id,
                        "name": repository.name,
                        "full_name": repository.full_name,
                        "access_status": assignment.github_access_status if assignment else repository.access_status,
                    }
                    for repository in repositories
                ],
            }
        )

    @staticmethod
    def get_days_left(context, project_id):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        if not project.ends_on:
            return ServiceResult.success({"project_id": project.id, "days_left": None})
        return ServiceResult.success({"project_id": project.id, "days_left": (project.ends_on - timezone.localdate()).days})

    @staticmethod
    def get_alerts(context, project_id):
        alerts = DeliveryAlert.objects.filter(tenant=context.tenant, project_id=project_id).order_by("-created_at")
        return ServiceResult.success(
            {
                "count": alerts.count(),
                "results": [
                    {"id": alert.id, "severity": alert.severity, "title": alert.title, "status": alert.status}
                    for alert in alerts
                ],
            }
        )

    @staticmethod
    def update_project_details(context, project_id, data):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        update_fields = ["updated_by", "updated_at"]
        for field in ["name", "code", "client_name", "description", "project_type", "priority", "status", "health", "github_organization", "clickup_sync_enabled", "terms_required", "anti_phishing_enabled"]:
            if field in data:
                setattr(project, field, data.get(field))
                update_fields.append(field)
        for date_field in ["starts_on", "ends_on"]:
            if date_field in data:
                setattr(project, date_field, data.get(date_field) or None)
                update_fields.append(date_field)
        if "metadata" in data:
            project.metadata = data.get("metadata") or {}
            update_fields.append("metadata")
        project.updated_by = context.actor
        project.save(update_fields=update_fields)
        return ServiceResult.success(project)

    @staticmethod
    def update_milestone_details(context, milestone_id, data):
        milestone = DeliveryMilestone.objects.filter(tenant=context.tenant, id=milestone_id).first()
        if not milestone:
            return ServiceResult.failure({"milestone": "Milestone not found."}, status_code=404)
        update_fields = ["updated_by", "updated_at"]
        for field in ["title", "status", "sequence", "bounty", "delayed_days"]:
            if field in data:
                setattr(milestone, field, data.get(field))
                update_fields.append(field)
        for date_field in ["due_on", "completed_on"]:
            if date_field in data:
                setattr(milestone, date_field, data.get(date_field) or None)
                update_fields.append(date_field)
        if "acceptance_criteria" in data:
            milestone.acceptance_criteria = data.get("acceptance_criteria") or []
            update_fields.append("acceptance_criteria")
        milestone.updated_by = context.actor
        milestone.save(update_fields=update_fields)
        return ServiceResult.success(milestone)

    @staticmethod
    def mark_notifications_read(context, project_id=None):
        alerts = DeliveryAlert.objects.filter(tenant=context.tenant)
        if project_id:
            alerts = alerts.filter(project_id=project_id)
        count = alerts.update(status="Read", updated_by=context.actor)
        return ServiceResult.success({"count": count})

    @staticmethod
    def add_member_back(context, project_id, employee_id):
        assignment, _created = TeamAssignment.objects.update_or_create(
            tenant=context.tenant,
            project_id=project_id,
            employee_id=employee_id,
            defaults={"workspace": context.workspace, "status": "Active", "ends_on": None, "updated_by": context.actor},
        )
        return ServiceResult.success(assignment)

    @staticmethod
    def replace_member(context, project_id, old_employee_id, new_employee_id, role="Member"):
        old_assignment = TeamAssignment.objects.filter(tenant=context.tenant, project_id=project_id, employee_id=old_employee_id).first()
        if old_assignment:
            ProjectDeliveryService.remove_team_member(context, old_assignment.id, reason="Replaced")
        return ProjectDeliveryService.add_team_member(context, project_id, new_employee_id, role=role)

    @staticmethod
    def mark_absent(context, project_id, employee_id, is_absent=True, absent_reason=""):
        assignment = TeamAssignment.objects.filter(tenant=context.tenant, project_id=project_id, employee_id=employee_id).first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Team assignment not found."}, status_code=404)
        assignment.is_absent = is_absent
        assignment.absent_reason = absent_reason
        assignment.updated_by = context.actor
        assignment.save(update_fields=["is_absent", "absent_reason", "updated_by", "updated_at"])
        return ServiceResult.success(assignment)

    @staticmethod
    def upsert_clickup_mapping(context, project_id, external_id="", project_name="", space_id="", list_id=""):
        project = ProjectWorkspace.objects.filter(tenant=context.tenant, id=project_id).first()
        if not project:
            return ServiceResult.failure({"project": "Project not found."}, status_code=404)
        mapping, _created = ClickUpProjectMapping.objects.update_or_create(
            tenant=context.tenant,
            project=project,
            defaults={
                "workspace": context.workspace or project.workspace,
                "project_name": project_name or project.name,
                "external_id": external_id,
                "space_id": space_id,
                "list_id": list_id,
                "updated_by": context.actor,
            },
        )
        return ServiceResult.success(mapping, status_code=201)

    @staticmethod
    def task_detail(context, task_id):
        task = WorkItem.objects.filter(tenant=context.tenant, id=task_id).select_related("project", "owner").first()
        if not task:
            return ServiceResult.failure({"task": "Work item not found."}, status_code=404)
        return ServiceResult.success(
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "project_id": task.project_id,
                "owner_id": task.owner_id,
                "bounty": str(task.bounty),
                "due_at": task.due_at.isoformat() if task.due_at else None,
                "metadata": task.metadata,
            }
        )

    @staticmethod
    def add_task(context, project_id, title, owner_id=None, parent_id=None, description="", priority="Normal", bounty=0):
        return WorkManagementService.create_work_item(context, title, project_id=project_id, owner_id=owner_id, parent_id=parent_id, description=description, priority=priority, bounty=bounty)

    @staticmethod
    def update_task(context, task_id, data):
        task = WorkItem.objects.filter(tenant=context.tenant, id=task_id).first()
        if not task:
            return ServiceResult.failure({"task": "Work item not found."}, status_code=404)
        update_fields = ["updated_by", "updated_at"]
        for field in ["title", "description", "priority", "status", "owner_id", "parent_id"]:
            if field in data:
                setattr(task, field, data.get(field))
                update_fields.append(field)
        if "bounty" in data:
            task.bounty = data.get("bounty") or 0
            update_fields.append("bounty")
        if "due_at" in data:
            task.due_at = data.get("due_at") or None
            update_fields.append("due_at")
        if "task_type" in data:
            task.metadata = {**task.metadata, "task_type": data.get("task_type")}
            update_fields.append("metadata")
        task.updated_by = context.actor
        task.save(update_fields=update_fields)
        return ServiceResult.success(task)

    @staticmethod
    def delete_task(context, task_id):
        task = WorkItem.objects.filter(tenant=context.tenant, id=task_id).first()
        if not task:
            return ServiceResult.failure({"task": "Work item not found."}, status_code=404)
        task.delete()
        return ServiceResult.success({"task_id": task_id, "deleted": True})

    @staticmethod
    def assign_assignee(context, task_id, employee_id):
        return ProjectDeliveryService.update_task(context, task_id, {"owner_id": employee_id})

    @staticmethod
    def update_task_order(context, ordered_ids):
        return WorkManagementService.reorder_work_items(context, ordered_ids)

    @staticmethod
    def update_subtask_parent(context, task_id, parent_id):
        return ProjectDeliveryService.update_task(context, task_id, {"parent_id": parent_id})

    @staticmethod
    def update_subtask_status(context, task_id, status):
        return WorkManagementService.transition_work_item(context, task_id, status)

    @staticmethod
    def save_task_link(context, task_id, url):
        task = WorkItem.objects.filter(tenant=context.tenant, id=task_id).first()
        if not task:
            return ServiceResult.failure({"task": "Work item not found."}, status_code=404)
        task.metadata = {**task.metadata, "task_link": url}
        task.updated_by = context.actor
        task.save(update_fields=["metadata", "updated_by", "updated_at"])
        return ServiceResult.success(task)

    @staticmethod
    def get_items(context, project_id=None):
        tasks = WorkItem.objects.filter(tenant=context.tenant)
        milestones = DeliveryMilestone.objects.filter(tenant=context.tenant)
        if project_id:
            tasks = tasks.filter(project_id=project_id)
            milestones = milestones.filter(project_id=project_id)
        return ServiceResult.success(
            {
                "tasks": [{"id": task.id, "title": task.title, "status": task.status} for task in tasks.order_by("order_index", "id")],
                "milestones": [{"id": milestone.id, "title": milestone.title, "status": milestone.status} for milestone in milestones.order_by("sequence", "id")],
            }
        )

    @staticmethod
    def add_delay(context, milestone_id, delayed_days=1):
        milestone = DeliveryMilestone.objects.filter(tenant=context.tenant, id=milestone_id).first()
        if not milestone:
            return ServiceResult.failure({"milestone": "Milestone not found."}, status_code=404)
        milestone.delayed_days += int(delayed_days or 1)
        milestone.updated_by = context.actor
        milestone.save(update_fields=["delayed_days", "updated_by", "updated_at"])
        return ServiceResult.success(milestone)

    @staticmethod
    def upload_project_document(context, project_id, title, document_type="General", storage_reference="", file_id="", metadata=None):
        result = ProjectDeliveryService.record_document(context, project_id, title, document_type=document_type, storage_reference=storage_reference, file_id=file_id)
        if result.ok and metadata:
            result.data.metadata = metadata
            result.data.updated_by = context.actor
            result.data.save(update_fields=["metadata", "updated_by", "updated_at"])
        return result

    @staticmethod
    def edit_project_document(context, document_id, title="", storage_reference="", metadata=None):
        document = DeliveryDocument.objects.filter(tenant=context.tenant, id=document_id).first()
        if not document:
            return ServiceResult.failure({"document": "Delivery document not found."}, status_code=404)
        if title:
            document.title = title
        if storage_reference:
            document.storage_reference = storage_reference
        if metadata is not None:
            document.metadata = metadata
        document.updated_by = context.actor
        document.save(update_fields=["title", "storage_reference", "metadata", "updated_by", "updated_at"])
        return ServiceResult.success(document)

    @staticmethod
    def delete_project_document(context, document_id):
        document = DeliveryDocument.objects.filter(tenant=context.tenant, id=document_id).first()
        if not document:
            return ServiceResult.failure({"document": "Delivery document not found."}, status_code=404)
        document.status = "Archived"
        document.updated_by = context.actor
        document.save(update_fields=["status", "updated_by", "updated_at"])
        return ServiceResult.success(document)

    @staticmethod
    def get_file_name(context, file_id):
        document = DeliveryDocument.objects.filter(tenant=context.tenant, file_id=file_id).first()
        return ServiceResult.success({"file_id": file_id, "title": document.title if document else ""})

    @staticmethod
    def record_project_link(context, project_id, title, url, link_type="Link"):
        return ProjectDeliveryService.upload_project_document(
            context,
            project_id,
            title,
            document_type=link_type,
            storage_reference=url,
            metadata={"url": url, "link_type": link_type},
        )

    @staticmethod
    def send_anti_phishing_assessment(context, project_id, employee_ids=None, name="Anti phishing assessment"):
        return ProjectDeliveryService.launch_compliance_campaign(context, project_id, name=name, employee_ids=employee_ids)

    @staticmethod
    def complete_compliance_by_token(context, token, score=0, evidence=None):
        assignment = ComplianceAssignment.objects.filter(tenant=context.tenant, token=token).first()
        if not assignment:
            return ServiceResult.failure({"assignment": "Compliance assignment not found."}, status_code=404)
        return ProjectDeliveryService.complete_compliance_assignment(context, assignment.id, score=score, evidence=evidence)

    @staticmethod
    def anti_phishing_reports(context, project_id=None):
        assignments = ComplianceAssignment.objects.filter(tenant=context.tenant, campaign__campaign_type="AntiPhishing")
        if project_id:
            assignments = assignments.filter(campaign__project_id=project_id)
        rows = list(assignments.values("status").annotate(count=Count("id")).order_by("status"))
        average_score = assignments.aggregate(total=Count("id"), score_total=Count("score"))
        return ServiceResult.success({"rows": rows, "count": assignments.count(), "project_id": project_id, "completed_count": assignments.filter(status="Completed").count()})

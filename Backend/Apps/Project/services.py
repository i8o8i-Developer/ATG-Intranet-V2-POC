from django.db.models import Count
from django.utils import timezone
from django.utils.crypto import get_random_string

from Backend.Apps.Project.models import ComplianceAssignment, ComplianceCampaign, DefaultCheckpoint, DeliveryAlert, DeliveryDocument, DeliveryMilestone, MilestoneComponent, ProjectWorkspace, RepositoryLink, TeamAssignment
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
        full_name = f"{owner}/{name}" if owner else name
        repository, _created = RepositoryLink.objects.update_or_create(
            tenant=context.tenant,
            project=project,
            name=name,
            defaults={"workspace": context.workspace or project.workspace, "owner": owner, "full_name": full_name, "provider": provider, "default_branch": default_branch, "access_status": "Created" if live else "DryRunCreated", "metadata": {"dry_run": not live}, "updated_by": context.actor},
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

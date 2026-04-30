from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from Backend.Apps.Assesment.models import AssessmentActivity, AssessmentAssignment, AssessmentSubmission, AssessmentTemplate
from Backend.Apps.AtgDocs.models import DriveFile, DriveFolder, DocumentVersion, KnowledgeActivity, KnowledgeDocument, KnowledgePermission
from Backend.Apps.Banao.models import AuditArtifact, LeadAccount, LeadActivity, LeadContact, LeadNote, LeadTag, LeadTest, ProposalArtifact, WorkflowStatusHistory, WorkflowTransition
from Backend.Apps.FinanceAndPayroll.models import ApprovalDecision, BankAccount, CompensationPlan, PaymentOrder, PaymentWebhookEvent, PayPeriod, PayrollLineItem, PayrollRun, PayoutExecution, PayslipDocument
from Backend.Apps.Git.models import GitActivitySnapshot, GitRepositorySnapshot, RepositoryUtilityRequest
from Backend.Apps.GithubExtension.models import BranchReviewerAssignment, BranchTestingAssignment, GitHubRepository, RepositoryBranchStatus
from Backend.Apps.HtmlTemplate.models import ContentTemplate, GenericHtmlTemplate, OfferMacro, OfferTemplate, TemplateVariable
from Backend.Apps.IntegrationHub.models import IntegrationAttempt, IntegrationConnection, IntegrationProvider, IntegrationSyncJob, WebhookInboxEvent
from Backend.Apps.L3.models import CandidateProfile, CollegeAssignment, CollegeContact, CollegeEmailTemplate, CollegePipelineRecord, TalentAssignment, TalentEmail, TalentPerformanceSnapshot
from Backend.Apps.LegacyBridge.models import LegacyApplicationMap, LegacyMigrationIssue, LegacyModelCrosswalk, MigrationRun
from Backend.Apps.Lms.models import LeadQueueSnapshot, LearningAssignment, LearningModule, LearningPath, RevenuePerformanceSnapshot
from Backend.Apps.MainApp.models import CredentialShareGrant, CredentialVaultItem, ExternalIssueReference, LeaveRequest, ManagerScope, NotificationItem, OnboardingOffer
from Backend.Apps.McpAccessLayer.models import AgentPrincipal, DraftAgentAction, McpAccessGrant, McpInvocationAudit, McpResourceDefinition, McpToolDefinition
from Backend.Apps.Project.models import ComplianceAssignment, ComplianceCampaign, DefaultCheckpoint, DeliveryAlert, DeliveryDocument, DeliveryMilestone, MilestoneComponent, ProjectContact, ProjectWorkspace, RepositoryLink, TeamAssignment
from Backend.Apps.TasksDashboard.models import ClickUpProjectMapping, DailyStatusEntry, ExternalWorkMapping, ManagerAbbreviation, SlackDeliveryMessage, SlackDeliveryThread, TaskActivity, WorkEntry, WorkItem
from Backend.Apps.Users.models import BenchPeriod, Department, DepartmentMembership, Domain, EmployeeBankAccount, EmployeeCertificate, EmployeeFeedback, EmployeePaymentSnapshot, EmployeeProfile, EmployeeRating, Goal, GoalFeedback, InterviewProgress, LeaveBalance, LeavePolicy, LeaveTransaction, PayProfile, Position, ResignationRequest, Skill, SubDepartment, UserEffortReport, UserSkill, UserStatusSnapshot
from Backend.Apps.WorkflowIntelligence.models import BusinessWorkflowMap, RouteUsageAggregate, WorkflowReport
from Backend.EnterpriseCore.models import AccessAuditLog, BusinessUnit, Capability, IdempotencyKey, Organization, OutboxEvent, ResourcePolicy, Role, RoleAssignment, RoleCapability, Tenant, Workspace


class Command(BaseCommand):
    help = "Seed realistic dummy data across all rebuilt ERP modules for end-to-end frontend testing."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default="Banao")
        parser.add_argument("--workspace", default="Default Workspace")
        parser.add_argument("--username", default="backend-admin")
        parser.add_argument("--password", default="backend-admin")
        parser.add_argument("--email", default="backend-admin@example.com")

    def handle(self, *args, **options):
        call_command(
            "bootstrap_backend",
            tenant=options["tenant"],
            workspace=options["workspace"],
            username=options["username"],
            password=options["password"],
            email=options["email"],
            verbosity=0,
        )
        self.tenant = Tenant.objects.get(slug=options["tenant"].lower().replace(" ", "-"))
        self.workspace = Workspace.objects.get(tenant=self.tenant, name=options["workspace"])
        self.created = 0
        self.updated = 0
        self.today = timezone.localdate()
        self.now = timezone.now()
        self.admin_user = get_user_model().objects.get(username=options["username"])

        employees = self.seed_people()
        projects = self.seed_projects(employees)
        self.seed_people_ops(employees)
        self.seed_tasks(employees, projects)
        leads = self.seed_revenue(employees)
        self.seed_lms(employees)
        self.seed_finance(employees)
        self.seed_docs(employees)
        self.seed_assessments(employees)
        self.seed_l3(employees)
        self.seed_git(employees, projects)
        self.seed_templates()
        self.seed_integrations()
        self.seed_mcp(employees)
        self.seed_workflow_intelligence()
        self.seed_legacy_bridge(projects, leads)
        self.seed_enterprise_audit()

        self.stdout.write(self.style.SUCCESS("Demo ERP seed complete."))
        self.stdout.write(f"Tenant ID: {self.tenant.id}")
        self.stdout.write(f"Workspace ID: {self.workspace.id}")
        self.stdout.write(f"Records created: {self.created}")
        self.stdout.write(f"Records updated: {self.updated}")

    def scoped(self, **values):
        return {"tenant": self.tenant, "workspace": self.workspace, **values}

    def upsert(self, model, lookup, defaults=None):
        fields = {field.name for field in model._meta.fields}
        payload = dict(defaults or {})
        if "tenant" in fields and "tenant" not in lookup and "tenant" not in payload:
            payload["tenant"] = self.tenant
        if "workspace" in fields and "workspace" not in lookup and "workspace" not in payload:
            payload["workspace"] = self.workspace
        obj, created = model.objects.update_or_create(**lookup, defaults=payload)
        self.created += int(created)
        self.updated += int(not created)
        return obj

    def make_user(self, username, first_name, last_name, email):
        user, _created = get_user_model().objects.update_or_create(
            username=username,
            defaults={"first_name": first_name, "last_name": last_name, "email": email, "is_active": True},
        )
        user.set_password("demo1234")
        user.save(update_fields=["password", "first_name", "last_name", "email", "is_active"])
        return user

    def seed_people(self):
        domains = {
            "Delivery": self.upsert(Domain, {"tenant": self.tenant, "name": "Delivery"}, {"code": "DEL", "description": "Project delivery and engineering operations"}),
            "Revenue": self.upsert(Domain, {"tenant": self.tenant, "name": "Revenue"}, {"code": "REV", "description": "Banao CRM and LMS operations"}),
            "People": self.upsert(Domain, {"tenant": self.tenant, "name": "People"}, {"code": "PPL", "description": "HR, people ops, finance, learning"}),
        }
        departments = {
            "Python Django": self.upsert(Department, {"tenant": self.tenant, "code": "PYDJ"}, {"name": "Python Django", "category": "Engineering", "domain": domains["Delivery"], "base_pay": Decimal("35000"), "pay_type": "Monthly"}),
            "MERN Stack": self.upsert(Department, {"tenant": self.tenant, "code": "MERN"}, {"name": "MERN Stack", "category": "Engineering", "domain": domains["Delivery"], "base_pay": Decimal("33000"), "pay_type": "Monthly"}),
            "Business Analysis": self.upsert(Department, {"tenant": self.tenant, "code": "BA"}, {"name": "Business Analysis", "category": "Revenue", "domain": domains["Revenue"], "base_pay": Decimal("30000"), "pay_type": "Monthly"}),
            "Human Resources": self.upsert(Department, {"tenant": self.tenant, "code": "HR"}, {"name": "Human Resources", "category": "People", "domain": domains["People"], "base_pay": Decimal("28000"), "pay_type": "Monthly"}),
            "Finance": self.upsert(Department, {"tenant": self.tenant, "code": "FIN"}, {"name": "Finance", "category": "Finance", "domain": domains["People"], "base_pay": Decimal("36000"), "pay_type": "Monthly"}),
            "Design": self.upsert(Department, {"tenant": self.tenant, "code": "DES"}, {"name": "Design", "category": "Creative", "domain": domains["Delivery"], "base_pay": Decimal("32000"), "pay_type": "Monthly"}),
            "Manual Testing": self.upsert(Department, {"tenant": self.tenant, "code": "QA"}, {"name": "Manual Testing", "category": "Quality", "domain": domains["Delivery"], "base_pay": Decimal("27000"), "pay_type": "Monthly"}),
            "L3 Team": self.upsert(Department, {"tenant": self.tenant, "code": "L3"}, {"name": "L3 Team", "category": "Talent", "domain": domains["People"], "base_pay": Decimal("25000"), "pay_type": "Monthly"}),
        }
        for dept in departments.values():
            self.upsert(SubDepartment, {"tenant": self.tenant, "department": dept, "name": f"{dept.name} Core"}, {"code": f"{dept.code}-CORE"})

        positions = {
            "Project Manager": self.upsert(Position, {"tenant": self.tenant, "code": "PM"}, {"title": "Project Manager", "level": "Lead"}),
            "Developer": self.upsert(Position, {"tenant": self.tenant, "code": "DEV"}, {"title": "Developer", "level": "L2"}),
            "Business Analyst": self.upsert(Position, {"tenant": self.tenant, "code": "BA"}, {"title": "Business Analyst", "level": "L2"}),
            "HR Manager": self.upsert(Position, {"tenant": self.tenant, "code": "HRM"}, {"title": "HR Manager", "level": "Lead"}),
            "Finance Manager": self.upsert(Position, {"tenant": self.tenant, "code": "FM"}, {"title": "Finance Manager", "level": "Lead"}),
            "Designer": self.upsert(Position, {"tenant": self.tenant, "code": "DSN"}, {"title": "Designer", "level": "L2"}),
            "QA Engineer": self.upsert(Position, {"tenant": self.tenant, "code": "QA"}, {"title": "QA Engineer", "level": "L2"}),
            "Intern": self.upsert(Position, {"tenant": self.tenant, "code": "INT"}, {"title": "Intern", "level": "Intern"}),
        }
        skills = [
            ("Django API", "Backend", departments["Python Django"]),
            ("React JS", "Frontend", departments["MERN Stack"]),
            ("Lead Qualification", "Revenue", departments["Business Analysis"]),
            ("Payroll Review", "Finance", departments["Finance"]),
            ("UI Layout", "Design", departments["Design"]),
            ("Regression Testing", "QA", departments["Manual Testing"]),
        ]
        skill_objects = [self.upsert(Skill, {"tenant": self.tenant, "name": name}, {"category": category, "department": dept}) for name, category, dept in skills]

        people = [
            ("sanchay", "Sanchay", "Bagul", "sanchay@example.com", "EMP001", "Sanchay Sanjeev Bagul", departments["Python Django"], positions["Project Manager"], "Full-Time"),
            ("faraz", "Mohammed", "Faraz", "faraz@example.com", "EMP002", "Mohammed Faraz Mohiuddin", departments["Python Django"], positions["Developer"], "Intern"),
            ("tamanna", "Tamanna", "Rastogi", "tamanna@example.com", "EMP003", "Tamanna Rastogi", departments["Business Analysis"], positions["Business Analyst"], "Intern"),
            ("nisha", "Nisha", "Sabar", "nisha@example.com", "EMP004", "Sabar Nisha S", departments["Human Resources"], positions["HR Manager"], "Full-Time"),
            ("rahul", "Rahul", "Finance", "rahul@example.com", "EMP005", "Rahul Finance", departments["Finance"], positions["Finance Manager"], "Full-Time"),
            ("aditi", "Aditi", "Design", "aditi@example.com", "EMP006", "Aditi Design", departments["Design"], positions["Designer"], "Full-Time"),
            ("hema", "Hema", "QA", "hema@example.com", "EMP007", "Hema QA", departments["Manual Testing"], positions["QA Engineer"], "Full-Time"),
            ("tanmay", "Tanmay", "Wagh", "tanmay@example.com", "EMP008", "Tanmay Arun Wagh", departments["L3 Team"], positions["Intern"], "Intern"),
        ]
        employees = {}
        manager = None
        for username, first, last, email, code, display_name, dept, position, employment_type in people:
            user = self.make_user(username, first, last, email)
            employee = self.upsert(
                EmployeeProfile,
                {"tenant": self.tenant, "employee_code": code},
                {
                    "user": user,
                    "display_name": display_name,
                    "department": dept,
                    "position": position,
                    "manager": manager,
                    "employment_type": employment_type,
                    "status": EmployeeProfile.STATUS_ACTIVE,
                    "joined_on": self.today - timezone.timedelta(days=120),
                    "leaves_wallet": Decimal("8"),
                    "leaves_per_month": Decimal("1.5"),
                    "onboarding_completed": True,
                    "github_username": username,
                },
            )
            if code == "EMP001":
                manager = employee
                employee.manager = None
                employee.save(update_fields=["manager", "updated_at"])
            self.upsert(DepartmentMembership, {"tenant": self.tenant, "employee": employee, "department": dept}, {"status": DepartmentMembership.STATUS_ACTIVE, "started_on": self.today - timezone.timedelta(days=120)})
            self.upsert(EmployeeRating, {"employee": employee}, {"tenant": self.tenant, "workspace": self.workspace, "rating_value": Decimal("4.20")})
            self.upsert(PayProfile, {"tenant": self.tenant, "employee": employee, "effective_at": self.now.replace(microsecond=0)}, {"base_pay": dept.base_pay, "pay_type": dept.pay_type, "pay_per_task": dept.pay_per_task})
            self.upsert(EmployeeBankAccount, {"tenant": self.tenant, "employee": employee, "masked_account_number": f"XXXX{code[-3:]}"}, {"account_holder_name": display_name, "ifsc_code": "HDFC0001234", "upi_id": f"{username}@upi", "verification_status": "Verified"})
            employees[code] = employee

        for index, employee in enumerate(employees.values()):
            skill = skill_objects[index % len(skill_objects)]
            self.upsert(UserSkill, {"tenant": self.tenant, "employee": employee, "skill": skill}, {"proficiency": 4, "rating": 4, "assigned_from_department": True})
            goal = self.upsert(Goal, {"tenant": self.tenant, "employee": employee, "title": "Complete AI-ready ERP workflow"}, {"assigned_by": self.admin_user, "description": "Operate one mapped module in the React ERP", "due_on": self.today + timezone.timedelta(days=14), "status": "Open"})
            self.upsert(GoalFeedback, {"tenant": self.tenant, "goal": goal, "feedback_type": "ManagerNote"}, {"author": self.admin_user, "rating": 4, "note": "Demo feedback for migrated HRMS view"})
            self.upsert(UserStatusSnapshot, {"tenant": self.tenant, "employee": employee, "status": "Active", "effective_from": self.today - timezone.timedelta(days=30)}, {"reason": "Demo active status"})
        self.upsert(BenchPeriod, {"tenant": self.tenant, "employee": employees["EMP006"], "started_on": self.today - timezone.timedelta(days=10)}, {"reason": "Available for AI design pilot"})
        self.upsert(EmployeeCertificate, {"tenant": self.tenant, "employee": employees["EMP002"], "position_title": "Django Developer"}, {"manager": employees["EMP001"], "issued_on": self.today - timezone.timedelta(days=20), "storage_reference": "demo://certificate/faraz"})
        self.upsert(EmployeeFeedback, {"tenant": self.tenant, "employee": employees["EMP002"], "feedback_type": "Project", "project_name": "Intranet Rebuild"}, {"submitted_by": self.admin_user, "feedback_text": "Solid progress on API parity and React screens."})
        self.upsert(InterviewProgress, {"tenant": self.tenant, "employee": employees["EMP008"]}, {"candidate_id": "IG-DEMO-001", "status": "InProgress", "level": "L1", "job_id": "L3-INTERN"})
        return employees

    def seed_people_ops(self, employees):
        policy = self.upsert(LeavePolicy, {"tenant": self.tenant, "name": "Standard Leave"}, {"leaves_per_month": Decimal("1.5"), "carry_forward": True})
        for employee in employees.values():
            balance = self.upsert(LeaveBalance, {"tenant": self.tenant, "employee": employee, "policy": policy}, {"available": Decimal("8"), "accrued": Decimal("12"), "used": Decimal("4")})
            self.upsert(LeaveTransaction, {"tenant": self.tenant, "balance": balance, "transaction_type": "Accrual", "amount": Decimal("1.5")}, {"reason": "Monthly accrual"})
        self.upsert(LeaveRequest, {"tenant": self.tenant, "employee": employees["EMP002"], "starts_on": self.today + timezone.timedelta(days=3)}, {"leave_type": "Casual", "ends_on": self.today + timezone.timedelta(days=4), "status": "Submitted", "requested_days": Decimal("2"), "reason": "Family function"})
        self.upsert(OnboardingOffer, {"tenant": self.tenant, "candidate_email": "new.dev@example.com"}, {"candidate_name": "New Dev Candidate", "company_name": "Banao", "position_title": "React Developer", "offer_type": "Intern", "token": "demo-offer-token", "status": "Issued", "issued_at": self.now})
        self.upsert(NotificationItem, {"tenant": self.tenant, "recipient": employees["EMP001"].user, "title": "Project dashboard review due"}, {"message": "Review delayed milestones and repo access", "category": "Project", "resource_type": "ProjectWorkspace", "resource_id": "demo", "delivered_at": self.now})
        credential = self.upsert(CredentialVaultItem, {"tenant": self.tenant, "name": "Demo GitHub Token", "system_name": "GitHub"}, {"owner": self.admin_user, "secret_reference": "secret://demo/github", "status": "Active", "rotation_due_at": self.now + timezone.timedelta(days=30)})
        self.upsert(CredentialShareGrant, {"tenant": self.tenant, "credential": credential, "grantee": employees["EMP001"].user}, {"permission": "Read", "expires_at": self.now + timezone.timedelta(days=14), "reason": "Project access"})
        self.upsert(ExternalIssueReference, {"tenant": self.tenant, "provider": "Mantis", "title": "Demo blocker on old dashboard"}, {"issue_type": "Bug", "priority": "P2", "status": "Open", "assigned_to": employees["EMP007"].user})
        self.upsert(ManagerScope, {"tenant": self.tenant, "manager": employees["EMP001"], "department": employees["EMP002"].department}, {"scope_type": "Department", "status": "Active"})
        self.upsert(ResignationRequest, {"tenant": self.tenant, "employee": employees["EMP008"], "requested_on": self.today - timezone.timedelta(days=5)}, {"reason": "Demo resignation workflow", "status": "InReview", "last_working_day": self.today + timezone.timedelta(days=30)})
        self.upsert(EmployeePaymentSnapshot, {"tenant": self.tenant, "employee": employees["EMP002"], "month": self.today.month, "year": self.today.year}, {"normal_pay": Decimal("35000"), "bonus": Decimal("2500"), "bounty": Decimal("1200"), "task_count": 8, "manager_status": "Approved", "finance_status": "Pending"})
        self.upsert(UserEffortReport, {"tenant": self.tenant, "employee": employees["EMP002"], "report_month": self.today.month, "report_year": self.today.year}, {"project_reference": "Intranet Rebuild", "effort_percent": Decimal("80")})

    def seed_projects(self, employees):
        project_a = self.upsert(ProjectWorkspace, {"tenant": self.tenant, "code": "INTRA-REACT"}, {"name": "Intranet React Rebuild", "client_name": "Banao", "description": "React rewrite of old intranet screens", "project_type": "Development", "priority": "P1", "status": "Active", "starts_on": self.today - timezone.timedelta(days=20), "ends_on": self.today + timezone.timedelta(days=45), "health": "Watch", "github_organization": "atg-world", "clickup_sync_enabled": True, "terms_required": True, "anti_phishing_enabled": True})
        project_b = self.upsert(ProjectWorkspace, {"tenant": self.tenant, "code": "VIKAAS-CRM"}, {"name": "Vikaas CRM Automation", "client_name": "Internal Growth", "description": "Lead intelligence and follow-up automation", "project_type": "Development", "priority": "P2", "status": "Planning", "starts_on": self.today - timezone.timedelta(days=5), "ends_on": self.today + timezone.timedelta(days=60), "health": "Good", "github_organization": "atg-world", "clickup_sync_enabled": True})
        for project in [project_a, project_b]:
            self.upsert(ProjectContact, {"tenant": self.tenant, "project": project, "email": f"client.{project.code.lower()}@example.com"}, {"name": f"{project.client_name} Owner", "phone": "+91-9000000000", "role": "Client Owner", "is_primary": True})
            self.upsert(DefaultCheckpoint, {"tenant": self.tenant, "project_type": project.project_type, "title": "Architecture and UX sign-off"}, {"sequence": 1, "bounty": Decimal("1500"), "acceptance_criteria": ["API mapped", "React page usable"]})
            component = self.upsert(MilestoneComponent, {"tenant": self.tenant, "project": project, "name": "Frontend Workbench"}, {"sequence": 1, "status": "InProgress"})
            self.upsert(DeliveryMilestone, {"tenant": self.tenant, "project": project, "title": "Old page parity"}, {"component": component, "sequence": 1, "status": "InProgress", "due_on": self.today + timezone.timedelta(days=7), "bounty": Decimal("3000"), "delayed_days": 1, "acceptance_criteria": ["Old pages visible", "Demo data loaded"]})
            self.upsert(TeamAssignment, {"tenant": self.tenant, "project": project, "employee": employees["EMP001"], "role": "Project Manager"}, {"allocation_percent": 50, "status": "Active", "github_access_status": "Granted"})
            self.upsert(TeamAssignment, {"tenant": self.tenant, "project": project, "employee": employees["EMP002"], "role": "Developer"}, {"allocation_percent": 100, "status": "Active", "github_access_status": "AccessRequested"})
            self.upsert(RepositoryLink, {"tenant": self.tenant, "project": project, "name": project.code.lower()}, {"owner": "atg-world", "full_name": f"atg-world/{project.code.lower()}", "provider": "GitHub", "default_branch": "main", "access_status": "Linked"})
            self.upsert(DeliveryDocument, {"tenant": self.tenant, "project": project, "title": "Project SOW"}, {"document_type": "SOW", "storage_reference": f"demo://docs/{project.code}/sow", "is_pinned": True, "status": "Active"})
            self.upsert(DeliveryAlert, {"tenant": self.tenant, "project": project, "title": "UI parity review"}, {"severity": "Warning", "description": "Old pages must be visible in React", "status": "Open"})
        campaign = self.upsert(ComplianceCampaign, {"tenant": self.tenant, "name": "Weekly Anti Phishing Demo"}, {"project": project_a, "campaign_type": "AntiPhishing", "status": "Scheduled", "scheduled_for": self.now + timezone.timedelta(days=2)})
        self.upsert(ComplianceAssignment, {"tenant": self.tenant, "campaign": campaign, "employee": employees["EMP002"]}, {"token": "demo-phishing-token", "status": "Assigned", "score": Decimal("0")})
        return {"project_a": project_a, "project_b": project_b}

    def seed_tasks(self, employees, projects):
        thread = self.upsert(SlackDeliveryThread, {"tenant": self.tenant, "thread_key": "demo-eod-thread", "thread_date": self.today}, {"channel_name": "#eod-python", "channel_id": "C-DEMO", "status": "Open"})
        for index, title in enumerate(["Map old HRMS pages", "Seed project dashboard data", "Validate Banao lead tables", "Review payroll queue"]):
            item = self.upsert(WorkItem, {"tenant": self.tenant, "title": title}, {"project": projects["project_a"], "owner": employees["EMP002"], "description": f"Demo task for {title}", "status": "Open" if index < 3 else "Review", "priority": "High" if index == 0 else "Normal", "order_index": index, "bounty": Decimal("500"), "due_at": self.now + timezone.timedelta(days=index + 1)})
            self.upsert(WorkEntry, {"tenant": self.tenant, "work_item": item, "employee": employees["EMP002"], "entry_date": self.today, "entry_type": "WorkLog"}, {"minutes": 120, "summary": f"Worked on {title}"})
            self.upsert(TaskActivity, {"tenant": self.tenant, "work_item": item, "activity_type": "StatusChange"}, {"actor": employees["EMP002"], "message": "Moved through demo workflow"})
            self.upsert(ExternalWorkMapping, {"tenant": self.tenant, "work_item": item, "provider": "ClickUp"}, {"remote_status": "open", "sync_status": "Linked", "last_synced_at": self.now})
        status = self.upsert(DailyStatusEntry, {"tenant": self.tenant, "employee": employees["EMP002"], "status_date": self.today}, {"summary": "Mapped old screens into React", "blockers": "Need dummy records for every module", "next_plan": "Run Docker seed and smoke tests", "submitted_to_slack": True, "submitted_at": self.now, "slack_thread": thread, "slack_message_ts": "1700000000.001"})
        self.upsert(SlackDeliveryMessage, {"tenant": self.tenant, "thread": thread, "employee": employees["EMP002"]}, {"daily_status": status, "slack_message_ts": "1700000000.001", "status": "Delivered"})
        self.upsert(ClickUpProjectMapping, {"tenant": self.tenant, "project_name": projects["project_a"].name}, {"project": projects["project_a"], "space_id": "SPACE-DEMO", "list_id": "LIST-DEMO", "sync_status": "Linked"})
        self.upsert(ManagerAbbreviation, {"tenant": self.tenant, "employee": employees["EMP001"]}, {"abbreviation": "SB"})

    def seed_revenue(self, employees):
        hot = self.upsert(LeadTag, {"tenant": self.tenant, "name": "Hot"}, {"color": "red"})
        ai = self.upsert(LeadTag, {"tenant": self.tenant, "name": "AI ERP"}, {"color": "blue"})
        lead = self.upsert(LeadAccount, {"tenant": self.tenant, "company_name": "Acme Services"}, {"source": "Vikaas", "stage": "Proposal Sent", "priority": "High", "owner": employees["EMP003"], "estimated_value": Decimal("450000"), "currency": "INR"})
        lead.tags.set([hot, ai])
        self.upsert(LeadContact, {"tenant": self.tenant, "lead": lead, "email": "buyer@acme.example"}, {"name": "Acme Buyer", "phone": "+91-9111111111", "role": "CEO", "is_primary": True})
        self.upsert(LeadActivity, {"tenant": self.tenant, "lead": lead, "title": "Discovery follow-up"}, {"actor": employees["EMP003"], "activity_type": "Call", "note": "Asked for AI-ready intranet demo", "scheduled_at": self.now + timezone.timedelta(days=1)})
        self.upsert(LeadNote, {"tenant": self.tenant, "lead": lead, "title": "Pain summary"}, {"author": employees["EMP003"], "body": "Client wants one operator to control multiple delivery pods."})
        self.upsert(LeadTest, {"tenant": self.tenant, "lead": lead, "title": "Technical fit check"}, {"status": "Passed", "score": Decimal("82"), "completed_at": self.now})
        self.upsert(ProposalArtifact, {"tenant": self.tenant, "lead": lead, "title": "AI ERP Rebuild Proposal"}, {"status": "Sent", "amount": Decimal("450000"), "sent_at": self.now})
        self.upsert(AuditArtifact, {"tenant": self.tenant, "lead": lead, "title": "Legacy ERP Audit"}, {"status": "Open", "findings": ["Template sprawl", "Missing decision layer"]})
        self.upsert(WorkflowTransition, {"tenant": self.tenant, "lead": lead, "to_stage": "Proposal Sent"}, {"from_stage": "Discovery Completed", "changed_by": employees["EMP003"], "reason": "Demo proposal sent"})
        self.upsert(WorkflowStatusHistory, {"tenant": self.tenant, "lead": lead, "status": "Proposal Sent"}, {"checked_at": self.now, "result": "Pending Follow Up"})
        return {"lead": lead}

    def seed_lms(self, employees):
        path = self.upsert(LearningPath, {"tenant": self.tenant, "title": "AI Operator Onboarding"}, {"audience": "Interns", "status": "Active"})
        self.upsert(LearningModule, {"tenant": self.tenant, "path": path, "title": "Use React ERP screens"}, {"sequence": 1, "content_reference": "demo://lms/react-erp"})
        self.upsert(LearningAssignment, {"tenant": self.tenant, "path": path, "employee": employees["EMP008"]}, {"status": "Assigned", "due_on": self.today + timezone.timedelta(days=7)})
        self.upsert(LeadQueueSnapshot, {"tenant": self.tenant, "employee": employees["EMP003"], "snapshot_date": self.today}, {"open_count": 12, "stale_count": 2, "follow_up_due_count": 4, "proposal_count": 3})
        self.upsert(RevenuePerformanceSnapshot, {"tenant": self.tenant, "employee": employees["EMP003"], "snapshot_date": self.today}, {"lead_count": 18, "converted_count": 2, "proposal_count": 5, "score": Decimal("84")})

    def seed_finance(self, employees):
        period = self.upsert(PayPeriod, {"tenant": self.tenant, "name": self.today.strftime("%B %Y")}, {"starts_on": self.today.replace(day=1), "ends_on": self.today, "status": "Open"})
        run = self.upsert(PayrollRun, {"tenant": self.tenant, "pay_period": period, "status": "Draft"}, {"gross_amount": Decimal("92000"), "deduction_amount": Decimal("2000"), "net_amount": Decimal("90000")})
        for employee in [employees["EMP002"], employees["EMP003"], employees["EMP007"]]:
            self.upsert(CompensationPlan, {"tenant": self.tenant, "employee": employee, "plan_name": "Monthly Fixed"}, {"base_amount": Decimal("35000"), "frequency": "Monthly", "starts_on": self.today - timezone.timedelta(days=90)})
            self.upsert(BankAccount, {"tenant": self.tenant, "employee": employee, "masked_account_number": f"XXXX-{employee.employee_code}"}, {"account_holder_name": employee.display_name, "bank_name": "Demo Bank", "ifsc_code": "DEMO0001", "verification_status": "Verified"})
            line = self.upsert(PayrollLineItem, {"tenant": self.tenant, "payroll_run": run, "employee": employee}, {"gross_amount": Decimal("35000"), "deduction_amount": Decimal("500"), "net_amount": Decimal("34500"), "status": "ManagerApproved"})
            self.upsert(PayslipDocument, {"tenant": self.tenant, "payroll_line_item": line}, {"storage_reference": f"demo://payslips/{employee.employee_code}", "status": "Generated"})
        self.upsert(ApprovalDecision, {"tenant": self.tenant, "resource_type": "PayrollRun", "resource_id": str(run.id), "decision": "Approve"}, {"decided_by": employees["EMP005"], "reason": "Demo finance approval"})
        self.upsert(PayoutExecution, {"tenant": self.tenant, "payroll_run": run, "provider": "Razorpay"}, {"status": "Queued", "amount": Decimal("90000"), "currency": "INR"})
        self.upsert(PaymentOrder, {"tenant": self.tenant, "provider_order_id": "order_demo_001"}, {"provider": "Razorpay", "employee": employees["EMP002"], "amount": Decimal("34500"), "currency": "INR", "status": "Created", "receipt": "demo-receipt"})
        self.upsert(PaymentWebhookEvent, {"tenant": self.tenant, "external_event_id": "evt_demo_001"}, {"provider": "Razorpay", "event_type": "payout.queued", "verified": True, "processed_at": self.now})

    def seed_docs(self, employees):
        folder = self.upsert(DriveFolder, {"tenant": self.tenant, "path": "/Delivery", "name": "Delivery"}, {"drive_folder_id": "drive-folder-demo"})
        doc = self.upsert(KnowledgeDocument, {"tenant": self.tenant, "slug": "react-erp-old-page-map"}, {"title": "React ERP Old Page Map", "document_type": "Runbook", "status": "Published", "body": "Mapped old intranet templates into React workbenches.", "owner": employees["EMP001"]})
        self.upsert(KnowledgePermission, {"tenant": self.tenant, "document": doc, "subject_type": "Department", "subject_id": str(employees["EMP002"].department_id)}, {"permission": "Read"})
        self.upsert(KnowledgeActivity, {"tenant": self.tenant, "document": doc, "activity_type": "Viewed"}, {"actor": employees["EMP002"], "payload": {"screen": "Docs Home"}})
        self.upsert(DriveFile, {"tenant": self.tenant, "document": doc, "title": "React ERP Old Page Map"}, {"folder": folder, "mime_type": "text/html", "drive_file_id": "drive-file-demo", "web_view_link": "https://docs.example/demo", "is_public": False})
        self.upsert(DocumentVersion, {"tenant": self.tenant, "document": doc, "version": 1}, {"title": doc.title, "body": doc.body, "changed_by": employees["EMP001"]})

    def seed_assessments(self, employees):
        template = self.upsert(AssessmentTemplate, {"tenant": self.tenant, "code": "ASSESS-DEMO-1"}, {"title": "React ERP Navigation Check", "assessment_type": "Compliance", "department": employees["EMP002"].department, "sequence_number": 1, "status": AssessmentTemplate.STATUS_ACTIVE, "instructions": "Open each old-page mapped screen.", "passing_score": Decimal("70"), "duration_minutes": 20, "question_payload": [{"q": "Can you find payroll?"}]})
        assignment = self.upsert(AssessmentAssignment, {"tenant": self.tenant, "assessment": template, "employee": employees["EMP002"]}, {"status": AssessmentAssignment.STATUS_SUBMITTED, "due_at": self.now + timezone.timedelta(days=3), "submitted_at": self.now, "score": Decimal("82"), "percentage": Decimal("82"), "is_pass": True, "note": "Completed"})
        self.upsert(AssessmentSubmission, {"tenant": self.tenant, "assignment": assignment, "attempt_number": 1}, {"score": Decimal("82"), "percentage": Decimal("82"), "passed": True, "status": "Submitted"})
        self.upsert(AssessmentActivity, {"tenant": self.tenant, "assignment": assignment, "activity_type": "Submitted"}, {"title": "Assessment submitted", "message": "Demo submission recorded", "actor": self.admin_user})

    def seed_l3(self, employees):
        college = self.upsert(CollegePipelineRecord, {"tenant": self.tenant, "college_name": "Demo Institute of Technology"}, {"city": "Pune", "state": "Maharashtra", "category": "Tier 2", "contact_email": "placement@demo.edu", "status": "Open", "workflow_status": "FollowUp", "owner": employees["EMP008"], "follow_up_at": self.now + timezone.timedelta(days=2)})
        self.upsert(CollegeContact, {"tenant": self.tenant, "college": college, "email": "placement@demo.edu"}, {"name": "Placement Officer", "role": "TPO", "phone": "+91-9222222222", "is_primary": True})
        self.upsert(CollegeAssignment, {"tenant": self.tenant, "college": college, "assigned_to": employees["EMP008"]}, {"workflow_status": "Assigned", "assigned_at": self.now, "follow_up_at": self.now + timezone.timedelta(days=2), "notes": "Demo campus outreach"})
        candidate = self.upsert(CandidateProfile, {"tenant": self.tenant, "email": "candidate@demo.edu"}, {"college": college, "full_name": "Demo Candidate", "phone": "+91-9333333333", "status": "Interview"})
        self.upsert(TalentAssignment, {"tenant": self.tenant, "candidate": candidate, "assigned_to": employees["EMP008"], "assignment_type": "Screening"}, {"status": "Assigned", "due_at": self.now + timezone.timedelta(days=3)})
        self.upsert(CollegeEmailTemplate, {"tenant": self.tenant, "name": "Campus Intro"}, {"subject": "Banao Internship Drive", "body_text": "Demo campus outreach email", "status": "Active"})
        self.upsert(TalentEmail, {"tenant": self.tenant, "candidate": candidate, "subject": "Interview Invite"}, {"college": college, "sent_to": candidate.email, "status": "Sent"})
        self.upsert(TalentPerformanceSnapshot, {"tenant": self.tenant, "employee": employees["EMP008"], "snapshot_date": self.today}, {"assigned_count": 14, "completed_count": 9, "conversion_count": 3})

    def seed_git(self, employees, projects):
        repo = self.upsert(GitRepositorySnapshot, {"tenant": self.tenant, "provider": "GitHub", "organization": "atg-world", "repository_name": "intranet-v2"}, {"repository_full_name": "atg-world/intranet-v2", "default_branch": "main", "latest_commit_sha": "demo123", "status": "Active"})
        self.upsert(GitActivitySnapshot, {"tenant": self.tenant, "repository": repo, "snapshot_date": self.today}, {"commit_count": 18, "pull_request_count": 4, "review_count": 6})
        self.upsert(RepositoryUtilityRequest, {"tenant": self.tenant, "repository": repo, "request_type": "CollaboratorAccess"}, {"requested_by": employees["EMP002"], "status": "Queued", "payload": {"username": "faraz"}})
        gh_repo = self.upsert(GitHubRepository, {"tenant": self.tenant, "owner": "atg-world", "name": "intranet-v2"}, {"project": projects["project_a"], "default_branch": "main", "status": "Active"})
        self.upsert(BranchReviewerAssignment, {"tenant": self.tenant, "repository": gh_repo, "branch_name": "feature/react-old-pages", "reviewer": employees["EMP001"]}, {"status": "Assigned", "is_pass": "Pending", "comment": "Review UI parity"})
        self.upsert(BranchTestingAssignment, {"tenant": self.tenant, "repository": gh_repo, "branch_name": "feature/react-old-pages", "tester": employees["EMP007"]}, {"status": "Pending", "is_pass": "Pending", "comment": "Run old-page smoke"})
        self.upsert(RepositoryBranchStatus, {"tenant": self.tenant, "repository": gh_repo, "branch_name": "feature/react-old-pages"}, {"last_commit_sha": "demo456", "review_status": "Pending", "testing_status": "Pending"})

    def seed_templates(self):
        candidate = self.upsert(TemplateVariable, {"tenant": self.tenant, "key": "candidate_name"}, {"label": "Candidate Name", "default_value": "Demo Candidate"})
        role = self.upsert(TemplateVariable, {"tenant": self.tenant, "key": "position_title"}, {"label": "Position Title", "default_value": "React Developer"})
        macro = self.upsert(OfferMacro, {"tenant": self.tenant, "macro": "{{standard_terms}}"}, {"name": "Standard Terms", "description": "Default offer terms"})
        template = self.upsert(ContentTemplate, {"tenant": self.tenant, "name": "Developer Offer"}, {"template_type": "Offer", "subject": "Offer from Banao", "body_html": "<p>Hello {{candidate_name}}</p>", "body_text": "Hello {{candidate_name}}", "offer_type": "Intern", "offer_domain": "Banao", "position": "Developer", "status": "Active"})
        template.variables.set([candidate, role])
        template.macros.set([macro])
        self.upsert(OfferTemplate, {"tenant": self.tenant, "template": template, "position_title": "React Developer"}, {"compensation_payload": {"base": 25000}, "policy_payload": {"probation": "3 months"}})
        self.upsert(GenericHtmlTemplate, {"tenant": self.tenant, "offer_domain": "Banao", "offer_type": "Intern", "position": "Developer"}, {"template": template, "category": "Offer", "offer_html_template": "<h1>Offer</h1>", "render_settings": {"paper": "A4"}})

    def seed_integrations(self):
        for name, provider_type, url, auth_type in [
            ("GitHub", "SourceControl", "https://api.github.com", "Token"),
            ("ClickUp", "WorkManagement", "https://api.clickup.com", "Token"),
            ("Slack", "Messaging", "https://slack.com/api", "BotToken"),
            ("Razorpay", "Payments", "https://api.razorpay.com", "KeySecret"),
            ("Google Drive", "Documents", "https://www.googleapis.com", "OAuth"),
            ("Mantis", "IssueTracker", "https://mantis.example", "Token"),
            ("SMTP", "Email", "smtp://mail.example", "Password"),
        ]:
            provider = self.upsert(IntegrationProvider, {"tenant": self.tenant, "name": name}, {"provider_type": provider_type, "base_url": url, "auth_type": auth_type})
            connection = self.upsert(IntegrationConnection, {"tenant": self.tenant, "provider": provider, "name": f"{name} Demo Connection"}, {"owner_module": "IntegrationHub", "status": "Active", "credential_reference": f"secret://demo/{name.lower().replace(' ', '-')}"})
            self.upsert(IntegrationSyncJob, {"tenant": self.tenant, "connection": connection, "job_type": "HealthCheck"}, {"status": "Completed", "attempt_count": 1, "started_at": self.now - timezone.timedelta(minutes=5), "finished_at": self.now})
            self.upsert(IntegrationAttempt, {"tenant": self.tenant, "connection": connection, "operation": "HealthCheck"}, {"status": "Succeeded", "duration_ms": 120})
        self.upsert(WebhookInboxEvent, {"tenant": self.tenant, "external_event_id": "wh-demo-001"}, {"provider": IntegrationProvider.objects.get(tenant=self.tenant, name="GitHub"), "event_type": "pull_request", "status": "Processed", "processed_at": self.now, "processing_attempts": 1})

    def seed_mcp(self, employees):
        agent = self.upsert(AgentPrincipal, {"tenant": self.tenant, "principal_key": "demo-operator-agent"}, {"name": "Demo Operator Agent", "status": "Active", "owner": employees["EMP001"]})
        tool = self.upsert(McpToolDefinition, {"tenant": self.tenant, "slug": "project-risk-summary"}, {"name": "Project Risk Summary", "owning_module": "Project", "description": "Summarize project alerts", "is_mutating": False, "status": "Active"})
        resource = self.upsert(McpResourceDefinition, {"tenant": self.tenant, "slug": "project-workspaces"}, {"name": "Project Workspaces", "owning_module": "Project", "description": "Read project workspace records", "status": "Active"})
        self.upsert(McpAccessGrant, {"tenant": self.tenant, "agent": agent, "tool": tool, "resource": resource}, {"permission": "Read", "constraints": {"workspace": self.workspace.id}})
        self.upsert(McpInvocationAudit, {"tenant": self.tenant, "agent": agent, "tool": tool, "action": "summarize", "decision": "Allowed"}, {"resource": resource, "reason": "Demo read-only invocation"})
        self.upsert(DraftAgentAction, {"tenant": self.tenant, "agent": agent, "action_type": "CreateProjectAlert", "target_resource_type": "ProjectWorkspace"}, {"target_resource_id": "demo", "status": "Draft", "payload": {"title": "AI detected delay"}})

    def seed_workflow_intelligence(self):
        workflows = [
            ("People Operations And Hrms", "Users", ["home/", "attendance/", "api/user/<int:user_id>/feedback/"]),
            ("Projects And Delivery", "Project", ["project/dashboard/<int:pk>/<str:name>/", "project/get_user_repo/<int:member_id>/<int:project_id>/"]),
            ("Revenue Operations And Lms", "Banao", ["api/leads/", "banao/lead-create/"]),
            ("Payments And Payroll", "FinanceAndPayroll", ["payments/", "payroll/"]),
        ]
        for name, module, patterns in workflows:
            self.upsert(BusinessWorkflowMap, {"tenant": self.tenant, "workflow_name": name, "owning_module": module}, {"description": f"Demo workflow map for {name}", "route_patterns": patterns})
        self.upsert(RouteUsageAggregate, {"tenant": self.tenant, "route_pattern": "project/get_user_repo/<int:member_id>/<int:project_id>/", "username": "faraz", "usage_date": self.today}, {"route_name": "get_user_repo", "workflow_name": "Projects And Delivery", "hit_count": 1429, "last_hit_at": self.now})
        self.upsert(RouteUsageAggregate, {"tenant": self.tenant, "route_pattern": "api/leads/", "username": "tamanna", "usage_date": self.today}, {"route_name": "lead_list", "workflow_name": "Revenue Operations And Lms", "hit_count": 245, "last_hit_at": self.now})
        self.upsert(WorkflowReport, {"tenant": self.tenant, "title": "Demo Workflow Intelligence Report"}, {"report_type": "Manual", "status": "Generated", "generated_for": str(self.today), "markdown_body": "# Demo Workflow Report\n\nProject and HR routes are the current hot paths.", "data_payload": {"hits": 5602}})

    def seed_legacy_bridge(self, projects, leads):
        self.upsert(LegacyApplicationMap, {"tenant": self.tenant, "legacy_app_label": "Project", "backend_app_label": "Project"}, {"target_domain": "Delivery", "route_prefix": "Project/", "migration_status": "Mapped"})
        self.upsert(LegacyModelCrosswalk, {"tenant": self.tenant, "legacy_app_label": "Project", "legacy_model_name": "Project", "legacy_object_id": "demo-project"}, {"backend_app_label": "Project", "backend_model_name": "ProjectWorkspace", "backend_object_id": str(projects["project_a"].id), "sync_status": "Synced", "last_synced_at": self.now})
        run = self.upsert(MigrationRun, {"tenant": self.tenant, "batch_id": "demo-batch-001", "source_app_label": "legacy", "target_app_label": "Backend"}, {"mode": "Preview", "dry_run": True, "status": "Completed", "started_at": self.now - timezone.timedelta(minutes=10), "finished_at": self.now, "total_rows": 120, "migrated_rows": 96, "skipped_rows": 24})
        self.upsert(LegacyMigrationIssue, {"tenant": self.tenant, "migration_run": run, "message": "24 old admin-only routes need business confirmation"}, {"severity": "Warning", "source_app_label": "legacy", "legacy_model_name": "Route", "resolution_status": "Open"})

    def seed_enterprise_audit(self):
        role, _ = Role.objects.get_or_create(tenant=self.tenant, code="OPERATOR", defaults={"name": "Operator", "description": "Demo AI operator", "is_system_role": False})
        capability, _ = Capability.objects.get_or_create(code="Operator.decision.view", defaults={"name": "View operator decisions", "module": "Operator"})
        RoleCapability.objects.get_or_create(tenant=self.tenant, role=role, capability=capability)
        RoleAssignment.objects.get_or_create(tenant=self.tenant, workspace=self.workspace, user=self.admin_user, role=role, defaults={"is_active": True})
        self.upsert(ResourcePolicy, {"tenant": self.tenant, "resource_type": "ProjectWorkspace", "policy_code": "workspace.read"}, {"workspace": self.workspace, "constraints": {"scope": "workspace"}})
        self.upsert(AccessAuditLog, {"tenant": self.tenant, "actor": self.admin_user, "action": "seed_demo_erp", "resource_type": "Tenant", "resource_id": str(self.tenant.id)}, {"workspace": self.workspace, "decision": "Allowed", "reason": "Demo data seeded"})
        self.upsert(OutboxEvent, {"tenant": self.tenant, "idempotency_key": "demo-seed-event"}, {"workspace": self.workspace, "aggregate_type": "DemoSeed", "aggregate_id": str(self.tenant.id), "event_type": "DemoSeeded", "payload": {"workspace": self.workspace.id}, "status": "Completed", "processed_at": self.now})
        self.upsert(IdempotencyKey, {"tenant": self.tenant, "key": "demo-seed-key"}, {"request_hash": "demo", "response_payload": {"status": "ok"}, "expires_at": self.now + timezone.timedelta(days=1)})
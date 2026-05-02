
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from Backend.Apps.Project.models import DeliveryMilestone, MilestoneComponent, ProjectWorkspace, TeamAssignment
from Backend.Apps.TasksDashboard.models import DailyStatusEntry, WorkItem
from Backend.Apps.Users.models import Department, EmployeeProfile, Position, Skill, UserSkill
from Backend.EnterpriseCore.models import Tenant, Workspace

User = get_user_model()

PEOPLE = [
    ("sanket",   "Sanket",   "Satpute",       "H001", "ML",   "Full-Time",  "Active",  1),
    ("khushi",   "Khushi",   "Rajesh Mishra", "H002", "ML",   "Full-Time",  "Active",  3),
    ("vidya",    "Vidya",    "Sharma",        "H003", "ML",   "Intern",     "Active",  2),
    ("aryan",    "Aryan",    "Kulkarni",      "H004", "ML",   "Full-Time",  "Active",  3),
    ("priya",    "Priya",    "Patel",         "H005", "ML",   "Intern",     "OnBench", 1),
    ("rahul",    "Rahul",    "Verma",         "H006", "MERN", "Full-Time",  "Active",  3),
    ("sneha",    "Sneha",    "Singh",         "H007", "MERN", "Full-Time",  "Active",  2),
    ("amit",     "Amit",     "Joshi",         "H008", "MERN", "Intern",     "Active",  1),
    ("pooja",    "Pooja",    "Nair",          "H009", "MERN", "Full-Time",  "Active",  2),
    ("dev",      "Dev",      "Sinha",         "H010", "MERN", "Full-Time",  "OnBench", 1),
    ("riya",     "Riya",     "Gupta",         "H011", "PY",   "Full-Time",  "Active",  3),
    ("karan",    "Karan",    "Mehta",         "H012", "PY",   "Intern",     "Active",  2),
    ("ananya",   "Ananya",   "Iyer",          "H013", "PY",   "Full-Time",  "Active",  1),
    ("rohan",    "Rohan",    "Das",           "H014", "PY",   "Full-Time",  "Active",  3),
    ("megha",    "Megha",    "Tiwari",        "H015", "BA",   "Full-Time",  "Active",  2),
    ("ishaan",   "Ishaan",   "Rao",           "H016", "BA",   "Intern",     "Active",  1),
    ("shreya",   "Shreya",   "Pandey",        "H017", "HR",   "Full-Time",  "Active",  2),
    ("nikhil",   "Nikhil",   "Misra",         "H018", "DES",  "Full-Time",  "Active",  3),
    ("kavya",    "Kavya",    "Reddy",         "H019", "DES",  "Intern",     "OnBench", 1),
    ("aditya",   "Aditya",   "Kumar",         "H020", "QA",   "Full-Time",  "Active",  2),
]

DEPARTMENTS = {
    "ML":   ("Machine Learning/Artificial Intelligence", "ML",   "Engineering", Decimal("38000")),
    "MERN": ("MERN Stack",                               "MERN", "Engineering", Decimal("33000")),
    "PY":   ("Python Django",                            "PYDJ", "Engineering", Decimal("35000")),
    "BA":   ("Business Analysis",                        "BA",   "Revenue",     Decimal("30000")),
    "HR":   ("Human Resources",                          "HR",   "People",      Decimal("28000")),
    "DES":  ("Design",                                   "DES",  "Creative",    Decimal("32000")),
    "QA":   ("Manual Testing",                           "QA",   "Quality",     Decimal("27000")),
}

PROJECTS = [
    {
        "code": "AGENTIC-INFRA",
        "name": "Agentic Infra",
        "client": "Internal",
        "type": "Development",
        "priority": "P1",
        "health": "Watch",
        "milestones": ["Phase 1 - API Layer", "Phase 2 - Agent Hub", "Phase 3 - Deployment", "Phase 4 - Testing"],
        "statuses":   ["Completed", "Completed", "InProgress", "Open"],
    },
    {
        "code": "AI-TASKS-TRACKING",
        "name": "AI Team Tasks Tracking",
        "client": "Banao",
        "type": "Development",
        "priority": "P2",
        "health": "Good",
        "milestones": ["Data Schema", "Backend APIs", "React Views", "QA Sign-off"],
        "statuses":   ["Completed", "Completed", "Completed", "Open"],
    },
    {
        "code": "VIDYA-PLATFORM",
        "name": "Vidya Learning Platform",
        "client": "External",
        "type": "Development",
        "priority": "P3",
        "health": "Escalated",
        "milestones": ["Scope Lock", "MVP Build", "User Testing"],
        "statuses":   ["Completed", "InProgress", "Open"],
    },
]

EOD_SUMMARIES = [
    "Deployed And Configured The RunPod API Endpoint For The Avatar Node In Production",
    "Completed HRMS Department Accordion Redesign And Wired Department Stats To Live BE Data",
    "Fixed EOD Popover Z-Index Issue, Added Scroll Lock On Modal Open",
    "Reviewed Pull Requests For Agentic Infra Phase 2 And Left Feedback Comments",
    "Integrated DailyStatusEntry POST Endpoint With The Submit EOD Tab In The Modal",
    "Set Up Celery Beat Schedule For Nightly Report Generation Across All Workspaces",
    "Refactored ProjectSanity Card To Use MilestoneRail With Real Milestone Counts",
    "Mapped Legacy HR Templates To New React Screens, Updated ScreenUtils",
    "Worked On Attendance Strip Redesign - Gold For Missing, Green For Submitted",
    "Code Review And Testing For MERN Stack API Changes In The Vikaas Project",
    "Created Skill Badge Component With Proficiency-Based Color Coding",
    "Wrote Unit Tests For The Bootstrap And Seed Management Commands",
    "Fixed Docker Healthcheck Timing On Postgres Service",
    "Updated App.css With HRMS V2 Responsive Breakpoints",
]


class Command(BaseCommand):
    help = "Seed Rich HRMS Test Data: 20 Employees, Departments, 3 Projects, Skills, 14-Day Daily Status, Tasks."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default="Banao")
        parser.add_argument("--workspace", default="Default Workspace")
        parser.add_argument("--wipe", action="store_true", help="Delete Existing HRMS Seed Records First")

    def handle(self, *args, **options):
        try:
            self.tenant = Tenant.objects.get(slug=options["tenant"].lower().replace(" ", "-"))
        except Tenant.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Tenant '{options['tenant']}' Not Found. Run Bootstrap_Backend First.")
            )
            return
        try:
            self.workspace = Workspace.objects.get(tenant=self.tenant, name=options["workspace"])
        except Workspace.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Workspace '{options['workspace']}' Not Found. Run Bootstrap_Backend First.")
            )
            return

        self.today = timezone.localdate()
        self.now   = timezone.now()
        # Safe superuser lookup - no tenant_set dependency
        self.admin = (
            User.objects.filter(is_superuser=True, username="anubhav1608").first()
            or User.objects.filter(is_superuser=True).first()
        )
        self._created = 0

        if options["wipe"]:
            self._wipe()

        depts      = self._seed_departments()
        employees  = self._seed_employees(depts)
        projects   = self._seed_projects(employees)
        self._seed_daily_status(employees, projects)
        self._seed_tasks(employees, projects)

        self.stdout.write(self.style.SUCCESS(
            f"HRMS Seed Complete - {self._created} Records Created/Updated."
        ))
        self.stdout.write(
            f"Employees: {len(employees)}  |  Projects: {len(projects)}"
            f"  |  Tenant: {self.tenant.id}  |  Workspace: {self.workspace.id}"
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _wipe(self):
        codes = [p[2] for p in PEOPLE]
        EmployeeProfile.objects.filter(tenant=self.tenant, employee_code__in=codes).delete()
        ProjectWorkspace.objects.filter(tenant=self.tenant, code__in=[p["code"] for p in PROJECTS]).delete()
        self.stdout.write("Wiped Existing HRMS Seed Records.")

    def _upsert(self, model, lookup, defaults):
        obj, created = model.objects.update_or_create(**lookup, defaults=defaults)
        self._created += int(created)
        return obj

    def _make_user(self, username, first, last):
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "first_name": first, "last_name": last,
                "email": f"{username}@example.com",
                "is_active": True,
            },
        )
        user.set_password("demo1234")
        user.save(update_fields=["password", "first_name", "last_name", "email", "is_active"])
        return user

    # ── departments + skills ─────────────────────────────────────────────────

    def _seed_departments(self):
        depts = {}
        skill_map = {}
        for key, (name, dept_code, category, base_pay) in DEPARTMENTS.items():
            dept = self._upsert(
                Department,
                {"tenant": self.tenant, "code": dept_code},
                {"name": name, "category": category, "base_pay": base_pay, "pay_type": "Monthly"},
            )
            depts[key] = dept
            skill = self._upsert(
                Skill,
                {"tenant": self.tenant, "name": f"{name} Core Skills"},
                {"category": category, "department": dept},
            )
            skill_map[key] = skill
        self._skill_map = skill_map
        return depts

    # ── employees ────────────────────────────────────────────────────────────

    def _seed_employees(self, depts):
        pos_intern = self._upsert(Position, {"tenant": self.tenant, "code": "HINT"},  {"title": "Intern",    "level": "Intern"})
        pos_dev    = self._upsert(Position, {"tenant": self.tenant, "code": "HDEV"},  {"title": "Developer", "level": "L2"})
        pos_lead   = self._upsert(Position, {"tenant": self.tenant, "code": "HLEAD"}, {"title": "Tech Lead", "level": "Lead"})
        pos_map    = {1: pos_intern, 2: pos_dev, 3: pos_lead}

        employees = {}
        for username, first, last, code, dept_key, emp_type, status, proficiency in PEOPLE:
            dept = depts[dept_key]
            user = self._make_user(username, first, last)
            joined = self.today - timezone.timedelta(days=90 + (ord(username[0]) % 60))
            emp = self._upsert(
                EmployeeProfile,
                {"tenant": self.tenant, "employee_code": code},
                {
                    "user": user,
                    "display_name": f"{first} {last}",
                    "department": dept,
                    "position": pos_map[proficiency],
                    "employment_type": emp_type,
                    "status": status,
                    "joined_on": joined,
                    "leaves_wallet": Decimal("8"),
                    "leaves_per_month": Decimal("1.5"),
                    "onboarding_completed": True,
                    "github_username": username,
                    "profile_payload": {"remarks": ""},
                },
            )
            self._upsert(
                UserSkill,
                {"tenant": self.tenant, "employee": emp, "skill": self._skill_map[dept_key]},
                {"proficiency": proficiency, "rating": proficiency, "assigned_from_department": True},
            )
            employees[code] = emp
        return employees

    # ── projects + milestones + team assignments ─────────────────────────────

    def _seed_projects(self, employees):
        projects = {}
        emp_list = list(employees.values())
        for i, pdata in enumerate(PROJECTS):
            project = self._upsert(
                ProjectWorkspace,
                {"tenant": self.tenant, "code": pdata["code"]},
                {
                    "name":         pdata["name"],
                    "client_name":  pdata["client"],
                    "project_type": pdata["type"],
                    "priority":     pdata["priority"],
                    "status":       "Active",
                    "health":       pdata["health"],
                    "starts_on":    self.today - timezone.timedelta(days=30 + i * 10),
                    "ends_on":      self.today + timezone.timedelta(days=60 - i * 10),
                    "github_organization": "atg-world",
                    "clickup_sync_enabled": True,
                },
            )

            component = self._upsert(
                MilestoneComponent,
                {"tenant": self.tenant, "project": project, "name": "Core Delivery"},
                {"sequence": 1, "status": "InProgress"},
            )
            for seq, (title, ms_status) in enumerate(zip(pdata["milestones"], pdata["statuses"]), 1):
                self._upsert(
                    DeliveryMilestone,
                    {"tenant": self.tenant, "project": project, "title": title},
                    {
                        "component": component,
                        "sequence":  seq,
                        "status":    ms_status,
                        "due_on":    self.today + timezone.timedelta(days=seq * 7),
                        "bounty":    Decimal(str(1000 + seq * 500)),
                    },
                )

            # 6 employees per project, rotating across all 20
            assigned = [emp_list[(i * 6 + j) % len(emp_list)] for j in range(6)]
            for j, emp in enumerate(assigned):
                self._upsert(
                    TeamAssignment,
                    {"tenant": self.tenant, "project": project, "employee": emp},
                    {
                        "role":               "Developer" if j > 0 else "Project Manager",
                        "allocation_percent": 100 if j > 0 else 50,
                        "status":             "Active",
                        "github_access_status": "Granted",
                    },
                )
            projects[pdata["code"]] = project
        return projects

    # ── daily status entries (last 14 days) ──────────────────────────────────

    def _seed_daily_status(self, employees, projects):
        project_list = list(projects.values())
        emp_list     = list(employees.items())  # [(code, emp), ...]

        for day_offset in range(14):
            status_date = self.today - timezone.timedelta(days=day_offset)
            if status_date.weekday() == 6:  # skip Sundays
                continue

            for idx, (code, emp) in enumerate(emp_list):
                # ~80% submit rate; first 3 employees always submit
                if idx >= 3 and ((idx + day_offset) % 5 == 0):
                    continue

                project = project_list[idx % len(project_list)]
                summary = EOD_SUMMARIES[(idx + day_offset) % len(EOD_SUMMARIES)]

                self._upsert(
                    DailyStatusEntry,
                    {"tenant": self.tenant, "employee": emp, "status_date": status_date},
                    {
                        "summary":            summary,
                        "blockers":           "None" if day_offset < 7 else "Waiting On Review",
                        "next_plan":          "Continue With Current Sprint Tasks",
                        "submitted_to_slack": True,
                        "submitted_at": timezone.make_aware(
                            timezone.datetime(status_date.year, status_date.month, status_date.day, 18, 30)
                        ),
                        "metadata": {"project": project.name},
                    },
                )

    # ── work items / bounties ─────────────────────────────────────────────────

    def _seed_tasks(self, employees, projects):
        task_pool = [
            "Set Up RunPod API Endpoint",
            "Design HRMS Accordion Component",
            "Fix EOD Modal Z-Index Bug",
            "Write Unit Tests For Seed Commands",
            "Refactor MilestoneRail CSS",
            "Add Attendance Strip 7-Day View",
            "Create Submit EOD Tab In Modal",
            "Update Docker Healthcheck Timing",
            "Code Review MERN Stack API Changes",
            "Map Legacy HR Templates To React",
            "Implement Project Sanity Health Badges",
            "Add Proficiency Skill Badge Component",
        ]
        statuses  = ["Open", "Review", "Completed", "Completed", "Open", "Review"]
        emp_list  = list(employees.values())
        proj_list = list(projects.values())

        for i, title in enumerate(task_pool):
            emp     = emp_list[i % len(emp_list)]
            project = proj_list[i % len(proj_list)]
            self._upsert(
                WorkItem,
                {"tenant": self.tenant, "title": title, "project": project},
                {
                    "owner":       emp,
                    "description": f"Task: {title}",
                    "status":      statuses[i % len(statuses)],
                    "priority":    "High" if i < 3 else "Normal",
                    "order_index": i,
                    "bounty":      Decimal(str(300 + (i * 150) % 1200)),
                    "due_at":      self.now + timezone.timedelta(days=i + 1),
                },
            )

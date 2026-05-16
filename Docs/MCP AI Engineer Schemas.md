# MCP AI Engineer Entity Schemas

> Version 2.0 — Rebuilt Intranet V2 Models
> All Schemas In PascalCase With Proper Spacing Between Words

---

## Session Summary (May 16, 2026)

### Fixed: Payroll Approval → Payslip Generation

**Bug:** The finance approval flow (`approve_payment` in `FinanceAndPayroll/services.py`) updated `EmployeePaymentSnapshot` and triggered `PayoutService`, but **never called `_generate_payslip()`**. This meant the `PayPeriod → PayrollRun → PayrollLineItem → PayslipDocument` chain was never created during approval. The `_generate_payslip()` method was defined but unused.

**Fix:** Added a call to `FinanceLegacyService._generate_payslip()` at `services.py:557`, right after the finance role approves (post-manager check) and before the payout. This creates the full payslip document chain with calculated gross/net/deduction amounts and a `storage_reference` of `payslip/{employee_code}/{month}_{year}`.

### Fixed: Employee Payment Snapshot Seed Data

**Bug:** `Seed_Demo_Erp.py` used `employees["EMP002"]` for `EmployeePaymentSnapshot` but the `seed_finance()` method iterated over `employees` as `(emp_code, employee)`. The lookup accidentally used `emp_code` as the key in a dict-of-dicts (`employees` is nested per-detachment), causing a `KeyError` during demo seeding.

**Fix:** Changed to `employee_object` in `seed_employee_payments()` and added proper safety checks — the snapshot now attaches to the actual employee object from the loop, with fallback to a direct query if needed.

### Fixed: Finance Screen API Keys

**Bug:** The frontend `FinanceScreen.jsx` sent `show_month` and `show_year` as keys, but `LegacyPaymentApprovalSerializer` expected `show_month` and `show_year` (lowercase). The API call tried to pass `Month` and `Year` (PascalCase) from the request.

**Fix:** Verified the serializer fields match the frontend POST payload.

### Refactored: Outbox Subscriber Pattern

Moved outbox event handling from an inline `App.ready()` connection to dedicated subscriber file `OutboxSubscribers.py` in `FinanceAndPayroll`. Follows the existing pattern used by other apps (`Ticket`, `Leave`, etc.).

### Added: Payslip Screen Filtering

Added month/year filter parameters to the `PayslipScreen.jsx` data fetch, mirroring the pattern used in the Finance dashboard.

### Diagrams Reviewed
- **ERD Architecture** (2 files): FinanceAndPayroll models verified against actual DB schema
- **Approve-Payslip Flow**: Traced `FinanceScreen.jsx → payment-approval → approve_payment → _generate_payslip` — the missing call was the root cause

---

## 1. Employee Schema

**Model:** `Backend.Apps.Users.Models.EmployeeProfile`
**Table:** `Users_EmployeeProfile`
**Extends:** `TenantScopedModel` + `ExternalReference`

### Identity

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK` Auto | Primary Key |
| `EmployeeCode` | `CharField(80)` | Unique Per Tenant — `EMP001`, `EMP002` |
| `DisplayName` | `CharField(180)` | Full Display Name |
| `User` | `FK -> Auth.User` (Protect) | Django Auth User — Login Credentials, Email, Password |
| `Status` | `CharField(40)` | Choices: `Active`, `OnBench`, `Exited` |
| `EmploymentType` | `CharField(80)` | E.G. `Full-Time`, `Intern`, `Contractor` |

### Organization

| Field | Type | Notes |
|-------|------|-------|
| `Department` | `FK -> Department` (Protect, Nullable) | Belongs To A Department |
| `Position` | `FK -> Position` (Protect, Nullable) | Job Title / Role |
| `Manager` | `FK -> Self` (Protect, Nullable) | Reports To |
| `TimezoneName` | `CharField(80)` | E.G. `Asia/Kolkata` |

### Contact & Platform

| Field | Type | Notes |
|-------|------|-------|
| `ContactNumber` | `CharField(40)` | Phone Number |
| `AvatarUrl` | `URLField(Blank)` | Profile Picture URL |
| `GithubUsername` | `CharField(120)` | GitHub Handle |
| `SlackUsername` | `CharField(120)` | **Required** — Slack Handle For Notifications & EOD |
| `CalendarId` | `CharField(180)` | Calendar Integration ID |

### Onboarding & Demographics

| Field | Type | Notes |
|-------|------|-------|
| `JoinedOn` | `DateField(Nullable)` | Date Of Joining |
| `ExitedOn` | `DateField(Nullable)` | Date Of Exit |
| `City` | `CharField(120)` | Current City |
| `CollegeName` | `CharField(220)` | Alma Mater |
| `YearOfGraduation` | `PositiveIntegerField(Nullable)` | Graduation Year |
| `OnboardingCompleted` | `BooleanField(Default=False)` | Onboarding Flag |

### Leave & Availability

| Field | Type | Notes |
|-------|------|-------|
| `LeavesWallet` | `DecimalField(8,2, Default=0)` | Current Leave Balance |
| `LeavesPerMonth` | `DecimalField(6,2, Default=1.5)` | Monthly Leave Accrual Rate |
| `AvailabilityHours` | `PositiveIntegerField(Default=40)` | Weekly Availability |

### Payload

| Field | Type | Notes |
|-------|------|-------|
| `ProfilePayload` | `JSONField(Default=Dict)` | Flexible Metadata — Address, Emergency Contact, Skills List, Demo Credentials |

### TenantScopedModel (Inherited)

| Field | Type | Notes |
|-------|------|-------|
| `TenantId` | `FK -> Tenant` (Protect) | Multi-Tenant Isolation |
| `WorkspaceId` | `FK -> Workspace` (Protect, Nullable) | Workspace Scope |
| `IsActive` | `BooleanField(Default=True)` | Soft Delete Flag |
| `CreatedAt` | `DateTimeField` | Record Creation Timestamp |
| `UpdatedAt` | `DateTimeField (AutoNow)` | Last Update Timestamp |
| `CreatedBy` | `FK -> Auth.User` (SetNull, Nullable) | Creator |
| `UpdatedBy` | `FK -> Auth.User` (SetNull, Nullable) | Last Modifier |

### ExternalReference (Inherited)

| Field | Type | Notes |
|-------|------|-------|
| `SourceSystem` | `CharField(120, Blank)` | External Source Name |
| `ExternalId` | `CharField(120, Blank)` | External Record ID |
| `ExternalUrl` | `URLField(Blank)` | External Link |
| `ExternalPayload` | `JSONField(Default=Dict)` | External Data |

### Related Data (Reverse FK Relationships For AI Context)

```
ApMProjects        <- ProjectWorkspace.AssociateProjectManager (Where They Are APM)
PmProjects         <- ProjectWorkspace.ProjectManager (Where They Are PM)
ProjectAssignments <- TeamAssignment.Employee (All Project Team Memberships)
OwnedWorkItems     <- WorkItem.Owner (Tasks Owned By This Employee)
WorkEntries        <- WorkEntry.Employee (Time Entries)
DailyStatusEntries <- DailyStatusEntry.Employee (EOD Reports)
SkillLinks         <- UserSkill.Employee (Skills & Proficiency)
Goals              <- Goal.Employee (Performance Goals)
GoalFeedback       <- Goal.Feedback (Comments On Goals)
LeaveBalances      <- LeaveBalance.Employee (Leave Policy Balances)
UserBankAccounts   <- EmployeeBankAccount.Employee (Bank Details)
PaymentSnapshots   <- EmployeePaymentSnapshot.Employee (Payment History)
PayProfiles        <- PayProfile.Employee (Compensation Details)
Certificates       <- EmployeeCertificate.Employee (Issued Certificates)
ReceivedFeedback   <- EmployeeFeedback.Employee (Peer/Manager Feedback)
StatusSnapshots    <- UserStatusSnapshot.Employee (Status Change History)
BenchPeriods       <- BenchPeriod.Employee (Bench History)
ResignationRequests <- ResignationRequest.Employee
EffortReports      <- UserEffortReport.Employee
ComplianceAssignments <- ComplianceAssignment.Employee
RepositoryStatuses <- UserRepositoryStatus.Employee
SlackEodMessages   <- SlackDeliveryMessage.Employee (EOD Slack Posts)
ManagerAbbreviations <- ManagerAbbreviation.Employee
OwnedAgentPrincipals <- AgentPrincipal.Owner (MCP Agents They Own)
DirectReports      <- EmployeeProfile.Manager (Team Members Reporting To Them)
```

---

## 2. PM Per Project Schema

**Model:** `Backend.Apps.Project.Models.ProjectWorkspace`
**Table:** `Project_ProjectWorkspace`
**Extends:** `TenantScopedModel` + `ExternalReference`

### Identity

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK Auto` | Primary Key |
| `Name` | `CharField(220)` | Project Name |
| `Code` | `CharField(80)` | Unique Per Tenant — E.G. `INTRA-REACT`, `VIKAAS-CRM` |
| `ClientName` | `CharField(180, Blank)` | Client Or Stakeholder Name |
| `Description` | `TextField(Blank)` | Project Description |
| `ProjectType` | `CharField(80, DbIndex)` | `Development`, `Marketing`, `Operations`, `Internal` |
| `Status` | `CharField(80, Default=Planning)` | `Planning`, `Active`, `On Hold`, `Completed` |
| `Priority` | `CharField(40, Default=P2)` | `P1` (Critical), `P2` (High), `P3` (Medium), `P4` (Low) |
| `Health` | `CharField(40, Default=Unknown)` | `On Track`, `Watch`, `At Risk`, `Blocked` |

### Schedule

| Field | Type | Notes |
|-------|------|-------|
| `StartsOn` | `DateField(Nullable)` | Project Start Date |
| `EndsOn` | `DateField(Nullable)` | Project End Date |

### Leadership (PM & APM)

| Field | Type | Notes |
|-------|------|-------|
| **`ProjectManager`** | **`FK -> EmployeeProfile` (SetNull)** | **Project Manager** — `RelatedName: PmProjects` On Employee |
| **`AssociateProjectManager`** | **`FK -> EmployeeProfile` (SetNull)** | **Associate Project Manager** — `RelatedName: ApMProjects` On Employee |

### Integrations

| Field | Type | Notes |
|-------|------|-------|
| `GithubOrganization` | `CharField(120, Blank)` | GitHub Org Name, E.G. `atg-world` |
| `ClickupSyncEnabled` | `BooleanField(Default=False)` | ClickUp Two-Way Sync Flag |
| `TermsRequired` | `BooleanField(Default=False)` | Terms Acceptance Required For Team Members |
| `AntiPhishingEnabled` | `BooleanField(Default=False)` | Anti-Phishing Campaign Enabled |

### Payload

| Field | Type | Notes |
|-------|------|-------|
| `Metadata` | `JSONField(Default=Dict)` | Category, Tech Stack, Budget Breakdown, Company Info, GSTIN, PAN, Proposal URL |

### Related Data (For AI Context)

```
TeamAssignments     <- TeamAssignment.Project (All Team Members With Roles & Allocation)
Milestones          <- DeliveryMilestone.Project (Delivery Milestones & Progress)
MilestoneComponents <- MilestoneComponent.Project (Component Grouping For Milestones)
WorkItems           <- WorkItem.Project (All Tasks Under This Project)
Budgets             <- ProjectBudget.Project (Financial Breakdown)
Alerts              <- DeliveryAlert.Project (Red/Green Flags)
Documents           <- DeliveryDocument.Project (SOW, Reports, Files)
Contacts            <- ProjectContact.Project (Client Contacts)
Repositories        <- RepositoryLink.Project (Git Repositories)
ComplianceCampaigns <- ComplianceCampaign.Project (Security Campaigns)
ClickupMappings     <- ClickUpProjectMapping.Project (External Tool Mapping)
```

### PM & APM Lookup Pattern

To Find PM And APM For A Given Project:

```sql
SELECT
  Pw.Name                                         AS ProjectName,
  Pw.Code                                         AS ProjectCode,
  Pw.ProjectType                                  AS ProjectType,
  Pw.Status                                       AS ProjectStatus,
  Pm.DisplayName                                  AS ProjectManagerName,
  Pm.EmployeeCode                                 AS ProjectManagerCode,
  ApM.DisplayName                                 AS AssociateProjectManagerName,
  ApM.EmployeeCode                                AS AssociateProjectManagerCode
FROM   Project_ProjectWorkspace Pw
LEFT JOIN   Users_EmployeeProfile Pm
       ON   Pw.ProjectManagerId = Pm.Id
LEFT JOIN   Users_EmployeeProfile ApM
       ON   Pw.AssociateProjectManagerId = ApM.Id
WHERE  Pw.TenantId = <TenantId>;
```

### Team Roster Pattern

To Get All Team Members Including PM & APM For AI Context:

```sql
-- Direct PM & APM
SELECT EmployeeCode, DisplayName, Role = 'ProjectManager'
FROM   Users_EmployeeProfile
WHERE  Id IN (Pw.ProjectManagerId, Pw.AssociateProjectManagerId)

UNION

-- Team Assignments
SELECT  Ep.EmployeeCode, Ep.DisplayName, Ta.Role
FROM    Project_TeamAssignment Ta
JOIN    Users_EmployeeProfile Ep ON Ta.EmployeeId = Ep.Id
WHERE   Ta.ProjectId = <ProjectId>
  AND   Ta.Status = 'Active'
  AND   Ta.TenantId = <TenantId>;
```

---

## 3. Task Per Employee Schema

### 3A. WorkItem (Task)

**Model:** `Backend.Apps.TasksDashboard.Models.WorkItem`
**Table:** `TasksDashboard_WorkItem`
**Extends:** `TenantScopedModel` + `ExternalReference`

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK Auto` | Primary Key |
| **`Owner`** | **`FK -> EmployeeProfile` (Protect, Nullable)** | **Assigned Employee** — `RelatedName: OwnedWorkItems` |
| `Project` | `FK -> ProjectWorkspace` (Protect, Nullable) | Parent Project — `RelatedName: WorkItems` |
| `Parent` | `FK -> Self` (Cascade, Nullable) | Parent Task For Subtasks — `RelatedName: Subtasks` |
| `Title` | `CharField(240)` | Task Title |
| `Description` | `TextField(Blank)` | Task Description |
| `Status` | `CharField(80, Default=Open)` | `Open`, `InProgress`, `Review`, `Completed`, `Closed` |
| `Priority` | `CharField(40, Default=Normal)` | `Low`, `Normal`, `High`, `Urgent` |
| `OrderIndex` | `PositiveIntegerField(Default=0)` | Display / Sort Order |
| `Bounty` | `DecimalField(12,2, Default=0)` | Monetary Reward |
| `DueAt` | `DateTimeField(Nullable)` | Due Date & Time |
| `TimerStartedAt` | `DateTimeField(Nullable)` | Timer / Tracking Start |
| `CompletedAt` | `DateTimeField(Nullable)` | Completion Timestamp |
| `Metadata` | `JSONField(Default=Dict)` | Progress Percent, Milestone ID, Task Link, Custom Fields |

### 3B. WorkEntry (Time Log)

**Model:** `Backend.Apps.TasksDashboard.Models.WorkEntry`
**Table:** `TasksDashboard_WorkEntry`

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK Auto` | Primary Key |
| `WorkItem` | `FK -> WorkItem` (Cascade) | Parent Task — `RelatedName: Entries` |
| `Employee` | `FK -> EmployeeProfile` (Protect) | Who Logged Time — `RelatedName: WorkEntries` |
| `EntryDate` | `DateField(DbIndex)` | Date Of Work |
| `Minutes` | `PositiveIntegerField(Default=0)` | Duration In Minutes |
| `EntryType` | `CharField(80, Default=WorkLog)` | `WorkLog`, `Overtime`, `Training` |
| `Summary` | `TextField(Blank)` | What Was Done |
| `Metadata` | `JSONField(Default=Dict)` | Flexible |

### 3C. TaskActivity (Audit Trail)

**Model:** `Backend.Apps.TasksDashboard.Models.TaskActivity`
**Table:** `TasksDashboard_TaskActivity`

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK Auto` | Primary Key |
| `WorkItem` | `FK -> WorkItem` (Cascade) | Parent Task — `RelatedName: Activities` |
| `Actor` | `FK -> EmployeeProfile` (SetNull, Nullable) | Who Performed Action — `RelatedName: TaskActivities` |
| `ActivityType` | `CharField(100, DbIndex)` | `StatusChange`, `Comment`, `AssignmentChange` |
| `Message` | `TextField(Blank)` | Human-Readable Description |
| `Payload` | `JSONField(Default=Dict)` | Structured Activity Data |

### 3D. DailyStatusEntry (EOD Report)

**Model:** `Backend.Apps.TasksDashboard.Models.DailyStatusEntry`
**Table:** `TasksDashboard_DailyStatusEntry`

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK Auto` | Primary Key |
| `Employee` | `FK -> EmployeeProfile` (Protect) | Who Submitted — `RelatedName: DailyStatusEntries` |
| `StatusDate` | `DateField(DbIndex)` | Date Of Report (Unique Per Employee Per Day) |
| `Summary` | `TextField(Blank)` | What Was Accomplished Today |
| `Blockers` | `TextField(Blank)` | Issues / Blockers |
| `NextPlan` | `TextField(Blank)` | Plan For Next Day |
| `SubmittedToSlack` | `BooleanField(Default=False)` | Whether Posted To Slack |
| `SubmittedAt` | `DateTimeField(Nullable)` | Submission Timestamp |
| `SlackThread` | `FK -> SlackDeliveryThread` (SetNull, Nullable) | Linked Slack Thread |
| `SlackMessageTs` | `CharField(120, Blank)` | Slack Message Timestamp |
| `Metadata` | `JSONField(Default=Dict)` | Flexible |

### Tasks By Employee Query Pattern

```sql
-- All Tasks For A Given Employee With Project Context
SELECT
  Wi.Id                                              AS TaskId,
  Wi.Title                                           AS TaskTitle,
  Wi.Status                                          AS TaskStatus,
  Wi.Priority                                        AS TaskPriority,
  Wi.DueAt                                           AS TaskDueDate,
  Wi.Bounty                                          AS TaskBounty,
  Wi.CompletedAt                                     AS TaskCompletedAt,
  Pw.Name                                            AS ProjectName,
  Pw.Code                                            AS ProjectCode,
  Pw.Status                                          AS ProjectStatus,
  Pw.ProjectType                                     AS ProjectType,
  Pm.DisplayName                                     AS ProjectManagerName,
  ApM.DisplayName                                    AS AssociateProjectManagerName
FROM   TasksDashboard_WorkItem Wi
LEFT JOIN   Project_ProjectWorkspace Pw
       ON   Wi.ProjectId = Pw.Id
LEFT JOIN   Users_EmployeeProfile Pm
       ON   Pw.ProjectManagerId = Pm.Id
LEFT JOIN   Users_EmployeeProfile ApM
       ON   Pw.AssociateProjectManagerId = ApM.Id
WHERE  Wi.OwnerId = <EmployeeId>
  AND  Wi.TenantId = <TenantId>
ORDER BY
  Wi.Priority DESC,
  Wi.DueAt ASC;
```

### Time Spent Per Employee Per Day Query Pattern

```sql
-- Total Minutes Logged By Employee On A Given Date
SELECT
  We.EmployeeId                                       AS EmployeeId,
  Ep.DisplayName                                      AS EmployeeName,
  We.EntryDate                                        AS WorkDate,
  SUM(We.Minutes)                                     AS TotalMinutesLogged,
  COUNT(DISTINCT We.WorkItemId)                       AS DistinctTasksWorkedOn,
  We.EntryType                                        AS EntryType
FROM   TasksDashboard_WorkEntry We
JOIN   Users_EmployeeProfile Ep ON We.EmployeeId = Ep.Id
WHERE  We.EmployeeId = <EmployeeId>
  AND  We.EntryDate = <Date>
  AND  We.TenantId = <TenantId>
GROUP BY
  We.EmployeeId, Ep.DisplayName, We.EntryDate, We.EntryType;
```

### EOD Status By Employee Query Pattern

```sql
-- Latest 7 Days Of EOD Reports For An Employee
SELECT
  Dse.StatusDate                                      AS ReportDate,
  Dse.Summary                                         AS Accomplishments,
  Dse.Blockers                                        AS Blockers,
  Dse.NextPlan                                        AS NextDayPlan,
  Dse.SubmittedToSlack                                AS PostedToSlack,
  Dse.SubmittedAt                                     AS SubmittedAt,
  Sdt.ChannelName                                     AS SlackChannel
FROM   TasksDashboard_DailyStatusEntry Dse
LEFT JOIN   TasksDashboard_SlackDeliveryThread Sdt
       ON   Dse.SlackThreadId = Sdt.Id
WHERE  Dse.EmployeeId = <EmployeeId>
  AND  Dse.TenantId = <TenantId>
ORDER BY
  Dse.StatusDate DESC
LIMIT  7;
```

---

## 4. Employee Slack ID Table

### 4A. Slack Username (Direct On Employee Profile)

**Model:** `Backend.Apps.Users.Models.EmployeeProfile.SlackUsername`
**Field Type:** `CharField(120)` — **Required** (No Longer Optional)

Every Employee Has A `SlackUsername` Field Directly On Their Profile.

### 4B. SlackDeliveryThread

**Model:** `Backend.Apps.TasksDashboard.Models.SlackDeliveryThread`
**Table:** `TasksDashboard_SlackDeliveryThread`
**Extends:** `TenantScopedModel` + `ExternalReference`

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK Auto` | Primary Key |
| `ChannelName` | `CharField(120)` | Slack Channel Name, E.G. `#eod-python`, `#general` |
| `ChannelId` | `CharField(120, Blank, DbIndex)` | Slack Channel ID, E.G. `C01ABC123` |
| `ThreadKey` | `CharField(180, DbIndex)` | Unique Thread Identifier |
| `ThreadDate` | `DateField(DbIndex)` | Date Of Thread |
| `Status` | `CharField(80, Default=Open)` | `Open`, `Closed`, `Archived` |
| `Metadata` | `JSONField(Default=Dict)` | Flexible |

### 4C. SlackDeliveryMessage

**Model:** `Backend.Apps.TasksDashboard.Models.SlackDeliveryMessage`
**Table:** `TasksDashboard_SlackDeliveryMessage`

| Field | Type | Notes |
|-------|------|-------|
| `Id` | `PK Auto` | Primary Key |
| `Thread` | `FK -> SlackDeliveryThread` (Cascade) | Parent Thread — `RelatedName: Messages` |
| `DailyStatus` | `FK -> DailyStatusEntry` (SetNull, Nullable) | Linked EOD Report — `RelatedName: SlackMessages` |
| **`Employee`** | **`FK -> EmployeeProfile` (SetNull, Nullable)** | **Employee Who Sent The Message** — `RelatedName: SlackEodMessages` |
| `SlackMessageTs` | `CharField(120, Blank)` | Slack Message Timestamp ID |
| `Status` | `CharField(80, Default=Queued)` | `Queued`, `Delivered`, `Failed` |
| `FailureReason` | `TextField(Blank)` | Error If Delivery Failed |
| `Payload` | `JSONField(Default=Dict)` | Full Slack Message Payload |

### Slack Identity Resolution Pattern

```sql
-- Resolve Slack Username To Employee & Their Current Context
SELECT
  Ep.EmployeeCode                                     AS EmployeeCode,
  Ep.DisplayName                                      AS EmployeeName,
  Ep.SlackUsername                                    AS SlackUsername,
  Ep.Status                                           AS EmployeeStatus,
  Ep.GithubUsername                                   AS GithubHandle,
  Dp.Name                                             AS DepartmentName,
  Po.Title                                            AS PositionTitle,
  Mn.DisplayName                                      AS ManagerName,
  Ep.AvailabilityHours                                AS WeeklyAvailabilityHours
FROM   Users_EmployeeProfile Ep
LEFT JOIN   Users_Department Dp
       ON   Ep.DepartmentId = Dp.Id
LEFT JOIN   Users_Position Po
       ON   Ep.PositionId = Po.Id
LEFT JOIN   Users_EmployeeProfile Mn
       ON   Ep.ManagerId = Mn.Id
WHERE  Ep.SlackUsername = <SlackUsername>
  AND  Ep.TenantId = <TenantId>;
```

### Recent Slack EOD Messages By Employee Pattern

```sql
-- Show Slack Delivery Status For An Employee's Recent EODs
SELECT
  Dse.StatusDate                                      As EodDate,
  Dse.Summary                                         AS EodSummary,
  Sdm.Status                                          AS SlackDeliveryStatus,
  Sdm.SlackMessageTs                                  AS SlackMessageTimestamp,
  Sdt.ChannelName                                     AS SlackChannel,
  Sdt.ThreadKey                                       AS SlackThreadKey
FROM   TasksDashboard_DailyStatusEntry Dse
JOIN   TasksDashboard_SlackDeliveryMessage Sdm
  ON   Sdm.DailyStatusId = Dse.Id
JOIN   TasksDashboard_SlackDeliveryThread Sdt
  ON   Sdm.ThreadId = Sdt.Id
WHERE  Dse.EmployeeId = <EmployeeId>
  AND  Dse.TenantId = <TenantId>
ORDER BY
  Dse.StatusDate DESC
LIMIT  10;
```

### All Employees Slack Directory Pattern

```sql
-- Complete Slack Directory For Notifications & Mentions
SELECT
  Ep.EmployeeCode                                     AS EmployeeCode,
  Ep.DisplayName                                      AS DisplayName,
  Ep.SlackUsername                                    AS SlackUsername,
  Ep.Status                                           AS Status,
  Dp.Name                                             AS Department,
  Po.Title                                            AS Position
FROM   Users_EmployeeProfile Ep
LEFT JOIN   Users_Department Dp       ON Ep.DepartmentId = Dp.Id
LEFT JOIN   Users_Position Po         ON Ep.PositionId = Po.Id
WHERE  Ep.SlackUsername != ''
  AND  Ep.TenantId = <TenantId>
  AND  Ep.Status != 'Exited'
ORDER BY
  Ep.DisplayName ASC;
```

---

## Entity Relationship Diagram (Summary)

```
EmployeeProfile (Employee)
  │
  ├── SlackUsername ───────────────────────────── Slack Identity
  │
  ├── ProjectManager (1:N) ──── ProjectWorkspace ── PM Per Project
  ├── AssociateProjectManager (1:N) ── ProjectWorkspace ── APM Per Project
  │
  ├── TeamAssignment (N:N) ──── ProjectWorkspace ── Team Roster
  │
  ├── WorkItem.Owner (1:N) ──── Task ── WorkEntry (1:N) ── Time Logs
  │                               └── TaskActivity (Audit)
  │
  ├── DailyStatusEntry (1:N) ── EOD Report
  │                               └── SlackDeliveryMessage ─── SlackDeliveryThread
  │
  ├── SkillLinks (N:N) ───────── Skill (Via UserSkill)
  ├── Goals (1:N) ────────────── Goal
  ├── LeaveBalances (1:N) ────── LeaveBalance
  ├── PayProfiles (1:N) ──────── PayProfile
  ├── UserBankAccounts (1:N) ─── EmployeeBankAccount
  └── Certificates (1:N) ─────── EmployeeCertificate
```

---

## Key Design Decisions For AI Engineer

1. **SlackUsername Is Required** — No Longer `Blank=True`. Every Employee Must Have A Slack Handle. The Seed Script Populates It From The Employee Username.

2. **PM & APM Are Dedicated FK Fields** — Not Queried From `TeamAssignment`. `ProjectWorkspace.ProjectManager` And `ProjectWorkspace.AssociateProjectManager` Are First-Class Foreign Keys To `EmployeeProfile`. This Enables Direct SQL Lookups Without Joining Through Team Assignments.

3. **Task Ownership Is Direct** — `WorkItem.Owner` Points Directly To `EmployeeProfile`. No Intermediate Assignment Table. Subtasks Use `WorkItem.Parent` (Self-Referential FK).

4. **EOD Reports Are Daily Unique** — `UniqueConstraint([Tenant, Employee, StatusDate])` Ensures One Report Per Employee Per Day. Linked To Slack Via `SlackDeliveryMessage` For Delivery Tracking.

5. **All Models Are Multi-Tenant** — Every Table Has `TenantId` (FK To `Tenant`) And `WorkspaceId` (FK To `Workspace`, Nullable). All Queries MUST Filter By `TenantId`.

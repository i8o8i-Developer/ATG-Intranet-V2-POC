import React, { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, Bell, ChevronLeft, LogOut } from "lucide-react";
import { apiGet, apiPost, clearApiAuth, getApiSettings, unpackList } from "./Api/Client.js";
import { LoginScreen, ProfileScreen } from "./Screens/AuthScreens.jsx";
import { RouteRenderer } from "./Screens/AppScreens.jsx";
import OfferAcceptanceScreen from "./Screens/OfferAcceptanceScreen.jsx";
import { resolveActiveEmployee } from "./Screens/Shared/ScreenUtils.jsx"; // Forced Reload
import {
  ATGLogo,
  IconHome,
  IconHRMS,
  IconLMS,
  IconMCP,
  IconDevProject,
  IconMarketing,
  IconCalendar,
  IconPassword,
  IconAssessments,
  IconBank,
  IconPayslip,
  IconManageEmployees,
  IconDocument,
  IconFeedback,
  IconFinance,
  IconNewEmployee,
  IconAdd,
  IconDot,
  IconDelayManagement,
  IconPayrollDownload,
  SvgChevronUp,
  SvgChevronDown,
} from "./Components/icons/icons.jsx";

// ─── Flat Nav List For Page Title Lookup ────────────
const navItems = [
  { label: "Home",                  path: "/home/" },
  { label: "HRMS",                  path: "/hrms/" },
  { label: "LMS",                   path: "/lms/" },
  { label: "MCP Agents",            path: "/mcp/" },
  { label: "Development Projects",  path: "/project/dashboard/" },
  { label: "Marketing Project",     path: "/marketing-project/" },
  { label: "Apply Leave",           path: "/leave/apply/" },
  { label: "Password Management",   path: "/change-password/" },
  { label: "Assessments",           path: "/assessment/" },
  { label: "Bank Details",          path: "/Bankdetails/" },
  { label: "Payslips",              path: "/payslips/" },
  { label: "Manage Employees",      path: "/employee-registrar/" },
  { label: "Send Offer",            path: "/Onboard/Send_Offer" },
  { label: "Send Certificate",      path: "/send-certificate" },
  { label: "Deactivate Employee",   path: "/deactivate-multiple-employee/" },
  { label: "Documents",             path: "/docs/" },
  { label: "Finance Department",    path: "/payments/" },
  { label: "New Employee Register", path: "/employee-registrar/new/" },
  { label: "MCP Agents",            path: "/mcp/" },
  { label: "Notifications",         path: "/notifications/" },
  { label: "Payroll Downloads",     path: "/payroll-downloads/" },
  { label: "Delay Management",      path: "/delays/" },
];

const endpointMap = [
  ["me", "/Users/Auth/Me/", "object"],
  ["employees", "/Users/EmployeeProfiles/", "list"],
  ["departments", "/Users/Departments/", "list"],
  ["subDepartments", "/Users/SubDepartments/", "list"],
  ["positions", "/Users/Positions/", "list"],
  ["skills", "/Users/Skills/", "list"],
  ["userSkills", "/Users/UserSkills/", "list"],
  ["payProfiles", "/Users/PayProfiles/", "list"],
  ["bankAccounts", "/Users/EmployeeBankAccounts/", "list"],
  ["paymentSnapshots", "/Users/EmployeePaymentSnapshots/", "list"],
  ["leavePolicies", "/Users/LeavePolicies/", "list"],
  ["leaveBalances", "/Users/LeaveBalances/", "list"],
  ["employeeFeedback", "/Users/EmployeeFeedback/", "list"],
  ["projects", "/Project/ProjectWorkspaces/", "list"],
  ["teamAssignments", "/Project/TeamAssignments/", "list"],
  ["milestones", "/Project/DeliveryMilestones/", "list"],
  ["projectDocuments", "/Project/DeliveryDocuments/", "list"],
  ["repositories", "/Project/RepositoryLinks/", "list"],
  ["alerts", "/Project/DeliveryAlerts/", "list"],
  ["tasks", "/TasksDashboard/WorkItems/", "list"],
  ["workEntries", "/TasksDashboard/WorkEntries/", "list"],
  ["dailyStatus", "/TasksDashboard/DailyStatusEntries/", "list"],
  ["taskActivities", "/TasksDashboard/TaskActivities/", "list"],
  ["notifications", "/MainApp/Notifications/", "list"],
  ["leaveRequests", "/MainApp/LeaveRequests/", "list"],
  ["leaveOverview", "/MainApp/leave/", "object"],
  ["offers", "/MainApp/OnboardingOffers/", "list"],
  ["issues", "/MainApp/ExternalIssueReferences/", "list"],
  ["leadAccounts", "/Banao/LeadAccounts/", "list"],
  ["leadTags", "/Banao/LeadTags/", "list"],
  ["leadContacts", "/Banao/LeadContacts/", "list"],
  ["leadActivities", "/Banao/LeadActivities/", "list"],
  ["leadNotes", "/Banao/LeadNotes/", "list"],
  ["leadTests", "/Banao/LeadTests/", "list"],
  ["leadProposals", "/Banao/ProposalArtifacts/", "list"],
  ["leadAudits", "/Banao/AuditArtifacts/", "list"],
  ["leadTransitions", "/Banao/WorkflowTransitions/", "list"],
  ["lmsLeads", "/Lms/api/leads/?limit=100", "object"],
  ["learningPaths", "/Lms/LearningPaths/", "list"],
  ["learningModules", "/Lms/LearningModules/", "list"],
  ["learningAssignments", "/Lms/LearningAssignments/", "list"],
  ["leadQueueSnapshots", "/Lms/LeadQueueSnapshots/", "list"],
  ["revenueSnapshots", "/Lms/RevenuePerformanceSnapshots/", "list"],
  ["docs", "/AtgDocs/KnowledgeDocuments/", "list"],
  ["docPermissions", "/AtgDocs/KnowledgePermissions/", "list"],
  ["driveFiles", "/AtgDocs/DriveFiles/", "list"],
  ["docVersions", "/AtgDocs/DocumentVersions/", "list"],
  ["assessmentLegacy", "/Assesment/assessment/?page_size=50", "object"],
  ["assessmentAssignments", "/Assesment/AssessmentAssignments/", "list"],
  ["assessmentTemplates", "/Assesment/AssessmentTemplates/", "list"],
  ["financeDashboard", "/FinanceAndPayroll/payments/?pay_month=current&month_name=May", "object"],
  ["payPeriods", "/FinanceAndPayroll/PayPeriods/", "list"],
  ["payrollRuns", "/FinanceAndPayroll/PayrollRuns/", "list"],
  ["payrollLineItems", "/FinanceAndPayroll/PayrollLineItems/", "list"],
  ["payslipDocuments", "/FinanceAndPayroll/PayslipDocuments/", "list"],
  ["paymentOrders", "/FinanceAndPayroll/PaymentOrders/", "list"],
  ["domains", "/Users/Domains/", "list"],
  ["departmentMemberships", "/Users/DepartmentMemberships/", "list"],
  ["goals", "/Users/Goals/", "list"],
  ["goalFeedback", "/Users/GoalFeedback/", "list"],
  ["userStatusSnapshots", "/Users/UserStatusSnapshots/", "list"],
  ["benchPeriods", "/Users/BenchPeriods/", "list"],
  ["employeeRatings", "/Users/EmployeeRatings/", "list"],
  ["employeeCertificates", "/Users/EmployeeCertificates/", "list"],
  ["leaveTransactions", "/Users/LeaveTransactions/", "list"],
  ["resignationRequests", "/Users/ResignationRequests/", "list"],
  ["userEffortReports", "/Users/UserEffortReports/", "list"],
  ["interviewProgress", "/Users/InterviewProgress/", "list"],
  ["credentialVaultItems", "/MainApp/CredentialVaultItems/", "list"],
  ["credentialShareGrants", "/MainApp/CredentialShareGrants/", "list"],
  ["notificationSnoozeRecords", "/MainApp/NotificationSnoozeRecords/", "list"],
  ["managerScopes", "/MainApp/ManagerScopes/", "list"],
  ["projectContacts", "/Project/ProjectContacts/", "list"],
  ["defaultCheckpoints", "/Project/DefaultCheckpoints/", "list"],
  ["milestoneComponents", "/Project/MilestoneComponents/", "list"],
  ["complianceCampaigns", "/Project/ComplianceCampaigns/", "list"],
  ["complianceAssignments", "/Project/ComplianceAssignments/", "list"],
  ["delays", "/Project/ProjectDelays/", "list"],
  ["slackThreads", "/TasksDashboard/SlackDeliveryThreads/", "list"],
  ["slackMessages", "/TasksDashboard/SlackDeliveryMessages/", "list"],
  ["externalWorkMappings", "/TasksDashboard/ExternalWorkMappings/", "list"],
  ["clickupMappings", "/TasksDashboard/ClickUpProjectMappings/", "list"],
  ["managerAbbreviations", "/TasksDashboard/ManagerAbbreviations/", "list"],
  ["leadStatusHistory", "/Banao/WorkflowStatusHistory/", "list"],
  ["knowledgeActivities", "/AtgDocs/KnowledgeActivities/", "list"],
  ["driveFolders", "/AtgDocs/DriveFolders/", "list"],
  ["compensationPlans", "/FinanceAndPayroll/CompensationPlans/", "list"],
  ["financeBankAccounts", "/FinanceAndPayroll/BankAccounts/", "list"],
  ["approvalDecisions", "/FinanceAndPayroll/ApprovalDecisions/", "list"],
  ["payoutExecutions", "/FinanceAndPayroll/PayoutExecutions/", "list"],
  ["paymentWebhookEvents", "/FinanceAndPayroll/PaymentWebhookEvents/", "list"],
  ["gitRepoSnapshots", "/Git/GitRepositorySnapshots/", "list"],
  ["gitActivitySnapshots", "/Git/GitActivitySnapshots/", "list"],
  ["repoUtilityRequests", "/Git/RepositoryUtilityRequests/", "list"],
  ["githubRepositories", "/GithubExtension/GitHubRepositories/", "list"],
  ["branchReviewers", "/GithubExtension/BranchReviewerAssignments/", "list"],
  ["branchTesters", "/GithubExtension/BranchTestingAssignments/", "list"],
  ["repoBranchStatuses", "/GithubExtension/RepositoryBranchStatuses/", "list"],
  ["templateVariables", "/HtmlTemplate/TemplateVariables/", "list"],
  ["offerMacros", "/HtmlTemplate/OfferMacros/", "list"],
  ["contentTemplates", "/HtmlTemplate/ContentTemplates/", "list"],
  ["offerTemplates", "/HtmlTemplate/OfferTemplates/", "list"],
  ["genericHtmlTemplates", "/HtmlTemplate/GenericHtmlTemplates/", "list"],
  ["collegePipelines", "/L3/CollegePipelineRecords/", "list"],
  ["collegeContacts", "/L3/CollegeContacts/", "list"],
  ["collegeAssignments", "/L3/CollegeAssignments/", "list"],
  ["collegeEmailTemplates", "/L3/CollegeEmailTemplates/", "list"],
  ["candidateProfiles", "/L3/CandidateProfiles/", "list"],
  ["talentAssignments", "/L3/TalentAssignments/", "list"],
  ["talentEmails", "/L3/TalentEmails/", "list"],
  ["talentPerformanceSnapshots", "/L3/TalentPerformanceSnapshots/", "list"],
  ["integrationProviders", "/IntegrationHub/IntegrationProviders/", "list"],
  ["integrationConnections", "/IntegrationHub/IntegrationConnections/", "list"],
  ["webhookInboxEvents", "/IntegrationHub/WebhookInboxEvents/", "list"],
  ["integrationSyncJobs", "/IntegrationHub/IntegrationSyncJobs/", "list"],
  ["integrationAttempts", "/IntegrationHub/IntegrationAttempts/", "list"],
  ["agentPrincipals", "/McpAccessLayer/AgentPrincipals/", "list"],
  ["mcpToolDefinitions", "/McpAccessLayer/McpToolDefinitions/", "list"],
  ["mcpResourceDefinitions", "/McpAccessLayer/McpResourceDefinitions/", "list"],
  ["mcpAccessGrants", "/McpAccessLayer/McpAccessGrants/", "list"],
  ["mcpInvocationAudits", "/McpAccessLayer/McpInvocationAudits/", "list"],
  ["draftAgentActions", "/McpAccessLayer/DraftAgentActions/", "list"],
  ["legacyApplicationMaps", "/LegacyBridge/LegacyApplicationMaps/", "list"],
  ["legacyModelCrosswalks", "/LegacyBridge/LegacyModelCrosswalks/", "list"],
  ["migrationRuns", "/LegacyBridge/MigrationRuns/", "list"],
  ["legacyMigrationIssues", "/LegacyBridge/LegacyMigrationIssues/", "list"],
  ["enterpriseTenants", "/EnterpriseCore/Tenants/", "list"],
  ["enterpriseOrganizations", "/EnterpriseCore/Organizations/", "list"],
  ["enterpriseBusinessUnits", "/EnterpriseCore/BusinessUnits/", "list"],
  ["enterpriseWorkspaces", "/EnterpriseCore/Workspaces/", "list"],
  ["enterpriseRoles", "/EnterpriseCore/Roles/", "list"],
  ["enterpriseRoleAssignments", "/EnterpriseCore/RoleAssignments/", "list"],
  ["accessAuditLogs", "/EnterpriseCore/AccessAuditLogs/", "list"],
];

const LAZY_KEYS = new Set([
  "subDepartments", "payProfiles", "bankAccounts", "paymentSnapshots",
  "leavePolicies", "employeeFeedback", "projectDocuments", "repositories",
  "offers", "issues",
  "leadAccounts", "leadTags", "leadContacts", "leadActivities", "leadNotes",
  "leadTests", "leadProposals", "leadAudits", "leadTransitions",
  "lmsLeads", "learningPaths", "learningModules", "learningAssignments",
  "leadQueueSnapshots", "revenueSnapshots",
  "docs", "docPermissions", "driveFiles", "docVersions",
  "assessmentLegacy", "assessmentAssignments", "assessmentTemplates",
  "financeDashboard", "payPeriods", "payrollRuns", "payrollLineItems",
  "payslipDocuments", "paymentOrders",
  "domains", "departmentMemberships",
  "userStatusSnapshots", "benchPeriods", "employeeRatings",
  "employeeCertificates", "leaveTransactions", "resignationRequests",
  "userEffortReports", "interviewProgress",
  "credentialVaultItems", "credentialShareGrants", "notificationSnoozeRecords",
  "managerScopes", "projectContacts", "defaultCheckpoints",
  "milestoneComponents", "complianceCampaigns", "complianceAssignments", "delays",
  "slackThreads", "slackMessages", "externalWorkMappings", "clickupMappings",
  "managerAbbreviations", "leadStatusHistory", "knowledgeActivities", "driveFolders",
  "compensationPlans", "financeBankAccounts", "approvalDecisions",
  "payoutExecutions", "paymentWebhookEvents",
  "gitRepoSnapshots", "gitActivitySnapshots", "repoUtilityRequests",
  "githubRepositories", "branchReviewers", "branchTesters", "repoBranchStatuses",
  "templateVariables", "offerMacros", "contentTemplates", "offerTemplates",
  "genericHtmlTemplates",
  "collegePipelines", "collegeContacts", "collegeAssignments",
  "collegeEmailTemplates", "candidateProfiles", "talentAssignments",
  "talentEmails", "talentPerformanceSnapshots",
  "integrationProviders", "integrationConnections", "webhookInboxEvents",
  "integrationSyncJobs", "integrationAttempts",
  "agentPrincipals", "mcpToolDefinitions", "mcpResourceDefinitions",
  "mcpAccessGrants", "mcpInvocationAudits", "draftAgentActions",
  "legacyApplicationMaps", "legacyModelCrosswalks", "migrationRuns",
  "legacyMigrationIssues",
  "enterpriseTenants", "enterpriseOrganizations", "enterpriseBusinessUnits",
  "enterpriseWorkspaces", "enterpriseRoles", "enterpriseRoleAssignments",
  "accessAuditLogs",
]);

// ─── Nav Structure — Maps Figma Items To Your Existing Paths ─────────────────
function buildNavItems(activePath) {
  return [
    { label: "Home",                 icon: <IconHome active={activePath === "/home/"} />, path: "/home/" },
    { label: "HRMS",                 icon: <IconHRMS />,             path: "/hrms/" },
    { label: "LMS",                  icon: <IconLMS />,              path: "/lms/" },
    { label: "MCP",                  icon: <IconMCP />,              path: "/mcp/" },
    {
      label: "Development Project",
      icon: <IconDevProject />,
      path: "/project/dashboard/",
      children: [],
    },
    { label: "Marketing Project",    icon: <IconMarketing />,        path: "/marketing-project/", children: [] },
    { label: "Apply Leave",          icon: <IconCalendar />,         path: "/leave/apply/" },
    { label: "Password Management",  icon: <IconPassword />,         path: "/change-password/" },
    { label: "Assessments",          icon: <IconAssessments />,      path: "/assessment/" },
    { label: "Bank Details",         icon: <IconBank />,             path: "/Bankdetails/" },
    { label: "Payslips",             icon: <IconPayslip />,          path: "/payslips/" },
    {
      label: "Manage Employees",
      icon: <IconManageEmployees />,
      path: "/employee-registrar/",
      children: [
        { label: "Send Offer Letter",  path: "/Onboard/Send_Offer" },
        { label: "Send Certificate",   path: "/send-certificate" },
        { label: "Deactivate Employee", path: "/deactivate-multiple-employee/" },
      ],
    },
    { label: "Documents",            icon: <IconDocument />,         path: "/docs/" },
    { label: "Provide Feedbacks",    icon: <IconFeedback />,         path: "/feedback/" },
    { label: "Finance Department",   icon: <IconFinance />,          path: "/payments/?pay_month=current&month_name=May" },
    { label: "New Employee Register", icon: <IconNewEmployee />,      path: "/employee-registrar/new/" },
    { label: "Delay Management",     icon: <IconDelayManagement />,  path: "/delays/" },
    { label: "Payroll Downloads",    icon: <IconPayrollDownload />,  path: "/payroll-downloads/" },
  ];
}

// ─── Nav Link ─────────────────────────────────────────────────────────────
function NavLink({ item, depth = 0, activePath, navigate, collapsed }) {
  const hasChildren = item.children && item.children.length > 0;

  const isGroupActive = activePath === item.path ||
    (item.path && item.path !== "/home/" &&
      activePath.startsWith(item.path.split("?")[0].replace(/\/$/, "")));

  const [open, setOpen] = useState(
    item.label === "Development Project" || isGroupActive
  );

  useEffect(() => {
    if (isGroupActive && hasChildren) setOpen(true);
  }, [activePath, isGroupActive, hasChildren]);

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => setOpen((v) => !v)}
          style={{
            display: "flex", alignItems: "center", gap: 12,
            width: "100%", paddingRight: 12, paddingTop: 8, paddingBottom: 8,
            borderRadius: 13.6, border: "none", background: "transparent",
            cursor: "pointer", textAlign: "left",
            paddingLeft: depth === 0 ? 12 : 32,
            transition: "background 0.12s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "#EEF3FF"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          {item.icon && <span style={{ flexShrink: 0, display: "flex" }}>{item.icon}</span>}
          {!collapsed && (
            <span style={{ flex: 1, fontSize: 14, fontWeight: 500, lineHeight: "20px", color: "#60676D", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {item.label}
            </span>
          )}
          {!collapsed && (
            <span style={{ flexShrink: 0, display: "flex" }}>
              {open ? <SvgChevronUp /> : <SvgChevronDown />}
            </span>
          )}
        </button>
        {open && !collapsed && (
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {item.children.map((child) => (
              <NavLink key={child.path || child.label} item={child} depth={1} activePath={activePath} navigate={navigate} collapsed={collapsed} />
            ))}
          </div>
        )}
      </div>
    );
  }

  // Leaf Item — Determine Active State
  const pathBase = item.path ? item.path.split("?")[0] : "";
  const isActive = activePath === pathBase ||
    (pathBase && pathBase !== "/home/" && activePath.startsWith(pathBase.replace(/\/$/, "")));

  return (
    <button
      onClick={() => item.path && navigate(item.path)}
      style={{
        display: "flex", alignItems: "center", gap: 12,
        width: "100%", paddingRight: 12, paddingTop: 8, paddingBottom: 8,
        borderRadius: depth === 0 ? 8 : 13.6,
        border: "none",
        background: isActive ? "#D7E4FF" : "transparent",
        cursor: "pointer", textAlign: "left",
        paddingLeft: depth === 0 ? 12 : 32,
        transition: "background 0.12s",
      }}
      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = "#EEF3FF"; }}
      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
    >
      {item.isDot ? (
        <span style={{ flexShrink: 0, display: "flex" }}><IconDot /></span>
      ) : item.icon ? (
        <span style={{ flexShrink: 0, display: "flex" }}>{item.icon}</span>
      ) : (
        <span style={{ width: collapsed ? 20 : 16, flexShrink: 0 }} />
      )}
      {!collapsed && (
        <span style={{
          flex: 1, fontSize: 14, fontWeight: 500, lineHeight: "20px",
          color: isActive ? "#1D44B0" : "#60676D",
          whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
        }}>
          {item.label}
        </span>
      )}
    </button>
  );
}

// ─── App (Unchanged Logic) ───────────────────────────────────────────────────
function App() {
  const [settings, setSettings] = useState(getApiSettings);
  const [route, setRoute] = useState(() => window.location.pathname + window.location.search);
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const path = route.split("?")[0];

  const isLoginRoute = path.startsWith("/login");
  // Public Offer Acceptance Route — No Auth Needed
  const isPublicOfferRoute = path.startsWith("/offer/accept/");
  const hasAuth = Boolean(settings.basicAuth?.username && settings.basicAuth?.password);
  const { data, loading, errors, apiOnline, reload, loadMissing } = useIntranetData(reloadKey, hasAuth && !isLoginRoute && !isPublicOfferRoute);

  useEffect(() => {
    const onPop = () => setRoute(window.location.pathname + window.location.search);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((p) => {
    window.history.pushState(null, "", p);
    setRoute(window.location.pathname + window.location.search);
  }, []);

  useEffect(() => {
    if (isPublicOfferRoute) return;
    const currentEmployee = resolveActiveEmployee(data);
    const nextEmployeeId = currentEmployee?.id ? String(currentEmployee.id) : "";
    if (nextEmployeeId && nextEmployeeId !== String(selectedEmployeeId || "")) {
      setSelectedEmployeeId(nextEmployeeId);
    }
    if (!nextEmployeeId && selectedEmployeeId) {
      setSelectedEmployeeId("");
    }
  }, [data.employees, data.me, selectedEmployeeId, isPublicOfferRoute]);

  useEffect(() => {
    if (!hasAuth || isLoginRoute) return;
    const unauthorized = errors.some((e) => e.status === 401);
    const offline = !loading && !apiOnline && errors.length > 0;
    if (unauthorized || offline) {
      clearApiAuth();
      setSettings(getApiSettings());
      navigate("/login/");
    }
  }, [errors, loading, apiOnline, hasAuth, isLoginRoute, navigate]);

  const login = (path = "/home/") => { setSettings(getApiSettings()); setReloadKey((v) => v + 1); navigate(path); };
  const logout = async () => {
    try {
      await apiPost("/Users/Auth/Logout/");
    } catch (error) {
      console.warn("Logout Request Failed", error);
    }
    clearApiAuth();
    setSettings(getApiSettings());
    setReloadKey((v) => v + 1);
    navigate("/login/");
  };

  // Public Offer Acceptance — Bypass Auth, App Shell, And Resolve Active Employee Entirely
  if (isPublicOfferRoute) return <OfferAcceptanceScreen />;

  if (!hasAuth || path.startsWith("/login")) return <LoginScreen settings={settings} onLogin={login} />;

  const commonProps = { data, settings, selectedEmployeeId, reload, navigate, loadMissing };

  return (
    <AppShell route={route} navigate={navigate} data={data} apiOnline={apiOnline} loading={loading} logout={logout} errors={errors} reloadData={reload} loadMissing={loadMissing}>
      {path.startsWith("/profile")
        ? <ProfileScreen data={data} onLogout={logout} reload={reload} />
        : <RouteRenderer route={route} {...commonProps} />}
    </AppShell>
  );
}

// ─── Use Intranet Data ─────────────────────────────────────────────
function useIntranetData(reloadKey, enabled) {
  const [state, setState] = useState({ data: {}, loading: false, errors: [], apiOnline: false });
  const hasInitiallyLoaded = useRef(false);
  const loadedLazyKeys = useRef(new Set());

  const applyPayload = (nextData, key, mode, payload) => {
    if (key === "assessmentLegacy") {
      nextData.assessmentRows = payload?.data || payload?.results || [];
      nextData.assessmentLegacy = payload;
    } else if (key === "financeDashboard") {
      nextData.financeRows = payload?.user_list || [];
      nextData.financeDashboard = payload;
    } else if (key === "lmsLeads") {
      nextData.lmsLeads = payload;
      nextData.leadRows = payload?.results || [];
      nextData.leadOriginCounts = payload?.origin_counts || {};
    } else {
      nextData[key] = mode === "list" ? unpackList(payload) : payload;
    }
  };

const REALTIME_KEYS = ["dailyStatus", "me", "notifications", "employees", "tasks", "projects", "leaveRequests", "leaveBalances", "teamAssignments", "milestones", "alerts", "userSkills", "goals", "goalFeedback", "workEntries"];

const load = useCallback(async (keysFilter) => {
     if (!enabled) { setState({ data: {}, loading: false, errors: [], apiOnline: false }); hasInitiallyLoaded.current = false; return; }
     let effectiveFilter = keysFilter;
     if (keysFilter === undefined && hasInitiallyLoaded.current) {
       effectiveFilter = REALTIME_KEYS;
     } else if (keysFilter === true || keysFilter === "__all__") {
       effectiveFilter = undefined;
     } else if (Array.isArray(keysFilter)) {
       effectiveFilter = keysFilter;
       keysFilter.forEach((k) => loadedLazyKeys.current.add(k));
     }
     const subset = Array.isArray(effectiveFilter) && effectiveFilter.length
       ? endpointMap.filter(([key]) => effectiveFilter.includes(key))
       : endpointMap.filter(([key]) => !LAZY_KEYS.has(key));
     const isPartial = subset.length !== endpointMap.length;
     setState((cur) => ({ ...cur, loading: !isPartial ? true : cur.loading, errors: isPartial ? cur.errors : [] }));

     // Wave loading: critical endpoints (auth/me) first, then the rest in batches
     const criticalKeys = ["me", "enterprises", "departments", "positions", "skills"];
     const critical = subset.filter(([key]) => criticalKeys.includes(key));
     const rest = subset.filter(([key]) => !criticalKeys.includes(key));

     const results = [];
     // Wave 1: Critical endpoints (immediate)
     if (critical.length > 0) {
       const wave1 = await Promise.allSettled(critical.map(([key, p, mode]) => apiGet(p).then((payload) => ({ key, payload, mode }))));
       results.push(...wave1);
     }
     // Wave 2: Remaining endpoints (after critical resolve, reduces burst)
     if (rest.length > 0) {
       const wave2 = await Promise.allSettled(rest.map(([key, p, mode]) => apiGet(p).then((payload) => ({ key, payload, mode }))));
       results.push(...wave2);
     }

     setState((cur) => {
       const nextData = isPartial ? { ...cur.data } : {};
       const requestErrors = isPartial ? cur.errors.filter((err) => !effectiveFilter.includes(err.key)) : [];
       results.forEach((result, i) => {
         const [key, , mode] = subset[i];
         if (result.status === "fulfilled") applyPayload(nextData, key, mode, result.value.payload);
         else { requestErrors.push({ key, status: result.reason?.status, message: result.reason?.message || "Request Failed" }); if (!isPartial) nextData[key] = mode === "list" ? [] : null; }
       });
       return { data: nextData, loading: false, errors: requestErrors, apiOnline: isPartial ? cur.apiOnline : requestErrors.length < subset.length };
     });
     if (!isPartial) hasInitiallyLoaded.current = true;
   }, [enabled]);

   const loadMissing = useCallback(async (keys) => {
     if (!enabled || !Array.isArray(keys) || !keys.length) return;
     const missing = keys.filter((k) => LAZY_KEYS.has(k) && !loadedLazyKeys.current.has(k));
     if (!missing.length) return;
     await load(missing);
   }, [enabled, load]);

   useEffect(() => { load("__all__"); }, [load, reloadKey]);
   return { ...state, reload: load, loadMissing };
}

// ─── App Shell — Figma Builder Sidebar + Existing Topbar Logic ──────────────
function AppShell({ children, route, navigate, data, apiOnline, loading, logout, errors, reloadData, loadMissing }) {
  const activePath = route.split("?")[0];
  const activeItem = navItems.find((item) => activePath === item.path || (item.path !== "/home/" && activePath.startsWith(item.path.replace(/\/$/, ""))));
  const pageTitle = activePath.startsWith("/profile") ? "Profile" : activeItem?.label || "Home";

  const user = data.me?.user || data.me?.account || data.me || {};
  const employee = resolveActiveEmployee(data) || {};
  const displayName = employee.display_name || employee.displayName || user.fullName || user.full_name || user.username || "Profile";
  const initials = String(displayName).split(" ").map((p) => p[0]).join("").slice(0, 2).toUpperCase() || "U";
  const visibleErrors = errors.filter((item) => item.status && item.status !== 401).slice(0, 1);

  const builtNav = buildNavItems(activePath);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <style>{`
        *, *::before, *::after { box-sizing: border-box; }
        body { margin: 0; }

        .Atg-App { display: flex; height: 100vh; overflow: hidden; font-family: 'Inter', system-ui, sans-serif; background: #f7faff; }

        /* ── Sidebar ── */
        .Atg-Sidebar {
          width: 278px; min-width: 278px; height: 100vh;
          background: #f7faff;
          border-right: 1px solid #e3e3e3;
          display: flex; flex-direction: column; overflow: hidden;
          transition: width 0.2s, min-width 0.2s;
        }
        .Atg-Sidebar.Collapsed {
          width: 80px; min-width: 80px;
        }

        /* Brand */
        .Atg-Brand {
          display: flex; align-items: center; justify-content: space-between;
          padding: 24px 16px 0;
          margin-bottom: 24px;
          flex-shrink: 0;
        }
        .Atg-Brand-Left { display: flex; align-items: center; gap: 8px; }
        .Atg-Brand-Name {
          font-size: 24px; font-weight: 500; line-height: 24px;
          color: #000;
          font-family: sans-serif;
        }
        .Atg-Sidebar.Collapsed .Atg-Brand-Name { display: none; }
        .Atg-Sidebar.Collapsed .Atg-Brand { justify-content: center; padding: 24px 8px 0; }
        .Atg-Sidebar.Collapsed .Atg-Brand-Left { gap: 0; }

        .Atg-Collapse-Btn {
          width: 36px; height: 36px; border-radius: 8px;
          background: transparent;
          border: none; cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          color: #64748b; font-family: 'Inter', sans-serif;
          flex-shrink: 0; transition: background 0.15s, color 0.15s;
        }
        .Atg-Collapse-Btn:hover { background: #eef3ff; color: #1d44b0; }
        .Atg-Sidebar.Collapsed .Atg-Collapse-Btn { display: none; }

        /* Nav Scroll */
        .Atg-Nav {
          flex: 1; overflow-y: auto; overflow-x: hidden;
          padding: 0 16px 24px;
          display: flex; flex-direction: column; gap: 4px;
        }
        .Atg-Nav::-webkit-scrollbar { width: 4px; }
        .Atg-Nav::-webkit-scrollbar-track { background: transparent; }
        .Atg-Nav::-webkit-scrollbar-thumb { background: #c7d2fe; border-radius: 2px; }
        .Atg-Sidebar.Collapsed .Atg-Nav { padding: 0 8px 24px; }

        /* ── Main ── */
        .Atg-Main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }

        /* Topbar */
        .Atg-Topbar {
          display: flex; align-items: center; justify-content: space-between;
          padding: 0 24px; height: 56px;
          background: #fff; border-bottom: 1px solid #e3e3e3;
          flex-shrink: 0; gap: 12px;
        }
        .Atg-Topbar-Title { display: flex; flex-direction: column; gap: 1px; }
        .Atg-Topbar-Title .crumb { font-size: 11px; color: #94a3b8; }
        .Atg-Topbar-Title strong { font-size: 15px; color: #0f172a; font-weight: 600; }
        .Atg-Topbar-Actions { display: flex; align-items: center; gap: 8px; }

        .Sync-Badge {
          font-size: 11px; font-weight: 500;
          padding: 2px 8px; border-radius: 20px;
          background: #f1f5f9; color: #64748b;
        }
        .Sync-Badge-Danger { background: #fee2e2; color: #dc2626; }

        .Atg-User-Chip {
          display: flex; align-items: center; gap: 6px;
          padding: 4px 10px 4px 6px; border-radius: 20px;
          border: 1px solid #e2e8f0; background: #fff;
          cursor: pointer; font-family: inherit; font-size: 13px;
          color: #374151; font-weight: 500; transition: background 0.12s;
        }
        .Atg-User-Chip:hover, .Atg-User-Chip.Active { background: #f1f5f9; }
        .Atg-User-Chip .Chip-Avatar {
          width: 26px; height: 26px; border-radius: 50%;
          background: #d7e4ff; color: #1d44b0;
          font-size: 11px; font-weight: 700;
          display: flex; align-items: center; justify-content: center;
        }

        .Atg-Icon-Btn {
          width: 32px; height: 32px; border-radius: 8px;
          border: none; background: transparent; cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          color: #64748b; transition: background 0.12s, color 0.12s;
          position: relative;
        }
        .Atg-Icon-Btn:hover { background: #eef3ff; color: #1d44b0; }
        .Atg-Icon-Btn.Active { background: #d7e4ff; color: #1d44b0; }

        /* Notification */
        .Atg-Notif-Bell { position: relative; }
        .Atg-Notif-Count {
          position: absolute; top: 2px; right: 2px;
          min-width: 16px; height: 16px; border-radius: 8px;
          background: #ef4444; color: #fff;
          font-size: 10px; font-weight: 700;
          display: flex; align-items: center; justify-content: center;
          padding: 0 3px; pointer-events: none;
        }
        .Atg-Notif-Popover {
          position: absolute; top: calc(100% + 8px); right: 0;
          width: 340px; background: #fff;
          border: 1px solid #e2e8f0; border-radius: 12px;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.10); z-index: 200; overflow: hidden;
        }
        .Atg-Notif-Head {
          display: flex; align-items: center; gap: 8px;
          padding: 12px 16px; border-bottom: 1px solid #f1f5f9; flex-wrap: wrap;
        }
        .Atg-Notif-Head strong { font-size: 14px; color: #0f172a; margin-right: auto; }
        .Atg-Notif-Head span { font-size: 12px; color: #94a3b8; }
        .Atg-Link-Btn { border: none; background: transparent; color: #3b82f6; font-size: 12px; font-weight: 500; cursor: pointer; padding: 0; font-family: inherit; }
        .Atg-Link-Btn:hover { text-decoration: underline; }
        .Atg-Notif-List { max-height: 320px; overflow-y: auto; }
        .Atg-Notif-Item { display: flex; align-items: flex-start; gap: 12px; padding: 12px 16px; border-bottom: 1px solid #f8fafc; }
        .Atg-Notif-Item.Unread { background: #f8fafc; }
        .Atg-Notif-Item > div { flex: 1; min-width: 0; }
        .Atg-Notif-Item strong { display: block; font-size: 13px; color: #0f172a; }
        .Atg-Notif-Item p { font-size: 12px; color: #64748b; margin: 2px 0; }
        .Atg-Notif-Item small { font-size: 11px; color: #94a3b8; }
        .Atg-Notif-Empty { padding: 24px; text-align: center; color: #94a3b8; font-size: 13px; }
        .Atg-Soft-Btn {
          border: 1px solid #e2e8f0; background: #fff; border-radius: 6px;
          padding: 3px 8px; font-size: 12px; font-weight: 500;
          color: #374151; cursor: pointer; white-space: nowrap;
          font-family: inherit; transition: background 0.12s;
        }
        .Atg-Soft-Btn:hover { background: #f1f5f9; }

        /* Error Banner */
        .Atg-Error-Bar {
          display: flex; align-items: center; gap: 8px;
          background: #fef2f2; border-bottom: 1px solid #fecaca;
          padding: 10px 24px; color: #dc2626; font-size: 13px; flex-shrink: 0;
        }

        /* Content */
        .Atg-Content { flex: 1; overflow-y: auto; overflow-x: hidden; background: #fff; }
      `}</style>

      <div className="Atg-App">
        {/* ── Sidebar ── */}
        <aside className={"Atg-Sidebar" + (collapsed ? " Collapsed" : "")}>
          <div className="Atg-Brand">
            <div className="Atg-Brand-Left">
              <ATGLogo />
              <span className="Atg-Brand-Name">Intranet</span>
            </div>
            <button className="Atg-Collapse-Btn" onClick={() => setCollapsed((v) => !v)} title="Collapse sidebar">
              <ChevronLeft size={18} />
            </button>
          </div>

          <nav className="Atg-Nav">
            {builtNav.map((item) => (
              <NavLink
                key={item.path || item.label}
                item={item}
                depth={0}
                activePath={activePath}
                navigate={navigate}
                collapsed={collapsed}
              />
            ))}
          </nav>
        </aside>

        {/* ── Main ── */}
        <main className="Atg-Main">
          <header className="Atg-Topbar">
            <div className="Atg-Topbar-Title">
              <span className="crumb">Banao Intranet</span>
              <strong>{pageTitle}</strong>
            </div>
            <div className="Atg-Topbar-Actions">
              {loading && <span className="Sync-Badge">Syncing</span>}
              {!loading && !apiOnline && <span className="Sync-Badge-Danger">Offline</span>}
              <NotificationBell notifications={data.notifications || []} navigate={navigate} reloadData={reloadData} />
              <button className={activePath.startsWith("/profile") ? "Atg-User-Chip Active" : "Atg-User-Chip"} onClick={() => navigate("/profile/")}>
                <span className="Chip-Avatar">{initials}</span>
                <b>{displayName}</b>
              </button>
              <button className="Atg-Icon-Btn" onClick={logout} title="Logout"><LogOut size={16} /></button>
            </div>
          </header>

          {visibleErrors.length > 0 && (
            <div className="Atg-Error-Bar">
              <AlertTriangle size={16} />
              <span>{visibleErrors[0].status === 403 ? "Current User Does Not Have Permission For One Or More Records." : visibleErrors[0].message}</span>
            </div>
          )}

          <div className="Atg-Content">{children}</div>
        </main>
      </div>
    </>
  );
}

// ─── Notification Bell ──────────────────────────────────────
function NotificationBell({ notifications = [], navigate, reloadData }) {
  const [open, setOpen] = useState(false);
  const [busyId, setBusyId] = useState("");
  const [markAllBusy, setMarkAllBusy] = useState(false);
  const [optimisticRead, setOptimisticRead] = useState(false);
  const ref = useRef(null);
  const unread = optimisticRead ? [] : notifications.filter((item) => !item.is_read);
  const rows = [...notifications].sort((l, r) => new Date(r.created_at || 0) - new Date(l.created_at || 0)).slice(0, 8);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDocClick); document.removeEventListener("keydown", onKey); };
  }, [open]);

  const notificationPath = (item) => {
    const t = String(item.resource_type || item.category || "").toLowerCase();
    const id = item.resource_id || item.metadata?.project || item.metadata?.project_id;
    if (t.includes("project") && id) return `/project/dashboard/${id}/project/`;
    if (t.includes("leave")) return "/leave/apply/";
    if (t.includes("assessment")) return "/assessment/";
    return "/notifications/";
  };

  const review = async (item) => {
    setBusyId(String(item.id));
    try {
      if (!item.is_read) await apiPost(`/MainApp/Notifications/${item.id}/mark-read/`, {});
      if (reloadData) reloadData(["notifications"]);
      navigate(notificationPath(item));
      setOpen(false);
    } finally { setBusyId(""); }
  };

  const markAllRead = async () => {
    if (markAllBusy) return;
    setMarkAllBusy(true);
    setOptimisticRead(true);
    try {
      await apiPost("/MainApp/Notifications/mark-all-read/", {});
      setOptimisticRead(false);
      if (reloadData) reloadData(["notifications"]);
    } catch (err) {
      console.warn("Mark All Read API Error:", err);
      setOptimisticRead(false);
      if (reloadData) reloadData(["notifications"]);
    }
    setMarkAllBusy(false);
  };

  return (
    <div className="Atg-Notif-Bell" ref={ref}>
      <button className={open ? "Atg-Icon-Btn Active" : "Atg-Icon-Btn"} onClick={() => setOpen((v) => !v)} title="Notifications">
        <Bell size={16} />
        {unread.length > 0 && <span className="Atg-Notif-Count">{unread.length}</span>}
      </button>
      {open && (
        <div className="Atg-Notif-Popover">
          <div className="Atg-Notif-Head">
            <strong>Notifications</strong>
            <span>{unread.length} Unread</span>
            {unread.length > 0 && <button className="Atg-Link-Btn" onClick={markAllRead}>Mark All Read</button>}
            <button className="Atg-Link-Btn" onClick={() => { setOpen(false); navigate("/notifications/"); }}>View All</button>
          </div>
          <div className="Atg-Notif-List">
            {rows.map((item) => (
              <div key={item.id} className={item.is_read ? "Atg-Notif-Item" : "Atg-Notif-Item Unread"}>
                <div>
                  <strong>{item.title || item.category || "Notification"}</strong>
                  <p>{item.message || item.description || "Open This Notification."}</p>
                  <small>{item.created_at || ""}</small>
                </div>
                <button className="Atg-Soft-Btn" onClick={() => review(item)} disabled={busyId === String(item.id)}>
                  {busyId === String(item.id) ? "Opening" : "Review"}
                </button>
              </div>
            ))}
            {!rows.length && <div className="Atg-Notif-Empty">No Notifications Loaded.</div>}
          </div>
        </div>
      )}
    </div>
  );
}

function isCompleted(status = "") {
  return ["completed", "complete", "done", "passed", "submitted", "closed"].includes(String(status).toLowerCase());
}

export default App;
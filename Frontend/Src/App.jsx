import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Bell,
  BookOpen,
  BriefcaseBusiness,
  CalendarDays,
  ClipboardCheck,
  Download,
  DollarSign,
  FileText,
  Home,
  KeyRound,
  LogOut,
  Megaphone,
  Plug,
  Send,
  ShieldCheck,
  UserPlus,
  Users,
} from "lucide-react";
import { apiGet, apiPost, clearApiAuth, getApiSettings, unpackList } from "./Api/Client.js";
import { LoginScreen, ProfileScreen } from "./Screens/AuthScreens.jsx";
import { RouteRenderer } from "./Screens/AppScreens.jsx";

const navItems = [
  { label: "Home", path: "/home/", icon: Home },
  { label: "HRMS", path: "/hrms/", icon: Users },
  { label: "Employee Registrar", path: "/employee-registrar/", icon: UserPlus },
  { label: "Leave Apply", path: "/leave/apply/", icon: CalendarDays },
  { label: "Development Projects", path: "/project/dashboard/", icon: BriefcaseBusiness },
  { label: "Marketing Project", path: "/marketing-project/", icon: Megaphone },
  { label: "LMS / Banao", path: "/lms/", icon: BarChart3 },
  { label: "Finance", path: "/payments/?pay_month=current&month_name=May", icon: DollarSign },
  { label: "Payroll Downloads", path: "/payroll-downloads/", icon: Download },
  { label: "Payslips", path: "/payslips/", icon: FileText },
  { label: "Docs", path: "/docs/", icon: BookOpen },
  { label: "Assessment", path: "/assessment/", icon: ClipboardCheck },
  { label: "Workflow Intelligence", path: "/workflow/", icon: Plug },
  { label: "MCP Agents", path: "/mcp/", icon: KeyRound },
  { label: "Notifications", path: "/notifications/", icon: Bell },
  { label: "Change Password", path: "/change-password/", icon: KeyRound },
  { label: "Bank Details", path: "/Bankdetails/", icon: FileText },
  { label: "Send Offer", path: "/Onboard/Send_Offer", icon: Send },
  { label: "Send Certificate", path: "/send-certificate", icon: ShieldCheck },
  { label: "Deactivate Employee", path: "/deactivate-multiple-employee/", icon: AlertTriangle },
  { label: "Delay Management", path: "/delays/", icon: AlertTriangle },
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
  ["workflowSummary", "/WorkflowIntelligence/api/route-usage/summary/", "object"],
  ["topWorkflows", "/WorkflowIntelligence/api/route-usage/top-workflows/", "object"],
  ["businessWorkflows", "/WorkflowIntelligence/api/business-workflows/", "list"],
  ["workflowReports", "/WorkflowIntelligence/WorkflowReports/", "list"],
  ["routeUsageAggregates", "/WorkflowIntelligence/RouteUsageAggregates/", "list"],
  ["businessWorkflowMaps", "/WorkflowIntelligence/BusinessWorkflowMaps/", "list"],

  ["domains", "/Users/Domains/", "list"],
  ["departmentMemberships", "/Users/DepartmentMemberships/", "list"],
  ["goals", "/Users/Goals/", "list"],
  ["goalFeedback", "/Users/GoalFeedback/", "list"],
  ["userStatusSnapshots", "/Users/UserStatusSnapshots/", "list"],
  ["benchPeriods", "/Users/BenchPeriods/", "list"],
  ["employeeRatings", "/Users/EmployeeRatings/", "list"],
  ["employeeCertificates", "/Users/EmployeeCertificates/", "list"],
  ["employeeFeedback", "/Users/EmployeeFeedback/", "list"],
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
  // GithubExtension
  ["githubRepositories", "/GithubExtension/GitHubRepositories/", "list"],
  ["branchReviewers", "/GithubExtension/BranchReviewerAssignments/", "list"],
  ["branchTesters", "/GithubExtension/BranchTestingAssignments/", "list"],
  ["repoBranchStatuses", "/GithubExtension/RepositoryBranchStatuses/", "list"],
  // HtmlTemplate
  ["templateVariables", "/HtmlTemplate/TemplateVariables/", "list"],
  ["offerMacros", "/HtmlTemplate/OfferMacros/", "list"],
  ["contentTemplates", "/HtmlTemplate/ContentTemplates/", "list"],
  ["offerTemplates", "/HtmlTemplate/OfferTemplates/", "list"],
  ["genericHtmlTemplates", "/HtmlTemplate/GenericHtmlTemplates/", "list"],
  // L3
  ["collegePipelines", "/L3/CollegePipelineRecords/", "list"],
  ["collegeContacts", "/L3/CollegeContacts/", "list"],
  ["collegeAssignments", "/L3/CollegeAssignments/", "list"],
  ["collegeEmailTemplates", "/L3/CollegeEmailTemplates/", "list"],
  ["candidateProfiles", "/L3/CandidateProfiles/", "list"],
  ["talentAssignments", "/L3/TalentAssignments/", "list"],
  ["talentEmails", "/L3/TalentEmails/", "list"],
  ["talentPerformanceSnapshots", "/L3/TalentPerformanceSnapshots/", "list"],
  // IntegrationHub
  ["integrationProviders", "/IntegrationHub/IntegrationProviders/", "list"],
  ["integrationConnections", "/IntegrationHub/IntegrationConnections/", "list"],
  ["webhookInboxEvents", "/IntegrationHub/WebhookInboxEvents/", "list"],
  ["integrationSyncJobs", "/IntegrationHub/IntegrationSyncJobs/", "list"],
  ["integrationAttempts", "/IntegrationHub/IntegrationAttempts/", "list"],
  // McpAccessLayer
  ["agentPrincipals", "/McpAccessLayer/AgentPrincipals/", "list"],
  ["mcpToolDefinitions", "/McpAccessLayer/McpToolDefinitions/", "list"],
  ["mcpResourceDefinitions", "/McpAccessLayer/McpResourceDefinitions/", "list"],
  ["mcpAccessGrants", "/McpAccessLayer/McpAccessGrants/", "list"],
  ["mcpInvocationAudits", "/McpAccessLayer/McpInvocationAudits/", "list"],
  ["draftAgentActions", "/McpAccessLayer/DraftAgentActions/", "list"],
  // LegacyBridge
  ["legacyApplicationMaps", "/LegacyBridge/LegacyApplicationMaps/", "list"],
  ["legacyModelCrosswalks", "/LegacyBridge/LegacyModelCrosswalks/", "list"],
  ["migrationRuns", "/LegacyBridge/MigrationRuns/", "list"],
  ["legacyMigrationIssues", "/LegacyBridge/LegacyMigrationIssues/", "list"],
  // EnterpriseCore
  ["enterpriseTenants", "/EnterpriseCore/Tenants/", "list"],
  ["enterpriseOrganizations", "/EnterpriseCore/Organizations/", "list"],
  ["enterpriseBusinessUnits", "/EnterpriseCore/BusinessUnits/", "list"],
  ["enterpriseWorkspaces", "/EnterpriseCore/Workspaces/", "list"],
  ["enterpriseRoles", "/EnterpriseCore/Roles/", "list"],
  ["enterpriseRoleAssignments", "/EnterpriseCore/RoleAssignments/", "list"],
  ["accessAuditLogs", "/EnterpriseCore/AccessAuditLogs/", "list"],
];

function App() {
  const [settings, setSettings] = useState(getApiSettings);
  const [route, setRoute] = useState(() => window.location.pathname + window.location.search);
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("");
  const path = route.split("?")[0];
  const isLoginRoute = path.startsWith("/login");
  const hasAuth = Boolean(settings.basicAuth?.username && settings.basicAuth?.password);
  const { data, loading, errors, apiOnline, reload } = useIntranetData(reloadKey, hasAuth && !isLoginRoute);

  useEffect(() => {
    const onPop = () => setRoute(window.location.pathname + window.location.search);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((path) => {
    window.history.pushState(null, "", path);
    setRoute(window.location.pathname + window.location.search);
  }, []);

  useEffect(() => {
    if (!selectedEmployeeId && data.employees?.length) {
      const currentEmployee =
        data.me?.employees?.[0]?.id ||
        (data.employees || []).find((item) => String(item.user) === String(data.me?.user?.id))?.id;
      setSelectedEmployeeId(String(currentEmployee || data.employees?.[0]?.id || ""));
    }
  }, [data.employees, data.me, selectedEmployeeId]);

  useEffect(() => {
    if (!hasAuth || isLoginRoute) return;
    const unauthorized = errors.some((error) => error.status === 401);
    const offline = !loading && !apiOnline && errors.length > 0;
    if (unauthorized || offline) {
      clearApiAuth();
      setSettings(getApiSettings());
      navigate("/login/");
    }
  }, [errors, loading, apiOnline, hasAuth, isLoginRoute, navigate]);

  const login = () => {
    setSettings(getApiSettings());
    setReloadKey((value) => value + 1);
    navigate("/home/");
  };

  const logout = () => {
    clearApiAuth();
    setSettings(getApiSettings());
    setReloadKey((value) => value + 1);
    navigate("/login/");
  };

  if (!hasAuth || path.startsWith("/login")) {
    return <LoginScreen settings={settings} onLogin={login} />;
  }

  const commonProps = {
    data,
    settings,
    selectedEmployeeId,
    reload,
    navigate,
  };

  return (
    <AppShell route={route} navigate={navigate} data={data} apiOnline={apiOnline} loading={loading} logout={logout} errors={errors} reloadData={commonProps.reload}>
      {path.startsWith("/profile") ? <ProfileScreen data={data} onLogout={logout} reload={reload} /> : <RouteRenderer route={route} {...commonProps} />}
    </AppShell>
  );
}

function useIntranetData(reloadKey, enabled) {
  const [state, setState] = useState({ data: {}, loading: false, errors: [], apiOnline: false });
  const hasInitiallyLoaded = useRef(false);

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

  const load = useCallback(async (keysFilter) => {
    if (!enabled) {
      setState({ data: {}, loading: false, errors: [], apiOnline: false });
      hasInitiallyLoaded.current = false;
      return;
    }
    
    let effectiveFilter = keysFilter;
    if (keysFilter === undefined && hasInitiallyLoaded.current) {
      effectiveFilter = ["me", "notifications", "employees", "tasks", "projects", "leaveRequests"];
    } else if (keysFilter === true || keysFilter === "__all__") {
      effectiveFilter = undefined;
    }
    const subset = Array.isArray(effectiveFilter) && effectiveFilter.length
      ? endpointMap.filter(([key]) => effectiveFilter.includes(key))
      : endpointMap;
    const isPartial = subset.length !== endpointMap.length;
    setState((current) => ({ ...current, loading: !isPartial ? true : current.loading, errors: isPartial ? current.errors : [] }));
    const results = await Promise.allSettled(subset.map(([key, p, mode]) => apiGet(p).then((payload) => ({ key, payload, mode }))));
    setState((current) => {
      const nextData = isPartial ? { ...current.data } : {};
      const requestErrors = isPartial ? current.errors.filter((err) => !effectiveFilter.includes(err.key)) : [];
      results.forEach((result, index) => {
        const [key, , mode] = subset[index];
        if (result.status === "fulfilled") {
          applyPayload(nextData, key, mode, result.value.payload);
        } else {
          requestErrors.push({ key, status: result.reason?.status, message: result.reason?.message || "Request failed" });
          if (!isPartial) nextData[key] = mode === "list" ? [] : null;
        }
      });
      return {
        data: nextData,
        loading: false,
        errors: requestErrors,
        apiOnline: isPartial ? current.apiOnline : requestErrors.length < endpointMap.length,
      };
    });
    if (!isPartial) hasInitiallyLoaded.current = true;
  }, [enabled]);

  useEffect(() => {
    load("__all__");
  }, [load, reloadKey]);

  return { ...state, reload: load };
}

function AppShell({ children, route, navigate, data, apiOnline, loading, logout, errors, reloadData }) {
  const activePath = route.split("?")[0];
  const activeItem = navItems.find((item) => activePath === item.path || (item.path !== "/home/" && activePath.startsWith(item.path.replace(/\/$/, ""))));
  const pageTitle = activePath.startsWith("/profile") ? "Profile" : activeItem?.label || "Home";
  const user = data.me?.user || data.me?.account || data.me || {};
  const employee = data.me?.employees?.[0] || (data.employees || []).find((item) => String(item.user) === String(user.id)) || {};
  const displayName = employee.display_name || employee.displayName || user.fullName || user.full_name || user.username || "Profile";
  const initials = String(displayName).split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase() || "U";
  const visibleErrors = errors.filter((item) => item.status && item.status !== 401).slice(0, 1);

  return (
    <div className="erp-app">
      <aside className="erp-sidebar">
        <div className="brand-block">
          <div className="brand-mark">B</div>
          <div className="brand-copy">
            <strong>Banao</strong>
            <span>Intranet v2</span>
          </div>
        </div>
        <nav className="side-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = activePath === item.path || (item.path !== "/home/" && activePath.startsWith(item.path.replace(/\/$/, "")));
            return (
              <button key={item.path} className={active ? "active" : ""} onClick={() => navigate(item.path)} title={item.label}>
                <Icon size={17} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="erp-main">
        <header className="erp-topbar clean-topbar">
          <div className="topbar-title">
            <span className="crumb">Banao Intranet</span>
            <strong>{pageTitle}</strong>
          </div>
          <div className="topbar-actions user-actions">
            {loading && <span className="sync-state">Syncing</span>}
            {!loading && !apiOnline && <span className="sync-state danger">Offline</span>}
            <NotificationBell notifications={data.notifications || []} navigate={navigate} reloadData={reloadData} />
            <button className={activePath.startsWith("/profile") ? "user-chip active" : "user-chip"} onClick={() => navigate("/profile/")}>
              <span>{initials}</span>
              <b>{displayName}</b>
            </button>
            <button className="icon-button" onClick={logout} title="Logout"><LogOut size={16} /></button>
          </div>
        </header>
        {visibleErrors.length > 0 && (
          <section className="auth-alert">
            <AlertTriangle size={16} />
            <span>{visibleErrors[0].status === 403 ? "Current User Does Not Have Permission For One Or More Records." : visibleErrors[0].message}</span>
          </section>
        )}
        {children}
      </main>
    </div>
  );
}

function NotificationBell({ notifications = [], navigate, reloadData }) {
  const [open, setOpen] = useState(false);
  const [busyId, setBusyId] = useState("");
  const ref = useRef(null);
  const unread = notifications.filter((item) => !item.is_read);
  const rows = [...notifications].sort((left, right) => new Date(right.created_at || 0) - new Date(left.created_at || 0)).slice(0, 8);

  useEffect(() => {
    if (!open) return undefined;
    const onDocumentClick = (event) => {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    };
    const onKeyDown = (event) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDocumentClick);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDocumentClick);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const notificationPath = (item) => {
    const resourceType = String(item.resource_type || item.category || "").toLowerCase();
    const resourceId = item.resource_id || item.metadata?.project || item.metadata?.project_id;
    if (resourceType.includes("project") && resourceId) return `/project/dashboard/${resourceId}/project/`;
    if (resourceType.includes("leave")) return "/leave/apply/";
    if (resourceType.includes("assessment")) return "/assessment/";
    return "/notifications/";
  };

  const review = async (item) => {
    setBusyId(String(item.id));
    try {
      if (!item.is_read) await apiPost(`/MainApp/Notifications/${item.id}/read/`, {});
      if (reloadData) reloadData(["notifications"]);
      navigate(notificationPath(item));
      setOpen(false);
    } finally {
      setBusyId("");
    }
  };

  const markAllRead = async () => {
    await Promise.allSettled(unread.map((item) => apiPost(`/MainApp/Notifications/${item.id}/read/`, {})));
    if (reloadData) reloadData(["notifications"]);
  };

  return (
    <div className="notification-bell" ref={ref}>
      <button className={open ? "icon-button active" : "icon-button"} onClick={() => setOpen((value) => !value)} title="Notifications">
        <Bell size={16} />
        {unread.length > 0 && <span className="notification-count">{unread.length}</span>}
      </button>
      {open && (
        <div className="notification-popover">
          <div className="notification-popover-head">
            <strong>Notifications</strong>
            <span>{unread.length} Unread</span>
            {unread.length > 0 && <button className="link-button" onClick={markAllRead}>Mark All Read</button>}
            <button className="link-button" onClick={() => { setOpen(false); navigate("/notifications/"); }}>View All</button>
          </div>
          <div className="notification-list">
            {rows.map((item) => (
              <div className={item.is_read ? "notification-item" : "notification-item unread"} key={item.id}>
                <div>
                  <strong>{item.title || item.category || "Notification"}</strong>
                  <p>{item.message || item.description || "Open This Notification."}</p>
                  <small>{item.created_at || ""}</small>
                </div>
                <button className="soft-button small" onClick={() => review(item)} disabled={busyId === String(item.id)}>
                  {busyId === String(item.id) ? "Opening" : "Review"}
                </button>
              </div>
            ))}
            {!rows.length && <div className="notification-empty">No Notifications Loaded.</div>}
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

import React, { useEffect } from "react";

import { AssessmentScreen } from "./AssessmentScreen.jsx";
import { AdminChangePasswordScreen } from "./AdminChangePasswordScreen.jsx";
import { BankDetailsScreen } from "./BankDetailsScreen.jsx";
import { DeactivateEmployeeScreen } from "./DeactivateEmployeeScreen.jsx";
import { DelayManagementScreen } from "./DelayManagementScreen.jsx";
import { DocsDetailScreen, DocsScreen } from "./DocsScreen.jsx";
import { EmployeeRegistrarScreen } from "./EmployeeRegistrarScreen.jsx";
import { FinanceScreen } from "./FinanceScreen.jsx";
import { HomeScreen } from "./HomeScreen.jsx";
import { HrmsScreen } from "./HrmsScreen.jsx";
import { LeaveApplyScreen } from "./LeaveApplyScreen.jsx";
import { LmsScreen } from "./LmsScreen.jsx";
import { MarketingProjectScreen } from "./MarketingProjectScreen.jsx";
import { McpScreen } from "./McpScreen.jsx";
import { NotificationsScreen } from "./NotificationsScreen.jsx";
import OnboardingScreen from "./OnboardingScreen.jsx";
import { PayrollDownloadsScreen } from "./PayrollDownloadsScreen.jsx";
import { PayslipsScreen } from "./PayslipsScreen.jsx";
import { ProjectDashboardScreen } from "./ProjectDashboardScreen.jsx";
import { SendCertificateScreen } from "./SendCertificateScreen.jsx";
import { SendOfferScreen } from "./SendOfferScreen.jsx";
import { FeedbackScreen } from "./FeedbackScreen.jsx";

const SCREEN_DATA = {
  hrms: ["domains", "departmentMemberships", "userStatusSnapshots", "benchPeriods", "employeeRatings", "employeeCertificates", "leaveTransactions", "resignationRequests", "userEffortReports", "interviewProgress"],
  lms: ["lmsLeads", "learningPaths", "learningModules", "learningAssignments", "leadQueueSnapshots", "revenueSnapshots"],
  docs: ["docs", "docPermissions", "driveFiles", "docVersions", "knowledgeActivities", "driveFolders"],
  assessment: ["assessmentLegacy", "assessmentAssignments", "assessmentTemplates"],
  payments: ["financeDashboard", "payPeriods", "payrollRuns", "payrollLineItems", "payslipDocuments", "paymentOrders", "compensationPlans", "financeBankAccounts", "approvalDecisions", "payoutExecutions", "paymentWebhookEvents"],
  bank: ["bankAccounts"],
  payslips: ["payslipDocuments", "payrollLineItems", "payrollRuns"],
  payroll: ["payPeriods", "payrollRuns", "payrollLineItems", "payslipDocuments", "paymentOrders"],
  offers: ["offers", "templateVariables", "offerMacros", "contentTemplates", "offerTemplates", "genericHtmlTemplates"],
  registrar: ["subDepartments", "payProfiles", "positions", "leavePolicies"],
  project: ["projectDocuments", "repositories", "workEntries", "taskActivities", "projectContacts", "defaultCheckpoints", "milestoneComponents", "complianceCampaigns", "complianceAssignments", "delays", "slackThreads", "slackMessages", "externalWorkMappings", "clickupMappings", "managerAbbreviations"],
  l3: ["collegePipelines", "collegeContacts", "collegeAssignments", "collegeEmailTemplates", "candidateProfiles", "talentAssignments", "talentEmails", "talentPerformanceSnapshots"],
  github: ["githubRepositories", "branchReviewers", "branchTesters", "repoBranchStatuses", "gitRepoSnapshots", "gitActivitySnapshots", "repoUtilityRequests"],
  integrations: ["integrationProviders", "integrationConnections", "webhookInboxEvents", "integrationSyncJobs", "integrationAttempts"],
  mcp: ["agentPrincipals", "mcpToolDefinitions", "mcpResourceDefinitions", "mcpAccessGrants", "mcpInvocationAudits", "draftAgentActions"],
  legacy: ["legacyApplicationMaps", "legacyModelCrosswalks", "migrationRuns", "legacyMigrationIssues"],
  enterprise: ["enterpriseTenants", "enterpriseOrganizations", "enterpriseBusinessUnits", "enterpriseWorkspaces", "enterpriseRoles", "enterpriseRoleAssignments", "accessAuditLogs"],
};

function LazyLoader({ screen, loadMissing, children }) {
  useEffect(() => {
    if (!loadMissing || !screen) return;
    const keys = SCREEN_DATA[screen];
    if (keys) loadMissing(keys);
  }, [screen, loadMissing]);
  return children;
}

export function RouteRenderer(props) {
  const path = (props.route || "").split("?")[0];
  const { loadMissing } = props;
  let screen = null;
  let component = null;

  if (path.startsWith("/onboarding")) { screen = null; component = <OnboardingScreen {...props} />; }
  else if (path.startsWith("/hrms")) { screen = "hrms"; component = <HrmsScreen {...props} />; }
  else if (path.startsWith("/employee-registrar")) { screen = "registrar"; component = <EmployeeRegistrarScreen {...props} />; }
  else if (path.startsWith("/leave")) { screen = null; component = <LeaveApplyScreen {...props} />; }
  else if (path.startsWith("/delays")) { screen = null; component = <DelayManagementScreen {...props} />; }
  else if (path.startsWith("/project/dashboard") || path.startsWith("/marketing-project")) { screen = "project"; component = <ProjectDashboardScreen {...props} />; }
  else if (path.startsWith("/docs")) { screen = "docs"; component = path.includes("post-detail") ? <DocsDetailScreen {...props} /> : <DocsScreen {...props} />; }
  else if (path.startsWith("/Bankdetails") || path.startsWith("/bank")) { screen = "bank"; component = <BankDetailsScreen {...props} />; }
  else if (path.startsWith("/Onboard/Send_Offer") || path.startsWith("/send-certificate")) { screen = "offers"; component = path.startsWith("/Onboard") ? <SendOfferScreen {...props} /> : <SendCertificateScreen {...props} />; }
  else if (path.startsWith("/deactivate")) { screen = null; component = <DeactivateEmployeeScreen {...props} />; }
  else if (path.startsWith("/assessment")) { screen = "assessment"; component = <AssessmentScreen {...props} />; }
  else if (path.startsWith("/payroll-downloads") || path.startsWith("/Payroll")) { screen = "payroll"; component = <PayrollDownloadsScreen {...props} />; }
  else if (path.startsWith("/payslips")) { screen = "payslips"; component = <PayslipsScreen {...props} />; }
  else if (path.startsWith("/payments") || path.startsWith("/finance")) { screen = "payments"; component = <FinanceScreen {...props} />; }
  else if (path.startsWith("/notifications")) { screen = null; component = <NotificationsScreen {...props} />; }
  else if (path.startsWith("/change-password")) { screen = null; component = <AdminChangePasswordScreen {...props} />; }
  else if (path.startsWith("/mcp")) { screen = "mcp"; component = <McpScreen {...props} />; }
  else if (path.startsWith("/feedback")) { screen = null; component = <FeedbackScreen {...props} />; }
  else if (path.startsWith("/lms")) { screen = "lms"; component = <LmsScreen {...props} />; }
  else { screen = null; component = <HomeScreen {...props} />; }

  return <LazyLoader screen={screen} loadMissing={loadMissing}>{component}</LazyLoader>;
}
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoadingSkeleton } from './Components/NavigationComponents';

/**
 * MASTER ROUTES - ALL 95+ FEATURES
 */

// ============================================================================
// P0 - CRITICAL FEATURES (ALREADY BUILT)
// ============================================================================

const CompleteDashboard = lazy(() => import('./Pages/CompleteDashboard'));
const CompleteFinance = lazy(() => import('./Pages/CompleteFinance'));
const McpApiExplorer = lazy(() => import('./Pages/McpApiExplorer'));

// P0 - Building Next
const CompleteOfferSystem = lazy(() => import('./Pages/CompleteOfferSystem'));
const CompleteLeaveSystem = lazy(() => import('./Pages/CompleteLeaveSystem'));
const CompleteAttendanceEOD = lazy(() => import('./Pages/CompleteAttendanceEOD'));
const CompleteGoalsFeedback = lazy(() => import('./Pages/CompleteGoalsFeedback'));

// ============================================================================
// P1 - HIGH PRIORITY FEATURES
// ============================================================================

const CompleteBugTracking = lazy(() => import('./Pages/CompleteBugTracking'));
const CompletePasswordVault = lazy(() => import('./Pages/CompletePasswordVault'));
const CompleteProjectManagement = lazy(() => import('./Pages/CompleteProjectManagement'));
const CompleteCertificates = lazy(() => import('./Pages/CompleteCertificates'));
const CompleteHierarchy = lazy(() => import('./Pages/CompleteHierarchy'));
const EmployeeRegistration = lazy(() => import('./Pages/EmployeeRegistration'));

// ============================================================================
// P2 - MEDIUM PRIORITY FEATURES
// ============================================================================

const CompleteProfiles = lazy(() => import('./Pages/CompleteProfiles'));
const CompleteUtilities = lazy(() => import('./Pages/CompleteUtilities'));
const CompleteDocumentation = lazy(() => import('./Pages/CompleteDocumentation'));

// ============================================================================
// EXISTING PAGES (From ReBuild)
// ============================================================================

const HRMSDashboard = lazy(() => import('./Pages/HRMSDashboard'));
const PayrollManagement = lazy(() => import('./Pages/PayrollManagement'));
const LeaveManagement = lazy(() => import('./Pages/LeaveManagement'));
const EODManagement = lazy(() => import('./Pages/EODManagement'));

// Screens
const HomeScreen = lazy(() => import('./Screens/HomeScreen'));
const HrmsScreen = lazy(() => import('./Screens/HrmsScreen'));
const FinanceScreen = lazy(() => import('./Screens/FinanceScreen'));
const TasksScreen = lazy(() => import('./Screens/TasksScreen'));
const ProjectDashboardScreen = lazy(() => import('./Screens/ProjectDashboardScreen'));
const MarketingProjectScreen = lazy(() => import('./Screens/MarketingProjectScreen'));
const LeaveApplyScreen = lazy(() => import('./Screens/LeaveApplyScreen'));
const PayslipsScreen = lazy(() => import('./Screens/PayslipsScreen'));
const PayrollDownloadsScreen = lazy(() => import('./Screens/PayrollDownloadsScreen'));
const SendOfferScreen = lazy(() => import('./Screens/SendOfferScreen'));
const SendCertificateScreen = lazy(() => import('./Screens/SendCertificateScreen'));
const EmployeeRegistrarScreen = lazy(() => import('./Screens/EmployeeRegistrarScreen'));
const DeactivateEmployeeScreen = lazy(() => import('./Screens/DeactivateEmployeeScreen'));
const BankDetailsScreen = lazy(() => import('./Screens/BankDetailsScreen'));
const DocsScreen = lazy(() => import('./Screens/DocsScreen'));
const LmsScreen = lazy(() => import('./Screens/LmsScreen'));
const AssessmentScreen = lazy(() => import('./Screens/AssessmentScreen'));
const WorkflowIntelligenceScreen = lazy(() => import('./Screens/WorkflowIntelligenceScreen'));
const NotificationsScreen = lazy(() => import('./Screens/NotificationsScreen'));
const McpScreen = lazy(() => import('./Screens/McpScreen'));
const AdminChangePasswordScreen = lazy(() => import('./Screens/AdminChangePasswordScreen'));
const AuthScreens = lazy(() => import('./Screens/AuthScreens'));
const ConnectedSummaryScreen = lazy(() => import('./Screens/ConnectedSummaryScreen'));
const OfferAcceptanceScreen = lazy(() => import('./Screens/OfferAcceptanceScreen'));

// ============================================================================
// PROTECTED ROUTE WRAPPER
// ============================================================================

const ProtectedRoute = ({ children, requiredRole }) => {
  const token = localStorage.getItem('authToken');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && !user.roles?.includes(requiredRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

// ============================================================================
// MASTER ROUTER
// ============================================================================

const MasterRoutes = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSkeleton type="card" count={3} />}>
        <Routes>
          {/* ========================================== */}
          {/* AUTHENTICATION */}
          {/* ========================================== */}
          <Route path="/login" element={<AuthScreens />} />
          <Route path="/register" element={<AuthScreens />} />
          <Route path="/forgot-password" element={<AuthScreens />} />
          <Route path="/offer/accept/:token" element={<OfferAcceptanceScreen />} />

          {/* ========================================== */}
          {/* HOME / DASHBOARD */}
          {/* ========================================== */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HomeScreen />
              </ProtectedRoute>
            }
          />

          {/* ========================================== */}
          {/* P0 - CRITICAL FEATURES (COMPREHENSIVE PAGES) */}
          {/* ========================================== */}

          {/* Complete HRMS Dashboard - Replaces: HrmsView, ProfileDetailView, ProfileInlineView, etc. */}
          <Route
            path="/hrms/complete"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <CompleteDashboard />
              </ProtectedRoute>
            }
          />

          {/* Complete Finance & Payroll */}
          <Route
            path="/finance/complete"
            element={
              <ProtectedRoute requiredRole="FINANCE_MANAGER">
                <CompleteFinance />
              </ProtectedRoute>
            }
          />

          {/* Complete Offer System */}
          <Route
            path="/offers/complete"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <CompleteOfferSystem />
              </ProtectedRoute>
            }
          />

          {/* Complete Leave System */}
          <Route
            path="/leaves/complete"
            element={
              <ProtectedRoute>
                <CompleteLeaveSystem />
              </ProtectedRoute>
            }
          />

          {/* Complete Attendance & EOD */}
          <Route
            path="/attendance/complete"
            element={
              <ProtectedRoute>
                <CompleteAttendanceEOD />
              </ProtectedRoute>
            }
          />

          {/* Complete Goals & Feedback */}
          <Route
            path="/goals/complete"
            element={
              <ProtectedRoute>
                <CompleteGoalsFeedback />
              </ProtectedRoute>
            }
          />

          {/* ========================================== */}
          {/* P1 - HIGH PRIORITY FEATURES */}
          {/* ========================================== */}

          {/* Complete Bug/Task Tracking - Replaces 9 views */}
          <Route
            path="/bugs/complete"
            element={
              <ProtectedRoute>
                <CompleteBugTracking />
              </ProtectedRoute>
            }
          />

          {/* Complete Password Vault  */}
          <Route
            path="/vault"
            element={
              <ProtectedRoute>
                <CompletePasswordVault />
              </ProtectedRoute>
            }
          />

          {/* Complete Project Management  */}
          <Route
            path="/projects/complete"
            element={
              <ProtectedRoute>
                <CompleteProjectManagement />
              </ProtectedRoute>
            }
          />

          {/* Complete Certificates */}
          <Route
            path="/certificates/complete"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <CompleteCertificates />
              </ProtectedRoute>
            }
          />

          {/* Complete Hierarchy  */}
          <Route
            path="/hierarchy"
            element={
              <ProtectedRoute requiredRole="MANAGER">
                <CompleteHierarchy />
              </ProtectedRoute>
            }
          />

          {/* Employee Registration - Replaces EmployeeRegisterView */}
          <Route
            path="/employee/register"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <EmployeeRegistration />
              </ProtectedRoute>
            }
          />

          {/* ========================================== */}
          {/* P2 - MEDIUM PRIORITY FEATURES */}
          {/* ========================================== */}

          {/* Complete Profiles -  */}
          <Route
            path="/profiles/complete"
            element={
              <ProtectedRoute>
                <CompleteProfiles />
              </ProtectedRoute>
            }
          />

          {/* Utilities - Documentation, Search, API Testing */}
          <Route
            path="/utilities"
            element={
              <ProtectedRoute>
                <CompleteUtilities />
              </ProtectedRoute>
            }
          />

          {/* Documentation */}
          <Route
            path="/documentation"
            element={
              <ProtectedRoute>
                <CompleteDocumentation />
              </ProtectedRoute>
            }
          />

          {/* ========================================== */}
          {/* EXISTING SCREENS (From ReBuild) */}
          {/* ========================================== */}

          <Route
            path="/hrms"
            element={
              <ProtectedRoute>
                <HrmsScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/finance"
            element={
              <ProtectedRoute>
                <FinanceScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/tasks"
            element={
              <ProtectedRoute>
                <TasksScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectDashboardScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/projects/marketing"
            element={
              <ProtectedRoute>
                <MarketingProjectScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/leave/apply"
            element={
              <ProtectedRoute>
                <LeaveApplyScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/payslips"
            element={
              <ProtectedRoute>
                <PayslipsScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/payroll/downloads"
            element={
              <ProtectedRoute>
                <PayrollDownloadsScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/offer/send"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <SendOfferScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/certificate/send"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <SendCertificateScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/employee/registrar"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <EmployeeRegistrarScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/employee/deactivate"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <DeactivateEmployeeScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/bank-details"
            element={
              <ProtectedRoute>
                <BankDetailsScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/docs"
            element={
              <ProtectedRoute>
                <DocsScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/lms"
            element={
              <ProtectedRoute>
                <LmsScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/assessment"
            element={
              <ProtectedRoute>
                <AssessmentScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/workflow-intelligence"
            element={
              <ProtectedRoute>
                <WorkflowIntelligenceScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <NotificationsScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/mcp"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <McpScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/mcp-api-explorer"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <McpApiExplorer />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/change-password"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <AdminChangePasswordScreen />
              </ProtectedRoute>
            }
          />

          <Route
            path="/summary/connected"
            element={
              <ProtectedRoute>
                <ConnectedSummaryScreen />
              </ProtectedRoute>
            }
          />

          {/* ========================================== */}
          {/* LEGACY ROUTES (Original 4 Pages) */}
          {/* ========================================== */}

          <Route
            path="/hrms-dashboard"
            element={
              <ProtectedRoute>
                <HRMSDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/payroll-management"
            element={
              <ProtectedRoute requiredRole="FINANCE_MANAGER">
                <PayrollManagement />
              </ProtectedRoute>
            }
          />

          <Route
            path="/leave-management"
            element={
              <ProtectedRoute>
                <LeaveManagement />
              </ProtectedRoute>
            }
          />

          <Route
            path="/eod-management"
            element={
              <ProtectedRoute>
                <EODManagement />
              </ProtectedRoute>
            }
          />

          {/* ========================================== */}
          {/* ERROR PAGES */}
          {/* ========================================== */}

          <Route path="/unauthorized" element={<div>Unauthorized Access</div>} />
          <Route path="*" element={<div>404 - Page Not Found</div>} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

export default MasterRoutes;
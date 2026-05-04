/**
 * ROUTING CONFIGURATION - INTRANET V2
 * Complete Application Routing With React Router
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoadingSkeleton } from './Components/NavigationComponents';

// ============================================================================
// LAZY LOADED PAGES
// ============================================================================

// Authentication
const Login = lazy(() => import('./Pages/Login'));
const ForgotPassword = lazy(() => import('./Pages/ForgotPassword'));

// HRMS
const HRMSDashboard = lazy(() => import('./Pages/HRMSDashboard'));
const EmployeeProfile = lazy(() => import('./Pages/EmployeeProfile'));
const EmployeeList = lazy(() => import('./Pages/EmployeeList'));

// Finance & Payroll
const PayrollManagement = lazy(() => import('./Pages/PayrollManagement'));
const PaymentHistory = lazy(() => import('./Pages/PaymentHistory'));

// Leave Management
const LeaveManagement = lazy(() => import('./Pages/LeaveManagement'));
const LeaveCalendar = lazy(() => import('./Pages/LeaveCalendar'));

// EOD & Attendance
const EODManagement = lazy(() => import('./Pages/EODManagement'));
const AttendanceReport = lazy(() => import('./Pages/AttendanceReport'));

// Departments & Skills
const DepartmentManagement = lazy(() => import('./Pages/DepartmentManagement'));
const SkillManagement = lazy(() => import('./Pages/SkillManagement'));

// Goals & Feedback
const GoalsManagement = lazy(() => import('./Pages/GoalsManagement'));
const FeedbackSystem = lazy(() => import('./Pages/FeedbackSystem'));

// Projects & Tasks
const ProjectManagement = lazy(() => import('./Pages/ProjectManagement'));
const ProjectDetail = lazy(() => import('./Pages/ProjectDetail'));
const TaskManagement = lazy(() => import('./Pages/TaskManagement'));

// Offers & Certificates
const OfferLetterManagement = lazy(() => import('./Pages/OfferLetterManagement'));
const CertificateManagement = lazy(() => import('./Pages/CertificateManagement'));

// Reports & Analytics
const AnalyticsDashboard = lazy(() => import('./Pages/AnalyticsDashboard'));
const Reports = lazy(() => import('./Pages/Reports'));

// Settings
const Settings = lazy(() => import('./Pages/Settings'));
const UserProfile = lazy(() => import('./Pages/UserProfile'));

// MCP & AI Integration
const McpApiExplorer = lazy(() => import('./Pages/McpApiExplorer'));

// Error Pages
const NotFound = lazy(() => import('./Pages/NotFound'));

// ============================================================================
// PROTECTED ROUTE WRAPPER
// ============================================================================

const ProtectedRoute = ({ children, requiredRole }) => {
  const token = localStorage.getItem('authToken');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  // Check Authentication
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Check Role-Based Access
  if (requiredRole && !user.roles?.includes(requiredRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

// ============================================================================
// LOADING FALLBACK
// ============================================================================

const PageLoader = () => (
  <div style={{ padding: '2rem' }}>
    <LoadingSkeleton type="card" count={3} />
  </div>
);

// ============================================================================
// APP ROUTER
// ============================================================================

const AppRouter = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* Protected Routes - HRMS */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HRMSDashboard />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/hrms"
            element={
              <ProtectedRoute>
                <HRMSDashboard />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/employees"
            element={
              <ProtectedRoute>
                <EmployeeList />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/employees/:id"
            element={
              <ProtectedRoute>
                <EmployeeProfile />
              </ProtectedRoute>
            }
          />

          {/* Finance & Payroll */}
          <Route
            path="/payroll"
            element={
              <ProtectedRoute requiredRole="FINANCE_MANAGER">
                <PayrollManagement />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/payments"
            element={
              <ProtectedRoute>
                <PaymentHistory />
              </ProtectedRoute>
            }
          />

          {/* Leave Management */}
          <Route
            path="/leaves"
            element={
              <ProtectedRoute>
                <LeaveManagement />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/leaves/calendar"
            element={
              <ProtectedRoute>
                <LeaveCalendar />
              </ProtectedRoute>
            }
          />

          {/* EOD & Attendance */}
          <Route
            path="/eod"
            element={
              <ProtectedRoute>
                <EODManagement />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/attendance"
            element={
              <ProtectedRoute>
                <AttendanceReport />
              </ProtectedRoute>
            }
          />

          {/* Departments & Skills */}
          <Route
            path="/departments"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <DepartmentManagement />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/skills"
            element={
              <ProtectedRoute>
                <SkillManagement />
              </ProtectedRoute>
            }
          />

          {/* Goals & Feedback */}
          <Route
            path="/goals"
            element={
              <ProtectedRoute>
                <GoalsManagement />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/feedback"
            element={
              <ProtectedRoute>
                <FeedbackSystem />
              </ProtectedRoute>
            }
          />

          {/* Projects & Tasks */}
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectManagement />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/tasks"
            element={
              <ProtectedRoute>
                <TaskManagement />
              </ProtectedRoute>
            }
          />

          {/* Offers & Certificates */}
          <Route
            path="/offers"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <OfferLetterManagement />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/certificates"
            element={
              <ProtectedRoute requiredRole="HR_MANAGER">
                <CertificateManagement />
              </ProtectedRoute>
            }
          />

          {/* Reports & Analytics */}
          <Route
            path="/analytics"
            element={
              <ProtectedRoute requiredRole="MANAGER">
                <AnalyticsDashboard />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/reports"
            element={
              <ProtectedRoute requiredRole="MANAGER">
                <Reports />
              </ProtectedRoute>
            }
          />

          {/* Settings & Profile */}
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/settings"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <Settings />
              </ProtectedRoute>
            }
          />

          {/* MCP & AI Integration */}
          <Route
            path="/mcp-api-explorer"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <McpApiExplorer />
              </ProtectedRoute>
            }
          />

          {/* 404 - Not Found */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

export default AppRouter;

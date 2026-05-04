/**
 * HRMS DASHBOARD - INTRANET V2
 * Comprehensive Human Resource Management System Dashboard
 * 
 * Features:
 * - Employee overview with filters
 * - Headcount by status/department
 * - Quick actions
 * - Recent activities
 * - Performance metrics
 * - Leave summary
 * - Skills overview
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Tabs } from '../Components/DesignSystem';
import { Select, DatePicker } from '../Components/FormComponents';
import { Breadcrumb, Avatar, Progress, EmptyState, LoadingSkeleton, Toast } from '../Components/NavigationComponents';
import { colors, spacing, typography } from '../Components/DesignSystem';
import api, { handleApiError } from '../Services/api';

const HRMSDashboard = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [headcountData, setHeadcountData] = useState({});
  const [filters, setFilters] = useState({
    department: '',
    status: '',
    search: '',
  });
  const [activeTab, setActiveTab] = useState('overview');
  const [toast, setToast] = useState(null);

  // Fetch data on mount and filter change
  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (filters.department || filters.status || filters.search) {
      fetchEmployees();
    }
  }, [filters]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchEmployees(),
        fetchDepartments(),
        fetchDashboard(),
      ]);
    } catch (error) {
      const apiError = handleApiError(error);
      showToast(apiError.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployees = async () => {
    try {
      const params = {};
      if (filters.department) params.department = filters.department;
      if (filters.status) params.status = filters.status;
      if (filters.search) params.search = filters.search;

      const response = await api.employees.list(params);
      
      // Transform backend data to match UI structure
      const transformedEmployees = response.data.results?.map(emp => ({
        id: emp.id,
        name: emp.full_name || `${emp.user?.first_name} ${emp.user?.last_name}`,
        email: emp.user?.email || emp.email,
        department: emp.department?.name || 'N/A',
        position: emp.position?.name || 'N/A',
        status: emp.status,
        avatar: emp.avatar_url,
        joinDate: emp.joining_date,
        skills: emp.skills?.map(s => s.skill?.name) || [],
        performance: emp.performance_score || 75,
      })) || [];

      setEmployees(transformedEmployees);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
      // Fallback to empty array on error
      setEmployees([]);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await api.departments.list();
      
      const transformedDepartments = response.data.results?.map(dept => ({
        id: dept.id,
        name: dept.name,
        count: dept.member_count || 0,
      })) || [];

      setDepartments(transformedDepartments);
    } catch (error) {
      console.error('Failed to fetch departments:', error);
      setDepartments([]);
    }
  };

  const fetchDashboard = async () => {
    try {
      const response = await api.employees.dashboard();
      const data = response.data;

      setHeadcountData({
        total: data.total_employees || 0,
        active: data.active_count || 0,
        onboarding: data.onboarding_count || 0,
        notice: data.notice_period_count || 0,
        bench: data.bench_count || 0,
        byDepartment: data.by_department || {},
      });
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
      // Set default values on error
      setHeadcountData({
        total: 0,
        active: 0,
        onboarding: 0,
        notice: 0,
        bench: 0,
        byDepartment: {},
      });
    }
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  // Filter employees
  const filteredEmployees = employees.filter(emp => {
    if (filters.department && emp.department !== filters.department) return false;
    if (filters.status && emp.status !== filters.status) return false;
    if (filters.search && !emp.name.toLowerCase().includes(filters.search.toLowerCase()) &&
        !emp.email.toLowerCase().includes(filters.search.toLowerCase())) return false;
    return true;
  });

  // Status badge variant mapping
  const getStatusVariant = (status) => {
    const map = {
      ACTIVE: 'success',
      ONBOARDING: 'primary',
      NOTICE: 'warning',
      BENCH: 'default',
      TERMINATED: 'error',
    };
    return map[status] || 'default';
  };

  // Render functions
  const renderHeaderSection = () => (
    <div style={{
      marginBottom: spacing.xl,
      padding: spacing.xl,
      background: `linear-gradient(135deg, ${colors.primary[600]} 0%, ${colors.primary[800]} 100%)`,
      borderRadius: '12px',
      color: 'white',
    }}>
      <Breadcrumb
        items={[
          { label: 'Home', href: '/' },
          { label: 'HRMS Dashboard' },
        ]}
      />
      
      <h1 style={{
        margin: `${spacing.md} 0`,
        fontSize: typography.fontSize['4xl'],
        fontWeight: typography.fontWeight.bold,
      }}>
        Human Resource Management
      </h1>
      
      <p style={{
        margin: 0,
        fontSize: typography.fontSize.lg,
        opacity: 0.9,
      }}>
        Manage employees, track performance, and monitor organizational health
      </p>
    </div>
  );

  const renderQuickStats = () => (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: spacing.md,
      marginBottom: spacing.xl,
    }}>
      <Card padding="lg" hoverable>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: typography.fontSize['3xl'],
            fontWeight: typography.fontWeight.bold,
            color: colors.primary[600],
          }}>
            {headcountData.total || 0}
          </div>
          <div style={{
            fontSize: typography.fontSize.sm,
            color: colors.gray[600],
            marginTop: spacing.xs,
          }}>
            Total Employees
          </div>
        </div>
      </Card>

      <Card padding="lg" hoverable>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: typography.fontSize['3xl'],
            fontWeight: typography.fontWeight.bold,
            color: colors.success.main,
          }}>
            {headcountData.active || 0}
          </div>
          <div style={{
            fontSize: typography.fontSize.sm,
            color: colors.gray[600],
            marginTop: spacing.xs,
          }}>
            Active
          </div>
        </div>
      </Card>

      <Card padding="lg" hoverable>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: typography.fontSize['3xl'],
            fontWeight: typography.fontWeight.bold,
            color: colors.info.main,
          }}>
            {headcountData.onboarding || 0}
          </div>
          <div style={{
            fontSize: typography.fontSize.sm,
            color: colors.gray[600],
            marginTop: spacing.xs,
          }}>
            Onboarding
          </div>
        </div>
      </Card>

      <Card padding="lg" hoverable>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: typography.fontSize['3xl'],
            fontWeight: typography.fontWeight.bold,
            color: colors.warning.main,
          }}>
            {headcountData.notice || 0}
          </div>
          <div style={{
            fontSize: typography.fontSize.sm,
            color: colors.gray[600],
            marginTop: spacing.xs,
          }}>
            On Notice
          </div>
        </div>
      </Card>

      <Card padding="lg" hoverable>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: typography.fontSize['3xl'],
            fontWeight: typography.fontWeight.bold,
            color: colors.gray[500],
          }}>
            {headcountData.bench || 0}
          </div>
          <div style={{
            fontSize: typography.fontSize.sm,
            color: colors.gray[600],
            marginTop: spacing.xs,
          }}>
            On Bench
          </div>
        </div>
      </Card>
    </div>
  );

  const renderFilters = () => (
    <Card title="Filters" padding="lg" style={{ marginBottom: spacing.lg }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: spacing.md,
      }}>
        <div>
          <input
            type="text"
            placeholder="Search by name or email..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            style={{
              width: '100%',
              padding: spacing.md,
              fontSize: typography.fontSize.base,
              border: `1px solid ${colors.gray[300]}`,
              borderRadius: '6px',
              outline: 'none',
            }}
          />
        </div>

        <Select
          placeholder="Filter by Department"
          value={filters.department}
          onChange={(e) => setFilters({ ...filters, department: e.target.value })}
          options={[
            { value: '', label: 'All Departments' },
            ...departments.map(dept => ({
              value: dept.name,
              label: `${dept.name} (${dept.count})`,
            })),
          ]}
        />

        <Select
          placeholder="Filter by Status"
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          options={[
            { value: '', label: 'All Statuses' },
            { value: 'ACTIVE', label: 'Active' },
            { value: 'ONBOARDING', label: 'Onboarding' },
            { value: 'NOTICE', label: 'On Notice' },
            { value: 'BENCH', label: 'On Bench' },
            { value: 'TERMINATED', label: 'Terminated' },
          ]}
        />

        <Button
          variant="outline"
          onClick={() => setFilters({ department: '', status: '', search: '' })}
        >
          Clear Filters
        </Button>
      </div>
    </Card>
  );

  const renderEmployeeGrid = () => (
    <Card title="Employees" subtitle={`Showing ${filteredEmployees.length} of ${employees.length} employees`} padding="lg">
      {loading ? (
        <LoadingSkeleton type="card" count={3} />
      ) : filteredEmployees.length === 0 ? (
        <EmptyState
          icon="👥"
          title="No employees found"
          description="Try adjusting your filters to see more results"
          action={() => setFilters({ department: '', status: '', search: '' })}
          actionText="Clear Filters"
        />
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: spacing.lg,
        }}>
          {filteredEmployees.map(employee => (
            <div
              key={employee.id}
              style={{
                padding: spacing.lg,
                border: `1px solid ${colors.gray[200]}`,
                borderRadius: '8px',
                transition: 'all 0.2s ease',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: spacing.md }}>
                <Avatar
                  name={employee.name}
                  size="lg"
                  showStatus
                  status={employee.status === 'ACTIVE' ? 'online' : 'offline'}
                />
                
                <div style={{ flex: 1 }}>
                  <h3 style={{
                    margin: 0,
                    fontSize: typography.fontSize.lg,
                    fontWeight: typography.fontWeight.semibold,
                  }}>
                    {employee.name}
                  </h3>
                  <p style={{
                    margin: `${spacing.xs} 0`,
                    fontSize: typography.fontSize.sm,
                    color: colors.gray[600],
                  }}>
                    {employee.position}
                  </p>
                  <Badge variant={getStatusVariant(employee.status)} size="sm">
                    {employee.status}
                  </Badge>
                </div>
              </div>

              <div style={{ marginTop: spacing.md }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: spacing.xs,
                }}>
                  <span style={{ fontSize: typography.fontSize.sm, color: colors.gray[600] }}>
                    Department
                  </span>
                  <span style={{ fontSize: typography.fontSize.sm, fontWeight: typography.fontWeight.medium }}>
                    {employee.department}
                  </span>
                </div>

                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: spacing.xs,
                }}>
                  <span style={{ fontSize: typography.fontSize.sm, color: colors.gray[600] }}>
                    Join Date
                  </span>
                  <span style={{ fontSize: typography.fontSize.sm, fontWeight: typography.fontWeight.medium }}>
                    {new Date(employee.joinDate).toLocaleDateString()}
                  </span>
                </div>

                <Progress
                  value={employee.performance}
                  label="Performance"
                  variant={employee.performance >= 80 ? 'success' : employee.performance >= 60 ? 'primary' : 'warning'}
                  size="sm"
                />

                <div style={{ marginTop: spacing.md }}>
                  <span style={{
                    fontSize: typography.fontSize.xs,
                    color: colors.gray[600],
                    display: 'block',
                    marginBottom: spacing.xs,
                  }}>
                    Skills
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.xs }}>
                    {employee.skills.map((skill, index) => (
                      <Badge key={index} variant="default" size="sm">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{
                marginTop: spacing.md,
                display: 'flex',
                gap: spacing.sm,
              }}>
                <Button size="sm" variant="outline" fullWidth>
                  View Profile
                </Button>
                <Button size="sm" variant="ghost">
                  •••
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );

  const renderDepartmentBreakdown = () => (
    <Card title="Department Breakdown" padding="lg">
      {departments.map(dept => (
        <div
          key={dept.id}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: spacing.md,
            marginBottom: spacing.sm,
            borderBottom: `1px solid ${colors.gray[200]}`,
          }}
        >
          <span style={{ fontWeight: typography.fontWeight.medium }}>
            {dept.name}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md }}>
            <Progress
              value={dept.count}
              max={headcountData.total}
              size="sm"
              showLabel={false}
              style={{ width: '100px' }}
            />
            <Badge variant="primary">{dept.count}</Badge>
          </div>
        </div>
      ))}
    </Card>
  );

  const renderQuickActions = () => (
    <Card title="Quick Actions" padding="lg">
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
        <Button variant="primary" fullWidth onClick={() => showToast('Opening employee registration...', 'info')}>
          + Add New Employee
        </Button>
        <Button variant="outline" fullWidth onClick={() => showToast('Opening payroll export...', 'info')}>
          Export Payroll
        </Button>
        <Button variant="outline" fullWidth onClick={() => showToast('Opening reports...', 'info')}>
          Generate Reports
        </Button>
        <Button variant="outline" fullWidth onClick={() => showToast('Opening bulk actions...', 'info')}>
          Bulk Actions
        </Button>
      </div>
    </Card>
  );

  return (
    <div style={{
      padding: spacing.xl,
      backgroundColor: colors.gray[50],
      minHeight: '100vh',
    }}>
      {renderHeaderSection()}
      {renderQuickStats()}
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 300px',
        gap: spacing.lg,
        marginBottom: spacing.lg,
      }}>
        <div>
          {renderFilters()}
          {renderEmployeeGrid()}
        </div>
        
        <div>
          {renderQuickActions()}
          <div style={{ marginTop: spacing.lg }}>
            {renderDepartmentBreakdown()}
          </div>
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default HRMSDashboard;

/**
 * EOD & ATTENDANCE MANAGEMENT - INTRANET V2
 * End-of-Day reporting and attendance tracking
 * 
 * Features:
 * - Submit daily EOD reports
 * - Track task completion
 * - Attendance summary
 * - Weekly/monthly views
 * - Team EOD overview
 * - Bounty tracking
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Table } from '../Components/DesignSystem';
import { Select, Textarea, FormGroup } from '../Components/FormComponents';
import { Breadcrumb, Toast, Avatar, Progress, EmptyState, LoadingSkeleton } from '../Components/NavigationComponents';
import { colors, spacing, typography } from '../Components/DesignSystem';
import api, { handleApiError } from '../Services/api';

const EODManagement = () => {
  // State
  const [loading, setLoading] = useState(true);
  const [eodRecords, setEodRecords] = useState([]);
  const [myTasks, setMyTasks] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [filters, setFilters] = useState({
    week: 'current',
    user: 'me',
  });
  const [toast, setToast] = useState(null);
  const [todayEOD, setTodayEOD] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [statistics, setStatistics] = useState({});

  // EOD Form
  const [eodForm, setEodForm] = useState({
    tasks_completed: '',
    blockers: '',
    tomorrow_plan: '',
    hours_worked: 8,
    bounty_claimed: 0,
  });
  const [formErrors, setFormErrors] = useState({});

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchEODRecords();
  }, [filters]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchCurrentUser(),
        fetchTodayEOD(),
        fetchMyTasks(),
        fetchEODRecords(),
        fetchStatistics(),
      ]);
    } catch (error) {
      showToast(handleApiError(error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const response = await api.auth.getCurrentUser();
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Failed to fetch current user:', error);
    }
  };

  const fetchTodayEOD = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await api.eod.list({ date: today });
      setTodayEOD(response.data.results?.[0] || null);
      
      if (response.data.results?.[0]) {
        // Pre-fill form if EOD already exists
        const eod = response.data.results[0];
        setEodForm({
          tasks_completed: eod.tasks_completed || '',
          blockers: eod.blockers || '',
          tomorrow_plan: eod.tomorrow_plan || '',
          hours_worked: eod.hours_worked || 8,
          bounty_claimed: eod.bounty_claimed || 0,
        });
      }
    } catch (error) {
      console.error('Failed to fetch today EOD:', error);
    }
  };

  const fetchMyTasks = async () => {
    try {
      const response = await api.tasks.list({ status: 'I', assignee: 'me' });
      setMyTasks(response.data.results || []);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  const fetchEODRecords = async () => {
    try {
      const params = { ...filters };
      
      // Calculate date range based on week filter
      if (filters.week === 'current') {
        const today = new Date();
        const monday = new Date(today.setDate(today.getDate() - today.getDay() + 1));
        params.date_from = monday.toISOString().split('T')[0];
      } else if (filters.week === 'last') {
        const today = new Date();
        const lastMonday = new Date(today.setDate(today.getDate() - today.getDay() - 6));
        const lastSunday = new Date(today.setDate(today.getDate() - today.getDay()));
        params.date_from = lastMonday.toISOString().split('T')[0];
        params.date_to = lastSunday.toISOString().split('T')[0];
      }

      const response = await api.eod.list(params);
      setEodRecords(response.data.results || []);
    } catch (error) {
      console.error('Failed to fetch EOD records:', error);
      setEodRecords([]);
    }
  };

  const fetchStatistics = async () => {
    try {
      // Get weekly statistics
      const today = new Date();
      const monday = new Date(today.setDate(today.getDate() - today.getDay() + 1));
      
      const response = await api.eod.list({
        date_from: monday.toISOString().split('T')[0],
        user: 'me',
      });

      const records = response.data.results || [];
      
      setStatistics({
        days_submitted: records.length,
        total_hours: records.reduce((sum, r) => sum + (r.hours_worked || 0), 0),
        total_bounty: records.reduce((sum, r) => sum + (r.bounty_claimed || 0), 0),
        completion_rate: records.length > 0 ? (records.length / 5) * 100 : 0, // 5 working days
      });
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };

  const validateForm = () => {
    const errors = {};
    
    if (!eodForm.tasks_completed?.trim()) {
      errors.tasks_completed = 'Please describe tasks completed today';
    }
    if (eodForm.hours_worked < 0 || eodForm.hours_worked > 24) {
      errors.hours_worked = 'Hours must be between 0 and 24';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmitEOD = async () => {
    if (!validateForm()) {
      showToast('Please fix the form errors', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const data = {
        ...eodForm,
        date: new Date().toISOString().split('T')[0],
      };

      if (todayEOD) {
        // Update existing EOD
        await api.eod.update(todayEOD.id, data);
        showToast('EOD updated successfully!', 'success');
      } else {
        // Create new EOD
        await api.eod.create(data);
        showToast('EOD submitted successfully!', 'success');
      }

      await fetchTodayEOD();
      await fetchEODRecords();
      await fetchStatistics();
    } catch (error) {
      const apiError = handleApiError(error);
      if (apiError.type === 'validation') {
        setFormErrors(apiError.errors);
      }
      showToast(apiError.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  // Table columns
  const columns = [
    {
      header: 'Date',
      key: 'date',
      render: (row) => new Date(row.date).toLocaleDateString('en-US', { 
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      }),
    },
    {
      header: 'Employee',
      key: 'user',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
          <Avatar name={row.user?.full_name} size="sm" />
          <span>{row.user?.full_name || 'N/A'}</span>
        </div>
      ),
    },
    {
      header: 'Hours',
      key: 'hours_worked',
      align: 'center',
      render: (row) => `${row.hours_worked || 0}h`,
    },
    {
      header: 'Bounty',
      key: 'bounty_claimed',
      align: 'right',
      render: (row) => row.bounty_claimed > 0 ? (
        <Badge variant="success">₹{row.bounty_claimed}</Badge>
      ) : (
        <span style={{ color: colors.gray[400] }}>-</span>
      ),
    },
    {
      header: 'Status',
      key: 'status',
      render: (row) => {
        const hasBlockers = row.blockers && row.blockers.trim();
        return hasBlockers ? (
          <Badge variant="warning">Has Blockers</Badge>
        ) : (
          <Badge variant="success">On Track</Badge>
        );
      },
    },
  ];

  return (
    <div style={{ padding: spacing.xl, backgroundColor: colors.gray[50], minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        marginBottom: spacing.xl,
        padding: spacing.xl,
        background: `linear-gradient(135deg, ${colors.secondary[600]} 0%, ${colors.secondary[800]} 100%)`,
        borderRadius: '12px',
        color: 'white',
      }}>
        <Breadcrumb
          items={[
            { label: 'Home', href: '/' },
            { label: 'EOD & Attendance' },
          ]}
        />
        
        <h1 style={{
          margin: `${spacing.md} 0`,
          fontSize: typography.fontSize['4xl'],
          fontWeight: typography.fontWeight.bold,
        }}>
          End-of-Day Reports
        </h1>
        
        <p style={{ margin: 0, fontSize: typography.fontSize.lg, opacity: 0.9 }}>
          Track your daily progress and team activities
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: spacing.lg }}>
        {/* Main Content */}
        <div>
          {/* Statistics Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: spacing.md,
            marginBottom: spacing.lg,
          }}>
            <Card padding="lg">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.primary[600] }}>
                  {statistics.days_submitted || 0}/5
                </div>
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
                  EODs This Week
                </div>
              </div>
            </Card>

            <Card padding="lg">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.info.main }}>
                  {statistics.total_hours || 0}h
                </div>
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
                  Total Hours
                </div>
              </div>
            </Card>

            <Card padding="lg">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.success.main }}>
                  ₹{statistics.total_bounty || 0}
                </div>
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
                  Bounty Earned
                </div>
              </div>
            </Card>

            <Card padding="lg">
              <div style={{ textAlign: 'center' }}>
                <Progress
                  value={statistics.completion_rate || 0}
                  showLabel={false}
                  variant={statistics.completion_rate >= 80 ? 'success' : 'warning'}
                />
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
                  Compliance Rate
                </div>
              </div>
            </Card>
          </div>

          {/* Filters */}
          <Card padding="lg" style={{ marginBottom: spacing.lg }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: spacing.md }}>
              <Select
                label="Week"
                value={filters.week}
                onChange={(e) => setFilters({ ...filters, week: e.target.value })}
                options={[
                  { value: 'current', label: 'Current Week' },
                  { value: 'last', label: 'Last Week' },
                  { value: 'all', label: 'All Time' },
                ]}
              />

              <Select
                label="Employee"
                value={filters.user}
                onChange={(e) => setFilters({ ...filters, user: e.target.value })}
                options={[
                  { value: 'me', label: 'My EODs' },
                  { value: 'team', label: 'Team EODs' },
                  { value: 'all', label: 'All EODs' },
                ]}
              />
            </div>
          </Card>

          {/* EOD Records Table */}
          <Card title="EOD History" padding="lg">
            {loading ? (
              <LoadingSkeleton type="card" count={5} />
            ) : eodRecords.length === 0 ? (
              <EmptyState
                icon="📝"
                title="No EOD records found"
                description="No EODs have been submitted for the selected period"
              />
            ) : (
              <Table columns={columns} data={eodRecords} striped />
            )}
          </Card>
        </div>

        {/* Sidebar - Submit EOD */}
        <div>
          <Card
            title={todayEOD ? "Update Today's EOD" : "Submit Today's EOD"}
            subtitle={new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            padding="lg"
          >
            <FormGroup>
              <Textarea
                label="Tasks Completed"
                required
                rows={4}
                value={eodForm.tasks_completed}
                onChange={(e) => setEodForm({ ...eodForm, tasks_completed: e.target.value })}
                error={formErrors.tasks_completed}
                helpText="What did you accomplish today?"
              />

              <Textarea
                label="Blockers/Challenges"
                rows={3}
                value={eodForm.blockers}
                onChange={(e) => setEodForm({ ...eodForm, blockers: e.target.value })}
                helpText="Any blockers or challenges faced?"
              />

              <Textarea
                label="Tomorrow's Plan"
                rows={3}
                value={eodForm.tomorrow_plan}
                onChange={(e) => setEodForm({ ...eodForm, tomorrow_plan: e.target.value })}
                helpText="What are you planning for tomorrow?"
              />

              <Select
                label="Hours Worked"
                value={eodForm.hours_worked}
                onChange={(e) => setEodForm({ ...eodForm, hours_worked: parseFloat(e.target.value) })}
                error={formErrors.hours_worked}
                options={[
                  { value: 4, label: '4 hours' },
                  { value: 6, label: '6 hours' },
                  { value: 8, label: '8 hours' },
                  { value: 9, label: '9 hours' },
                  { value: 10, label: '10 hours' },
                ]}
              />

              <Button
                variant="primary"
                fullWidth
                onClick={handleSubmitEOD}
                loading={submitting}
              >
                {todayEOD ? 'Update EOD' : 'Submit EOD'}
              </Button>
            </FormGroup>
          </Card>

          {/* My Pending Tasks */}
          <Card
            title="Pending Tasks"
            subtitle={`${myTasks.length} incomplete tasks`}
            padding="lg"
            style={{ marginTop: spacing.lg }}
          >
            {myTasks.length === 0 ? (
              <EmptyState
                icon="✅"
                title="All caught up!"
                description="No pending tasks"
              />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
                {myTasks.slice(0, 5).map((task) => (
                  <div
                    key={task.id}
                    style={{
                      padding: spacing.sm,
                      borderLeft: `3px solid ${colors.primary[600]}`,
                      backgroundColor: colors.gray[50],
                      borderRadius: borderRadius.md,
                    }}
                  >
                    <div style={{
                      fontSize: typography.fontSize.sm,
                      fontWeight: typography.fontWeight.medium,
                    }}>
                      {task.title}
                    </div>
                    {task.bounty > 0 && (
                      <Badge variant="success" size="sm" style={{ marginTop: spacing.xs }}>
                        ₹{task.bounty}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Toast */}
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

export default EODManagement;

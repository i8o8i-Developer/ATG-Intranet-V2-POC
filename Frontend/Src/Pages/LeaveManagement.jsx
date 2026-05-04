/**
 * LEAVE MANAGEMENT - INTRANET V2
 * Complete leave application, approval, and tracking system
 * 
 * Features:
 * - Apply for leave
 * - Leave calendar view
 * - Leave balance tracking
 * - Approve/reject leave requests
 * - Leave history
 * - Team leave overview
 * - Multiple leave types
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Table, Modal } from '../Components/DesignSystem';
import { Select, DatePicker, Textarea, FormGroup, Radio } from '../Components/FormComponents';
import { Breadcrumb, Toast, Avatar, EmptyState, LoadingSkeleton, Pagination } from '../Components/NavigationComponents';
import { colors, spacing, typography } from '../Components/DesignSystem';
import api, { handleApiError } from '../Services/api';

const LeaveManagement = () => {
  // State
  const [loading, setLoading] = useState(true);
  const [leaves, setLeaves] = useState([]);
  const [leaveBalances, setLeaveBalances] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    leave_type: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
  });
  const [toast, setToast] = useState(null);
  const [applyModal, setApplyModal] = useState(false);
  const [detailModal, setDetailModal] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, totalPages: 1 });
  
  // Form state
  const [leaveForm, setLeaveForm] = useState({
    leave_type: '',
    date_from: '',
    date_to: '',
    reason: '',
    half_day: false,
    half_day_type: 'FIRST_HALF',
  });
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchLeaves();
  }, [filters, pagination.page]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchCurrentUser(),
        fetchLeaveBalances(),
        fetchLeaveTypes(),
        fetchLeaves(),
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

  const fetchLeaveBalances = async () => {
    try {
      const response = await api.leaveBalances.list();
      setLeaveBalances(response.data.results || []);
    } catch (error) {
      console.error('Failed to fetch leave balances:', error);
    }
  };

  const fetchLeaveTypes = async () => {
    try {
      const response = await api.leavePolicies.list();
      setLeaveTypes(response.data.results || []);
    } catch (error) {
      console.error('Failed to fetch leave types:', error);
    }
  };

  const fetchLeaves = async () => {
    try {
      const params = { ...filters, page: pagination.page };
      const response = await api.leaves.list(params);
      
      setLeaves(response.data.results || []);
      setPagination({
        page: response.data.current_page || 1,
        totalPages: response.data.total_pages || 1,
      });
    } catch (error) {
      console.error('Failed to fetch leaves:', error);
      setLeaves([]);
    }
  };

  const validateForm = () => {
    const errors = {};
    
    if (!leaveForm.leave_type) errors.leave_type = 'Please select leave type';
    if (!leaveForm.date_from) errors.date_from = 'Start date is required';
    if (!leaveForm.date_to) errors.date_to = 'End date is required';
    if (new Date(leaveForm.date_from) > new Date(leaveForm.date_to)) {
      errors.date_to = 'End date must be after start date';
    }
    if (!leaveForm.reason?.trim()) errors.reason = 'Reason is required';
    if (leaveForm.reason?.length > 500) errors.reason = 'Reason must be less than 500 characters';

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleApplyLeave = async () => {
    if (!validateForm()) {
      showToast('Please fix the form errors', 'error');
      return;
    }

    setSubmitting(true);
    try {
      await api.leaves.create(leaveForm);
      showToast('Leave application submitted successfully!', 'success');
      setApplyModal(false);
      resetForm();
      await fetchLeaves();
      await fetchLeaveBalances();
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

  const handleApproveLeave = async (leaveId) => {
    try {
      await api.leaves.approve(leaveId, { approved: true });
      showToast('Leave approved successfully!', 'success');
      await fetchLeaves();
      setDetailModal(false);
    } catch (error) {
      showToast(handleApiError(error).message, 'error');
    }
  };

  const handleRejectLeave = async (leaveId) => {
    try {
      await api.leaves.reject(leaveId, { reason: 'Rejected by manager' });
      showToast('Leave rejected', 'warning');
      await fetchLeaves();
      setDetailModal(false);
    } catch (error) {
      showToast(handleApiError(error).message, 'error');
    }
  };

  const handleCancelLeave = async (leaveId) => {
    try {
      await api.leaves.cancel(leaveId);
      showToast('Leave cancelled successfully', 'info');
      await fetchLeaves();
      await fetchLeaveBalances();
    } catch (error) {
      showToast(handleApiError(error).message, 'error');
    }
  };

  const resetForm = () => {
    setLeaveForm({
      leave_type: '',
      date_from: '',
      date_to: '',
      reason: '',
      half_day: false,
      half_day_type: 'FIRST_HALF',
    });
    setFormErrors({});
  };

  const calculateLeaveDays = () => {
    if (!leaveForm.date_from || !leaveForm.date_to) return 0;
    
    const start = new Date(leaveForm.date_from);
    const end = new Date(leaveForm.date_to);
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
    
    return leaveForm.half_day ? 0.5 : days;
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      P: { variant: 'warning', label: 'Pending' },
      A: { variant: 'success', label: 'Approved' },
      R: { variant: 'error', label: 'Rejected' },
      C: { variant: 'default', label: 'Cancelled' },
    };
    const config = statusMap[status] || { variant: 'default', label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  // Table columns
  const columns = [
    {
      header: 'Employee',
      key: 'user',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
          <Avatar name={row.user?.full_name} size="sm" />
          <div>
            <div style={{ fontWeight: typography.fontWeight.medium }}>
              {row.user?.full_name || 'N/A'}
            </div>
            <div style={{ fontSize: typography.fontSize.xs, color: colors.gray[600] }}>
              {row.user?.department?.name}
            </div>
          </div>
        </div>
      ),
    },
    {
      header: 'Leave Type',
      key: 'leave_type',
      render: (row) => row.leave_type?.name || 'N/A',
    },
    {
      header: 'From',
      key: 'date_from',
      render: (row) => new Date(row.date_from).toLocaleDateString(),
    },
    {
      header: 'To',
      key: 'date_to',
      render: (row) => new Date(row.date_to).toLocaleDateString(),
    },
    {
      header: 'Days',
      key: 'total_days',
      align: 'center',
      render: (row) => row.total_days || 1,
    },
    {
      header: 'Status',
      key: 'status',
      render: (row) => getStatusBadge(row.status),
    },
    {
      header: 'Actions',
      key: 'actions',
      render: (row) => (
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            setSelectedLeave(row);
            setDetailModal(true);
          }}
        >
          View
        </Button>
      ),
    },
  ];

  return (
    <div style={{ padding: spacing.xl, backgroundColor: colors.gray[50], minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        marginBottom: spacing.xl,
        padding: spacing.xl,
        background: `linear-gradient(135deg, ${colors.info.main} 0%, ${colors.info.dark} 100%)`,
        borderRadius: '12px',
        color: 'white',
      }}>
        <Breadcrumb
          items={[
            { label: 'Home', href: '/' },
            { label: 'Leave Management' },
          ]}
        />
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{
              margin: `${spacing.md} 0`,
              fontSize: typography.fontSize['4xl'],
              fontWeight: typography.fontWeight.bold,
            }}>
              Leave Management
            </h1>
            
            <p style={{ margin: 0, fontSize: typography.fontSize.lg, opacity: 0.9 }}>
              Apply for leave, track balance, and manage team leaves
            </p>
          </div>
          
          <Button
            variant="secondary"
            size="lg"
            onClick={() => setApplyModal(true)}
          >
            + Apply for Leave
          </Button>
        </div>
      </div>

      {/* Leave Balance Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: spacing.md,
        marginBottom: spacing.lg,
      }}>
        {leaveBalances.map((balance) => (
          <Card key={balance.id} padding="lg" hoverable>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: typography.fontSize.sm,
                color: colors.gray[600],
                marginBottom: spacing.xs,
              }}>
                {balance.leave_type?.name}
              </div>
              <div style={{
                fontSize: typography.fontSize['3xl'],
                fontWeight: typography.fontWeight.bold,
                color: colors.primary[600],
              }}>
                {balance.available_balance || 0}
              </div>
              <div style={{
                fontSize: typography.fontSize.xs,
                color: colors.gray[500],
                marginTop: spacing.xs,
              }}>
                of {balance.total_balance || 0} days available
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card padding="lg" style={{ marginBottom: spacing.lg }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: spacing.md,
        }}>
          <Select
            label="Status"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            options={[
              { value: '', label: 'All Statuses' },
              { value: 'P', label: 'Pending' },
              { value: 'A', label: 'Approved' },
              { value: 'R', label: 'Rejected' },
            ]}
          />

          <Select
            label="Leave Type"
            value={filters.leave_type}
            onChange={(e) => setFilters({ ...filters, leave_type: e.target.value })}
            options={[
              { value: '', label: 'All Types' },
              ...leaveTypes.map(t => ({ value: t.id, label: t.name })),
            ]}
          />

          <Select
            label="Month"
            value={filters.month}
            onChange={(e) => setFilters({ ...filters, month: parseInt(e.target.value) })}
            options={Array.from({ length: 12 }, (_, i) => ({
              value: i + 1,
              label: new Date(2000, i, 1).toLocaleString('default', { month: 'long' }),
            }))}
          />

          <Select
            label="Year"
            value={filters.year}
            onChange={(e) => setFilters({ ...filters, year: parseInt(e.target.value) })}
            options={Array.from({ length: 3 }, (_, i) => {
              const year = new Date().getFullYear() - i;
              return { value: year, label: year.toString() };
            })}
          />
        </div>
      </Card>

      {/* Leave Table */}
      <Card title="Leave Requests" padding="lg">
        {loading ? (
          <LoadingSkeleton type="card" count={5} />
        ) : leaves.length === 0 ? (
          <EmptyState
            icon="🏖️"
            title="No leave requests found"
            description="No leaves found for the selected filters"
            action={() => setApplyModal(true)}
            actionText="Apply for Leave"
          />
        ) : (
          <>
            <Table columns={columns} data={leaves} striped />
            {pagination.totalPages > 1 && (
              <Pagination
                currentPage={pagination.page}
                totalPages={pagination.totalPages}
                onPageChange={(page) => setPagination({ ...pagination, page })}
              />
            )}
          </>
        )}
      </Card>

      {/* Apply Leave Modal */}
      {applyModal && (
        <Modal
          isOpen={applyModal}
          onClose={() => {
            setApplyModal(false);
            resetForm();
          }}
          title="Apply for Leave"
          size="md"
        >
          <FormGroup title="Leave Details">
            <Select
              label="Leave Type"
              required
              value={leaveForm.leave_type}
              onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}
              error={formErrors.leave_type}
              options={leaveTypes.map(t => ({ value: t.id, label: t.name }))}
            />

            <DatePicker
              label="Start Date"
              required
              value={leaveForm.date_from}
              onChange={(e) => setLeaveForm({ ...leaveForm, date_from: e.target.value })}
              error={formErrors.date_from}
              min={new Date().toISOString().split('T')[0]}
            />

            <DatePicker
              label="End Date"
              required
              value={leaveForm.date_to}
              onChange={(e) => setLeaveForm({ ...leaveForm, date_to: e.target.value })}
              error={formErrors.date_to}
              min={leaveForm.date_from || new Date().toISOString().split('T')[0]}
            />

            <Textarea
              label="Reason"
              required
              rows={4}
              maxLength={500}
              showCount
              value={leaveForm.reason}
              onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
              error={formErrors.reason}
              helpText="Please provide a brief reason for your leave"
            />

            <div>
              <p style={{ marginBottom: spacing.sm, fontWeight: typography.fontWeight.medium }}>
                Total Days: <span style={{ color: colors.primary[600] }}>{calculateLeaveDays()}</span>
              </p>
            </div>
          </FormGroup>

          <div style={{ display: 'flex', gap: spacing.md, justifyContent: 'flex-end', marginTop: spacing.lg }}>
            <Button
              variant="outline"
              onClick={() => {
                setApplyModal(false);
                resetForm();
              }}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleApplyLeave}
              loading={submitting}
            >
              Submit Application
            </Button>
          </div>
        </Modal>
      )}

      {/* Leave Detail Modal */}
      {detailModal && selectedLeave && (
        <Modal
          isOpen={detailModal}
          onClose={() => setDetailModal(false)}
          title="Leave Details"
          size="md"
        >
          <div style={{ marginBottom: spacing.lg }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md, marginBottom: spacing.lg }}>
              <Avatar name={selectedLeave.user?.full_name} size="lg" />
              <div>
                <h3 style={{ margin: 0, fontWeight: typography.fontWeight.semibold }}>
                  {selectedLeave.user?.full_name}
                </h3>
                <p style={{ margin: 0, fontSize: typography.fontSize.sm, color: colors.gray[600] }}>
                  {selectedLeave.user?.department?.name}
                </p>
              </div>
            </div>

            <div style={{ display: 'grid', gap: spacing.md }}>
              <div>
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600] }}>Leave Type</div>
                <div style={{ fontWeight: typography.fontWeight.medium }}>{selectedLeave.leave_type?.name}</div>
              </div>

              <div>
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600] }}>Duration</div>
                <div style={{ fontWeight: typography.fontWeight.medium }}>
                  {new Date(selectedLeave.date_from).toLocaleDateString()} - {new Date(selectedLeave.date_to).toLocaleDateString()}
                  ({selectedLeave.total_days} days)
                </div>
              </div>

              <div>
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600] }}>Reason</div>
                <div>{selectedLeave.reason}</div>
              </div>

              <div>
                <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600] }}>Status</div>
                <div>{getStatusBadge(selectedLeave.status)}</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: spacing.md, justifyContent: 'flex-end' }}>
            {selectedLeave.status === 'P' && currentUser?.is_manager && (
              <>
                <Button variant="outline" onClick={() => handleRejectLeave(selectedLeave.id)}>
                  Reject
                </Button>
                <Button variant="success" onClick={() => handleApproveLeave(selectedLeave.id)}>
                  Approve
                </Button>
              </>
            )}
            {selectedLeave.status === 'P' && selectedLeave.user?.id === currentUser?.employee_id && (
              <Button variant="danger" onClick={() => handleCancelLeave(selectedLeave.id)}>
                Cancel Leave
              </Button>
            )}
            <Button variant="outline" onClick={() => setDetailModal(false)}>
              Close
            </Button>
          </div>
        </Modal>
      )}

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

export default LeaveManagement;

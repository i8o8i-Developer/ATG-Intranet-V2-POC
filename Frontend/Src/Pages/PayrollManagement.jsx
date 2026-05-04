/**
 * PAYROLL MANAGEMENT - INTRANET V2
 * Complete payroll processing and export system
 * 
 * Features:
 * - Monthly payroll overview
 * - Filter by department/month/year
 * - Export to Excel (async)
 * - Payment status tracking
 * - Employee payment details
 * - Bulk payment approval
 * - Payment history
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Table, Modal } from '../Components/DesignSystem';
import { Select, DatePicker, FormGroup } from '../Components/FormComponents';
import { Breadcrumb, Toast, Progress, EmptyState, LoadingSkeleton } from '../Components/NavigationComponents';
import { colors, spacing, typography } from '../Components/DesignSystem';
import api, { handleApiError, downloadFile } from '../Services/api';

const PayrollManagement = () => {
  // State
  const [loading, setLoading] = useState(true);
  const [payments, setPayments] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [filters, setFilters] = useState({
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
    department: '',
    status: '',
    pay_type: '',
  });
  const [toast, setToast] = useState(null);
  const [exportModal, setExportModal] = useState(false);
  const [exportProgress, setExportProgress] = useState(null);
  const [exportTaskId, setExportTaskId] = useState(null);
  const [selectedPayments, setSelectedPayments] = useState([]);
  const [summary, setSummary] = useState({});

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchPayments();
  }, [filters]);

  // Poll export status
  useEffect(() => {
    if (exportTaskId) {
      const interval = setInterval(checkExportStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [exportTaskId]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchDepartments(),
        fetchPayments(),
      ]);
    } catch (error) {
      showToast(handleApiError(error).message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await api.departments.list();
      setDepartments(response.data.results || []);
    } catch (error) {
      console.error('Failed to fetch departments:', error);
    }
  };

  const fetchPayments = async () => {
    try {
      const response = await api.payments.list(filters);
      const data = response.data;
      
      setPayments(data.results || []);
      setSummary({
        total_employees: data.total_employees || 0,
        total_normal_pay: data.total_normal_pay || 0,
        total_bonus: data.total_bonus || 0,
        total_bounty: data.total_bounty || 0,
        total_deduction: data.total_deduction || 0,
        total_net_pay: data.total_net_pay || 0,
      });
    } catch (error) {
      console.error('Failed to fetch payments:', error);
      setPayments([]);
    }
  };

  const handleExport = async () => {
    try {
      setExportProgress({ status: 'Starting export...', percent: 0 });
      
      const response = await api.payroll.exportAsync({
        report_month: filters.month,
        report_year: filters.year,
        pay_type: filters.pay_type,
      });

      const taskId = response.data.task_id;
      setExportTaskId(taskId);
    } catch (error) {
      showToast(handleApiError(error).message, 'error');
      setExportProgress(null);
    }
  };

  const checkExportStatus = async () => {
    if (!exportTaskId) return;

    try {
      const response = await api.payroll.exportStatus(exportTaskId);
      const data = response.data;

      if (data.state === 'SUCCESS') {
        setExportProgress({ status: 'Download ready!', percent: 100 });
        setExportTaskId(null);
        
        // Download file
        const fileResponse = await api.payroll.download(data.result.file_id);
        downloadFile(fileResponse.data, data.result.filename);
        
        showToast('Payroll exported successfully!', 'success');
        setExportModal(false);
        setExportProgress(null);
      } else if (data.state === 'FAILURE') {
        setExportProgress(null);
        setExportTaskId(null);
        showToast('Export failed. Please try again.', 'error');
      } else if (data.state === 'PROGRESS') {
        setExportProgress({
          status: data.status || 'Processing...',
          percent: data.progress || 50,
        });
      }
    } catch (error) {
      console.error('Failed to check export status:', error);
    }
  };

  const handleSyncPayments = async () => {
    try {
      showToast('Syncing payment status...', 'info');
      await api.payments.requestSync({ month: filters.month, year: filters.year });
      await fetchPayments();
      showToast('Payment status synced successfully!', 'success');
    } catch (error) {
      showToast(handleApiError(error).message, 'error');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      PENDING: { variant: 'warning', label: 'Pending' },
      APPROVED: { variant: 'success', label: 'Approved' },
      PAID: { variant: 'success', label: 'Paid' },
      FAILED: { variant: 'error', label: 'Failed' },
      PROCESSING: { variant: 'primary', label: 'Processing' },
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
      key: 'employee',
      render: (row) => (
        <div>
          <div style={{ fontWeight: typography.fontWeight.medium }}>
            {row.employee?.full_name || 'N/A'}
          </div>
          <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600] }}>
            {row.employee?.email}
          </div>
        </div>
      ),
    },
    {
      header: 'Department',
      key: 'department',
      render: (row) => row.employee?.department?.name || 'N/A',
    },
    {
      header: 'Base Pay',
      key: 'normal_pay',
      align: 'right',
      render: (row) => formatCurrency(row.normal_pay),
    },
    {
      header: 'Bonus',
      key: 'bonus',
      align: 'right',
      render: (row) => formatCurrency(row.bonus),
    },
    {
      header: 'Bounty',
      key: 'bounty',
      align: 'right',
      render: (row) => formatCurrency(row.bounty),
    },
    {
      header: 'Deduction',
      key: 'deduction',
      align: 'right',
      render: (row) => <span style={{ color: colors.error.main }}>{formatCurrency(row.deduction)}</span>,
    },
    {
      header: 'Net Pay',
      key: 'net_pay',
      align: 'right',
      render: (row) => (
        <span style={{ fontWeight: typography.fontWeight.semibold }}>
          {formatCurrency(row.net_pay)}
        </span>
      ),
    },
    {
      header: 'Status',
      key: 'status',
      render: (row) => getStatusBadge(row.payment_status),
    },
  ];

  return (
    <div style={{ padding: spacing.xl, backgroundColor: colors.gray[50], minHeight: '100vh' }}>
      {/* Header */}
      <div style={{
        marginBottom: spacing.xl,
        padding: spacing.xl,
        background: `linear-gradient(135deg, ${colors.success.main} 0%, ${colors.success.dark} 100%)`,
        borderRadius: '12px',
        color: 'white',
      }}>
        <Breadcrumb
          items={[
            { label: 'Home', href: '/' },
            { label: 'Finance' },
            { label: 'Payroll Management' },
          ]}
        />
        
        <h1 style={{
          margin: `${spacing.md} 0`,
          fontSize: typography.fontSize['4xl'],
          fontWeight: typography.fontWeight.bold,
        }}>
          Payroll Management
        </h1>
        
        <p style={{ margin: 0, fontSize: typography.fontSize.lg, opacity: 0.9 }}>
          Process payments, export reports, and track payment status
        </p>
      </div>

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: spacing.md,
        marginBottom: spacing.lg,
      }}>
        <Card padding="lg">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.gray[900] }}>
              {summary.total_employees}
            </div>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
              Employees
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.primary[600] }}>
              {formatCurrency(summary.total_normal_pay)}
            </div>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
              Base Pay
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.success.main }}>
              {formatCurrency(summary.total_bonus)}
            </div>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
              Bonus
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.info.main }}>
              {formatCurrency(summary.total_bounty)}
            </div>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
              Bounty
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.error.main }}>
              {formatCurrency(summary.total_deduction)}
            </div>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
              Deductions
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: typography.fontSize['2xl'], fontWeight: typography.fontWeight.bold, color: colors.success.dark }}>
              {formatCurrency(summary.total_net_pay)}
            </div>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.gray[600], marginTop: spacing.xs }}>
              Net Pay
            </div>
          </div>
        </Card>
      </div>

      {/* Filters and Actions */}
      <Card padding="lg" style={{ marginBottom: spacing.lg }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: spacing.lg }}>
          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: spacing.md }}>
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
              options={Array.from({ length: 5 }, (_, i) => {
                const year = new Date().getFullYear() - i;
                return { value: year, label: year.toString() };
              })}
            />

            <Select
              label="Department"
              value={filters.department}
              onChange={(e) => setFilters({ ...filters, department: e.target.value })}
              options={[
                { value: '', label: 'All Departments' },
                ...departments.map(d => ({ value: d.id, label: d.name })),
              ]}
            />

            <Select
              label="Pay Type"
              value={filters.pay_type}
              onChange={(e) => setFilters({ ...filters, pay_type: e.target.value })}
              options={[
                { value: '', label: 'All Types' },
                { value: 'FIXED', label: 'Fixed' },
                { value: 'PERFORMANCE', label: 'Performance' },
                { value: 'CONTRACT', label: 'Contract' },
              ]}
            />
          </div>

          <div style={{ display: 'flex', gap: spacing.sm, flexDirection: 'column' }}>
            <Button variant="primary" onClick={() => setExportModal(true)}>
              Export to Excel
            </Button>
            <Button variant="outline" onClick={handleSyncPayments}>
              Sync Payment Status
            </Button>
          </div>
        </div>
      </Card>

      {/* Payments Table */}
      <Card title={`Payroll for ${new Date(filters.year, filters.month - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}`} padding="lg">
        {loading ? (
          <LoadingSkeleton type="card" count={5} />
        ) : payments.length === 0 ? (
          <EmptyState
            icon="💰"
            title="No payment records found"
            description="No payments have been processed for the selected period"
          />
        ) : (
          <Table columns={columns} data={payments} striped />
        )}
      </Card>

      {/* Export Modal */}
      {exportModal && (
        <Modal
          isOpen={exportModal}
          onClose={() => {
            if (!exportTaskId) {
              setExportModal(false);
              setExportProgress(null);
            }
          }}
          title="Export Payroll"
          size="md"
        >
          {!exportProgress ? (
            <>
              <p style={{ marginBottom: spacing.lg }}>
                Export payroll data for <strong>{new Date(filters.year, filters.month - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}</strong>
              </p>
              <div style={{ display: 'flex', gap: spacing.md, justifyContent: 'flex-end' }}>
                <Button variant="outline" onClick={() => setExportModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={handleExport}>
                  Start Export
                </Button>
              </div>
            </>
          ) : (
            <div>
              <Progress
                value={exportProgress.percent}
                label={exportProgress.status}
                variant="primary"
              />
              <p style={{ textAlign: 'center', marginTop: spacing.md, color: colors.gray[600] }}>
                Please wait while we generate your report...
              </p>
            </div>
          )}
        </Modal>
      )}

      {/* Toast Notifications */}
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

export default PayrollManagement;

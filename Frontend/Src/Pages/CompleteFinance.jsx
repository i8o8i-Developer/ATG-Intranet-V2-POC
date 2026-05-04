import React, { useState, useEffect } from 'react';
import {
  DollarSign, TrendingUp, Download, Upload, CheckCircle, XCircle,
  Clock, AlertCircle, FileText, CreditCard, Users, Calendar,
  Filter, Search, Plus, Eye, Edit, Trash2, Send, RefreshCw,
  BarChart3, PieChart, Activity, ArrowUpRight, ArrowDownRight,
  Wallet, Building, User, Mail, Phone, MapPin, Hash, Percent,
  Receipt, Archive, Star, Flag, Tag, Zap, Target, Award
} from 'lucide-react';
import api from '../Services/api';

/**
 * COMPLETE FINANCE & PAYROLL SYSTEM
 * Combines all 11 missing finance views:
 * 
 * 1. ManagePayrollView - Main payroll dashboard
 * 2. FinanceDepartmentView - Finance overview
 * 3. NewFinanceDepartmentView - Enhanced finance
 * 4. PaymentsView - Payment management
 * 5. BanaoFinanceDepartmentView - Banao finance
 * 6. ExportPayrollAsyncAPIView - Async exports
 * 7. PayrollExportStatusAPIView - Export tracking
 * 8. DownloadPayrollFileView - File downloads
 * 9. newpaymentapprove - Payment approval (new)
 * 10. paymentapprove - Payment approval (old)
 * 11. Bankdetails - Bank details management
 */
export default function CompleteFinance() {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================

  const [activeTab, setActiveTab] = useState('overview'); // overview, payroll, payments, approvals, bank
  const [loading, setLoading] = useState(true);
  
  // Overview Data
  const [financeStats, setFinanceStats] = useState(null);
  const [monthlyMetrics, setMonthlyMetrics] = useState([]);
  
  // Payroll Data
  const [payrollRuns, setPayrollRuns] = useState([]);
  const [selectedPayroll, setSelectedPayroll] = useState(null);
  const [showCreatePayroll, setShowCreatePayroll] = useState(false);
  const [exportStatus, setExportStatus] = useState({});
  
  // Payment Data
  const [payments, setPayments] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  
  // Bank Details
  const [bankAccounts, setBankAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [showBankModal, setShowBankModal] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    department: '',
    status: '',
    minAmount: '',
    maxAmount: '',
    search: ''
  });

  // ============================================================================
  // DATA LOADING
  // ============================================================================

  useEffect(() => {
    loadAllFinanceData();
  }, [activeTab]);

  const loadAllFinanceData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'overview':
          await Promise.all([
            loadFinanceStats(),
            loadMonthlyMetrics()
          ]);
          break;
        case 'payroll':
          await loadPayrollRuns();
          break;
        case 'payments':
          await Promise.all([
            loadPayments(),
            loadPendingApprovals()
          ]);
          break;
        case 'approvals':
          await loadPendingApprovals();
          break;
        case 'bank':
          await loadBankAccounts();
          break;
      }
    } catch (error) {
      console.error('Error loading finance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFinanceStats = async () => {
    try {
      const response = await api.finance.stats();
      setFinanceStats(response.data);
    } catch (error) {
      console.error('Error loading finance stats:', error);
    }
  };

  const loadMonthlyMetrics = async () => {
    try {
      const response = await api.finance.monthlyMetrics({ months: 6 });
      setMonthlyMetrics(response.data);
    } catch (error) {
      console.error('Error loading monthly metrics:', error);
    }
  };

  const loadPayrollRuns = async () => {
    try {
      const response = await api.payroll.list(filters);
      setPayrollRuns(response.data);
    } catch (error) {
      console.error('Error loading payroll runs:', error);
    }
  };

  const loadPayments = async () => {
    try {
      const response = await api.payments.list(filters);
      setPayments(response.data);
    } catch (error) {
      console.error('Error loading payments:', error);
    }
  };

  const loadPendingApprovals = async () => {
    try {
      const response = await api.payments.pendingApprovals();
      setPendingApprovals(response.data);
    } catch (error) {
      console.error('Error loading pending approvals:', error);
    }
  };

  const loadBankAccounts = async () => {
    try {
      const response = await api.finance.bankAccounts();
      setBankAccounts(response.data);
    } catch (error) {
      console.error('Error loading bank accounts:', error);
    }
  };

  // ============================================================================
  // PAYROLL ACTIONS
  // ============================================================================

  const handleCreatePayroll = async (data) => {
    try {
      await api.payroll.create(data);
      await loadPayrollRuns();
      setShowCreatePayroll(false);
    } catch (error) {
      console.error('Error creating payroll:', error);
    }
  };

  const handleRunPayroll = async (payrollId) => {
    try {
      await api.payroll.execute(payrollId);
      await loadPayrollRuns();
    } catch (error) {
      console.error('Error running payroll:', error);
    }
  };

  const handleExportPayroll = async (payrollId, format = 'excel') => {
    try {
      // Start async export
      const response = await api.payroll.exportAsync(payrollId, { format });
      const exportId = response.data.export_id;
      
      // Track export status
      setExportStatus(prev => ({
        ...prev,
        [exportId]: { status: 'processing', progress: 0 }
      }));

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.payroll.exportStatus(exportId);
          const { status, progress, download_url } = statusResponse.data;

          setExportStatus(prev => ({
            ...prev,
            [exportId]: { status, progress, download_url }
          }));

          if (status === 'completed') {
            clearInterval(pollInterval);
            // Auto-download
            window.location.href = download_url;
          } else if (status === 'failed') {
            clearInterval(pollInterval);
          }
        } catch (error) {
          clearInterval(pollInterval);
          console.error('Error checking export status:', error);
        }
      }, 2000); // Poll every 2 seconds

    } catch (error) {
      console.error('Error exporting payroll:', error);
    }
  };

  const handleDownloadPayroll = async (fileId) => {
    try {
      const response = await api.payroll.downloadFile(fileId);
      // Download file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `payroll_${fileId}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading payroll file:', error);
    }
  };

  // ============================================================================
  // PAYMENT ACTIONS
  // ============================================================================

  const handleApprovePayment = async (paymentId, approvalData) => {
    try {
      await api.payments.approve(paymentId, approvalData);
      await loadPendingApprovals();
      await loadPayments();
    } catch (error) {
      console.error('Error approving payment:', error);
    }
  };

  const handleRejectPayment = async (paymentId, reason) => {
    try {
      await api.payments.reject(paymentId, { reason });
      await loadPendingApprovals();
      await loadPayments();
    } catch (error) {
      console.error('Error rejecting payment:', error);
    }
  };

  const handleNewPaymentApprove = async (paymentId, data) => {
    // New approval flow with additional checks
    try {
      await api.payments.newApprove(paymentId, {
        ...data,
        verification_level: 'enhanced',
        requires_manager_approval: true
      });
      await loadPendingApprovals();
    } catch (error) {
      console.error('Error in new payment approval:', error);
    }
  };

  const handleCreatePayment = async (paymentData) => {
    try {
      await api.payments.create(paymentData);
      await loadPayments();
      setShowPaymentModal(false);
    } catch (error) {
      console.error('Error creating payment:', error);
    }
  };

  const handleSyncPayments = async () => {
    try {
      await api.payments.sync();
      await loadPayments();
    } catch (error) {
      console.error('Error syncing payments:', error);
    }
  };

  // ============================================================================
  // BANK DETAILS ACTIONS
  // ============================================================================

  const handleAddBankAccount = async (accountData) => {
    try {
      await api.finance.addBankAccount(accountData);
      await loadBankAccounts();
      setShowBankModal(false);
    } catch (error) {
      console.error('Error adding bank account:', error);
    }
  };

  const handleUpdateBankAccount = async (accountId, accountData) => {
    try {
      await api.finance.updateBankAccount(accountId, accountData);
      await loadBankAccounts();
      setShowBankModal(false);
    } catch (error) {
      console.error('Error updating bank account:', error);
    }
  };

  const handleDeleteBankAccount = async (accountId) => {
    try {
      await api.finance.deleteBankAccount(accountId);
      await loadBankAccounts();
    } catch (error) {
      console.error('Error deleting bank account:', error);
    }
  };

  const handleVerifyBankAccount = async (accountId) => {
    try {
      await api.finance.verifyBankAccount(accountId);
      await loadBankAccounts();
    } catch (error) {
      console.error('Error verifying bank account:', error);
    }
  };

  // ============================================================================
  // RENDER OVERVIEW TAB
  // ============================================================================

  const renderOverview = () => {
    if (!financeStats) return <div>Loading...</div>;

    const stats = [
      {
        title: 'Total Payroll This Month',
        value: `₹${(financeStats.total_payroll || 0).toLocaleString()}`,
        change: financeStats.payroll_change || 0,
        icon: DollarSign,
        color: 'blue',
        trend: 'up'
      },
      {
        title: 'Pending Payments',
        value: financeStats.pending_payments || 0,
        subtitle: `₹${(financeStats.pending_amount || 0).toLocaleString()}`,
        icon: Clock,
        color: 'orange'
      },
      {
        title: 'Approved Payments',
        value: financeStats.approved_payments || 0,
        subtitle: `₹${(financeStats.approved_amount || 0).toLocaleString()}`,
        icon: CheckCircle,
        color: 'green'
      },
      {
        title: 'Failed Transactions',
        value: financeStats.failed_payments || 0,
        subtitle: 'Requires attention',
        icon: XCircle,
        color: 'red'
      },
      {
        title: 'Active Employees',
        value: financeStats.active_employees || 0,
        subtitle: 'On payroll',
        icon: Users,
        color: 'purple'
      },
      {
        title: 'Avg Salary',
        value: `₹${(financeStats.avg_salary || 0).toLocaleString()}`,
        subtitle: 'Per employee',
        icon: TrendingUp,
        color: 'green'
      },
      {
        title: 'Bank Accounts',
        value: financeStats.bank_accounts || 0,
        subtitle: `${financeStats.verified_accounts || 0} verified`,
        icon: Building,
        color: 'blue'
      },
      {
        title: 'Pending Approvals',
        value: financeStats.pending_approvals || 0,
        subtitle: 'Action required',
        icon: AlertCircle,
        color: 'yellow'
      }
    ];

    return (
      <div>
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            const TrendIcon = stat.trend === 'up' ? ArrowUpRight : stat.trend === 'down' ? ArrowDownRight : null;

            return (
              <div
                key={index}
                className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-lg bg-${stat.color}-100`}>
                    <Icon className={`w-6 h-6 text-${stat.color}-600`} />
                  </div>
                  {stat.change !== undefined && TrendIcon && (
                    <div className={`flex items-center gap-1 text-sm ${
                      stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      <TrendIcon className="w-4 h-4" />
                      <span>{Math.abs(stat.change)}%</span>
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900 mb-1">
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-600">
                    {stat.title}
                  </div>
                  {stat.subtitle && (
                    <div className="text-xs text-gray-500 mt-1">
                      {stat.subtitle}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Monthly Metrics Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Monthly Payroll Trend
          </h3>
          <div className="h-64 flex items-end justify-between gap-4">
            {monthlyMetrics.map((month, index) => {
              const maxHeight = Math.max(...monthlyMetrics.map(m => m.total));
              const height = (month.total / maxHeight) * 100;

              return (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-blue-600 rounded-t hover:bg-blue-700 transition-colors cursor-pointer"
                    style={{ height: `${height}%` }}
                    title={`₹${month.total.toLocaleString()}`}
                  ></div>
                  <div className="mt-2 text-xs text-gray-600 text-center">
                    {month.month}
                  </div>
                  <div className="text-xs text-gray-500">
                    ₹{(month.total / 1000).toFixed(0)}K
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => setActiveTab('payroll')}
            className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-all text-left"
          >
            <Wallet className="w-8 h-8 text-blue-600 mb-3" />
            <div className="font-semibold text-gray-900 mb-1">
              Manage Payroll
            </div>
            <div className="text-sm text-gray-600">
              Create and run payroll cycles
            </div>
          </button>

          <button
            onClick={() => setActiveTab('payments')}
            className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-all text-left"
          >
            <CreditCard className="w-8 h-8 text-green-600 mb-3" />
            <div className="font-semibold text-gray-900 mb-1">
              Payments
            </div>
            <div className="text-sm text-gray-600">
              View and manage all payments
            </div>
          </button>

          <button
            onClick={() => setActiveTab('approvals')}
            className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-all text-left"
          >
            <CheckCircle className="w-8 h-8 text-orange-600 mb-3" />
            <div className="font-semibold text-gray-900 mb-1">
              Approvals
              {pendingApprovals.length > 0 && (
                <span className="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                  {pendingApprovals.length}
                </span>
              )}
            </div>
            <div className="text-sm text-gray-600">
              Approve pending payments
            </div>
          </button>

          <button
            onClick={() => setActiveTab('bank')}
            className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-all text-left"
          >
            <Building className="w-8 h-8 text-purple-600 mb-3" />
            <div className="font-semibold text-gray-900 mb-1">
              Bank Accounts
            </div>
            <div className="text-sm text-gray-600">
              Manage bank details
            </div>
          </button>
        </div>
      </div>
    );
  };

  // ============================================================================
  // RENDER PAYROLL TAB
  // ============================================================================

  const renderPayroll = () => {
    return (
      <div>
        {/* Payroll Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Payroll Runs
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Manage monthly payroll cycles
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleSyncPayments()}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Sync Payments
              </button>
              <button
                onClick={() => setShowCreatePayroll(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Create Payroll
              </button>
            </div>
          </div>
        </div>

        {/* Payroll List */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Period
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Employees
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Total Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {payrollRuns.map(payroll => (
                <tr key={payroll.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {payroll.period_start} - {payroll.period_end}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {payroll.employee_count} employees
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-gray-900">
                      ₹{payroll.total_amount.toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      payroll.status === 'completed' ? 'bg-green-100 text-green-800' :
                      payroll.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                      payroll.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {payroll.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {new Date(payroll.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedPayroll(payroll)}
                        className="text-blue-600 hover:text-blue-900"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {payroll.status === 'draft' && (
                        <button
                          onClick={() => handleRunPayroll(payroll.id)}
                          className="text-green-600 hover:text-green-900"
                          title="Run Payroll"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleExportPayroll(payroll.id)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Export"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Export Status */}
        {Object.keys(exportStatus).length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-sm p-6">
            <h4 className="font-semibold text-gray-900 mb-4">Export Status</h4>
            {Object.entries(exportStatus).map(([exportId, status]) => (
              <div key={exportId} className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-700">Export #{exportId}</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {status.status}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${status.progress}%` }}
                  ></div>
                </div>
                {status.download_url && (
                  <a
                    href={status.download_url}
                    className="text-sm text-blue-600 hover:underline mt-2 inline-block"
                  >
                    Download File
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // ============================================================================
  // RENDER PAYMENTS TAB
  // ============================================================================

  const renderPayments = () => {
    return (
      <div>
        {/* Payments Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Payment Management
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Track and manage all employee payments
              </p>
            </div>
            <button
              onClick={() => setShowPaymentModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Payment
            </button>
          </div>
        </div>

        {/* Payments List */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Payment Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {payments.map(payment => (
                <tr key={payment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {payment.employee?.display_name || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {payment.employee?.employee_code || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-gray-900">
                      ₹{payment.amount.toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {payment.payment_type}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      payment.status === 'completed' ? 'bg-green-100 text-green-800' :
                      payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      payment.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {payment.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {payment.payment_date ? new Date(payment.payment_date).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedPayment(payment)}
                        className="text-blue-600 hover:text-blue-900"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {payment.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprovePayment(payment.id, {})}
                            className="text-green-600 hover:text-green-900"
                            title="Approve"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleRejectPayment(payment.id, 'Reason here')}
                            className="text-red-600 hover:text-red-900"
                            title="Reject"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // ============================================================================
  // RENDER APPROVALS TAB
  // ============================================================================

  const renderApprovals = () => {
    return (
      <div>
        {/* Approvals Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Pending Approvals
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {pendingApprovals.length} payment(s) awaiting approval
              </p>
            </div>
            {pendingApprovals.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-orange-100 text-orange-800 text-sm font-semibold rounded-full">
                  Action Required
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Pending Approvals List */}
        {pendingApprovals.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              All Caught Up!
            </h3>
            <p className="text-gray-600">
              No pending payment approvals at this time.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {pendingApprovals.map(approval => (
              <div
                key={approval.id}
                className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-orange-500"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <AlertCircle className="w-5 h-5 text-orange-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">
                          {approval.employee?.display_name || 'N/A'}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {approval.employee?.employee_code || 'N/A'} • {approval.payment_type}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-4 mb-4">
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Amount</div>
                        <div className="text-sm font-semibold text-gray-900">
                          ₹{approval.amount.toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Payment Date</div>
                        <div className="text-sm text-gray-900">
                          {approval.payment_date ? new Date(approval.payment_date).toLocaleDateString() : 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Submitted</div>
                        <div className="text-sm text-gray-900">
                          {new Date(approval.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 mb-1">Reference</div>
                        <div className="text-sm text-gray-900">
                          #{approval.reference_number || approval.id}
                        </div>
                      </div>
                    </div>

                    {approval.notes && (
                      <div className="bg-gray-50 rounded p-3 mb-4">
                        <div className="text-xs text-gray-500 mb-1">Notes</div>
                        <div className="text-sm text-gray-900">{approval.notes}</div>
                      </div>
                    )}
                  </div>

                  <div className="ml-6 flex flex-col gap-2">
                    <button
                      onClick={() => handleApprovePayment(approval.id, { approved_by: 'current_user' })}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Approve
                    </button>
                    <button
                      onClick={() => handleRejectPayment(approval.id, 'Rejected by manager')}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
                    >
                      <XCircle className="w-4 h-4" />
                      Reject
                    </button>
                    <button
                      onClick={() => setSelectedPayment(approval)}
                      className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // ============================================================================
  // RENDER BANK DETAILS TAB
  // ============================================================================

  const renderBankDetails = () => {
    return (
      <div>
        {/* Bank Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Bank Accounts
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Manage employee bank account details
              </p>
            </div>
            <button
              onClick={() => setShowBankModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Bank Account
            </button>
          </div>
        </div>

        {/* Bank Accounts List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bankAccounts.map(account => (
            <div
              key={account.id}
              className="bg-white rounded-lg shadow-sm p-6 border border-gray-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Building className="w-6 h-6 text-blue-600" />
                </div>
                {account.is_verified && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
                    Verified
                  </span>
                )}
              </div>

              <div className="space-y-2">
                <div>
                  <div className="text-xs text-gray-500">Account Holder</div>
                  <div className="font-semibold text-gray-900">
                    {account.account_holder_name || 'N/A'}
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-500">Bank Name</div>
                  <div className="text-sm text-gray-900">
                    {account.bank_name || 'N/A'}
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-500">Account Number</div>
                  <div className="text-sm text-gray-900 font-mono">
                    ****{account.account_number?.slice(-4) || '****'}
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-500">IFSC Code</div>
                  <div className="text-sm text-gray-900 font-mono">
                    {account.ifsc_code || 'N/A'}
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
                <button
                  onClick={() => {
                    setSelectedAccount(account);
                    setShowBankModal(true);
                  }}
                  className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                >
                  Edit
                </button>

                {!account.is_verified && (
                  <button
                    onClick={() => handleVerifyBankAccount(account.id)}
                    className="text-green-600 hover:text-green-900 text-sm font-medium"
                  >
                    Verify
                  </button>
                )}

                <button
                  onClick={() => handleDeleteBankAccount(account.id)}
                  className="text-red-600 hover:text-red-900 text-sm font-medium"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  if (loading && activeTab === 'overview') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading finance dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <DollarSign className="w-8 h-8 text-blue-600" />
              Finance & Payroll
            </h1>
            <p className="text-gray-600 mt-1">
              Complete financial management system
            </p>
          </div>

          <button
            onClick={loadAllFinanceData}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="flex border-b border-gray-200">
            {[
              { key: 'overview', label: 'Overview', icon: BarChart3 },
              { key: 'payroll', label: 'Payroll', icon: Wallet },
              { key: 'payments', label: 'Payments', icon: CreditCard },
              { 
                key: 'approvals', 
                label: 'Approvals', 
                icon: CheckCircle,
                badge: pendingApprovals.length 
              },
              { key: 'bank', label: 'Bank Details', icon: Building }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 px-6 py-4 text-sm font-medium transition-colors relative ${
                    activeTab === tab.key
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center justify-center gap-2">
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                    {tab.badge > 0 && (
                      <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                        {tab.badge}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'payroll' && renderPayroll()}
          {activeTab === 'payments' && renderPayments()}
          {activeTab === 'approvals' && renderApprovals()}
          {activeTab === 'bank' && renderBankDetails()}
        </div>
      </div>

      {/* TODO: Add modals for:
        - Create Payroll
        - Create Payment
        - Payment Details
        - Bank Account Form
      */}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, Users, DollarSign, Calendar, ClipboardList, 
  FileText, Award, TrendingUp, AlertCircle, CheckCircle, 
  Clock, Target, Briefcase, UserCheck, BarChart3, PieChart,
  ArrowUpRight, ArrowDownRight, Activity, Mail, Phone,
  MapPin, Building, Tag, Filter, Download, Upload, Plus,
  Edit, Trash2, Eye, Send, Archive, Star, Heart, ThumbsUp,
  MessageSquare, Bell, Settings, Search, RefreshCw, X
} from 'lucide-react';
import api from '../Services/api';


export default function CompleteDashboard() {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================
  
  const [employees, setEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // grid, table, cards
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  
  // Filter States
  const [filters, setFilters] = useState({
    search: '',
    department: '',
    position: '',
    employmentType: '',
    status: '',
    joiningDateFrom: '',
    joiningDateTo: '',
    salaryMin: '',
    salaryMax: '',
    skills: [],
    hasLeaveToday: false,
    hasEODPending: false,
    hasTasksOverdue: false,
    benchStatus: ''
  });

  // Modal States
  const [showEmployeeDetail, setShowEmployeeDetail] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [showOfferModal, setShowOfferModal] = useState(false);
  const [showCertificateModal, setShowCertificateModal] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);

  // Dropdown Data
  const [departments, setDepartments] = useState([]);
  const [positions, setPositions] = useState([]);
  const [skills, setSkills] = useState([]);

  // ============================================================================
  // DATA FETCHING
  // ============================================================================

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadEmployees(),
        loadStats(),
        loadDepartments(),
        loadPositions(),
        loadSkills()
      ]);
    } catch (error) {
      console.error('Error Loading Dashboard Data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadEmployees = async () => {
    try {
      const response = await api.employees.list({
        include_inactive: false,
        with_details: true
      });
      setEmployees(response.data);
      setFilteredEmployees(response.data);
    } catch (error) {
      console.error('Error Loading Employees:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.employees.dashboard();
      setStats(response.data);
    } catch (error) {
      console.error('Error Loading Stats:', error);
    }
  };

  const loadDepartments = async () => {
    try {
      const response = await api.departments.list();
      setDepartments(response.data);
    } catch (error) {
      console.error('Error Loading Departments:', error);
    }
  };

  const loadPositions = async () => {
    try {
      const response = await api.positions.list();
      setPositions(response.data);
    } catch (error) {
      console.error('Error Loading Positions:', error);
    }
  };

  const loadSkills = async () => {
    try {
      const response = await api.skills.list();
      setSkills(response.data);
    } catch (error) {
      console.error('Error Loading Skills:', error);
    }
  };

  // ============================================================================
  // FILTERING LOGIC
  // ============================================================================

  useEffect(() => {
    applyFilters();
  }, [filters, employees]);

  const applyFilters = () => {
    let filtered = [...employees];

    // Search filter
    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter(emp => 
        emp.display_name?.toLowerCase().includes(search) ||
        emp.employee_code?.toLowerCase().includes(search) ||
        emp.email?.toLowerCase().includes(search) ||
        emp.phone?.toLowerCase().includes(search)
      );
    }

    // Department filter
    if (filters.department) {
      filtered = filtered.filter(emp => 
        emp.department?.id === parseInt(filters.department)
      );
    }

    // Position filter
    if (filters.position) {
      filtered = filtered.filter(emp => 
        emp.position?.id === parseInt(filters.position)
      );
    }

    // Employment type filter
    if (filters.employmentType) {
      filtered = filtered.filter(emp => 
        emp.employment_type === filters.employmentType
      );
    }

    // Status filter
    if (filters.status) {
      filtered = filtered.filter(emp => 
        emp.is_active === (filters.status === 'active')
      );
    }

    // Date range filters
    if (filters.joiningDateFrom) {
      filtered = filtered.filter(emp => 
        new Date(emp.joining_date) >= new Date(filters.joiningDateFrom)
      );
    }

    if (filters.joiningDateTo) {
      filtered = filtered.filter(emp => 
        new Date(emp.joining_date) <= new Date(filters.joiningDateTo)
      );
    }

    // Salary range filters
    if (filters.salaryMin) {
      filtered = filtered.filter(emp => 
        emp.current_salary >= parseFloat(filters.salaryMin)
      );
    }

    if (filters.salaryMax) {
      filtered = filtered.filter(emp => 
        emp.current_salary <= parseFloat(filters.salaryMax)
      );
    }

    // Skills filter
    if (filters.skills.length > 0) {
      filtered = filtered.filter(emp => {
        const empSkills = emp.user_skills?.map(s => s.skill?.id) || [];
        return filters.skills.every(skillId => empSkills.includes(skillId));
      });
    }

    // Boolean filters
    if (filters.hasLeaveToday) {
      filtered = filtered.filter(emp => emp.has_leave_today);
    }

    if (filters.hasEODPending) {
      filtered = filtered.filter(emp => emp.eod_pending);
    }

    if (filters.hasTasksOverdue) {
      filtered = filtered.filter(emp => emp.has_overdue_tasks);
    }

    // Bench status filter
    if (filters.benchStatus) {
      filtered = filtered.filter(emp => {
        if (filters.benchStatus === 'on_bench') return emp.is_on_bench;
        if (filters.benchStatus === 'allocated') return !emp.is_on_bench;
        return true;
      });
    }

    setFilteredEmployees(filtered);
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      department: '',
      position: '',
      employmentType: '',
      status: '',
      joiningDateFrom: '',
      joiningDateTo: '',
      salaryMin: '',
      salaryMax: '',
      skills: [],
      hasLeaveToday: false,
      hasEODPending: false,
      hasTasksOverdue: false,
      benchStatus: ''
    });
  };

  // ============================================================================
  // EMPLOYEE ACTIONS
  // ============================================================================

  const handleViewEmployee = async (employee) => {
    try {
      const response = await api.employees.get(employee.id);
      setSelectedEmployee(response.data);
      setShowEmployeeDetail(true);
    } catch (error) {
      console.error('Error fetching employee details:', error);
    }
  };

  const handleEditEmployee = (employee) => {
    setSelectedEmployee(employee);
    setShowEditModal(true);
  };

  const handleDeactivateEmployee = (employee) => {
    setSelectedEmployee(employee);
    setShowDeactivateModal(true);
  };

  const confirmDeactivate = async () => {
    try {
      await api.employees.deactivate(selectedEmployee.id);
      await loadEmployees();
      setShowDeactivateModal(false);
      setSelectedEmployee(null);
    } catch (error) {
      console.error('Error deactivating employee:', error);
    }
  };

  const handleSendOffer = (employee) => {
    setSelectedEmployee(employee);
    setShowOfferModal(true);
  };

  const handleSendCertificate = (employee) => {
    setSelectedEmployee(employee);
    setShowCertificateModal(true);
  };

  const handleExportData = async (format = 'excel') => {
    try {
      const response = await api.employees.export({
        format,
        filters,
        employee_ids: selectedEmployees.length > 0 ? selectedEmployees : null
      });
      
      // Download file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `employees_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'csv'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  // ============================================================================
  // BULK ACTIONS
  // ============================================================================

  const handleSelectEmployee = (employeeId) => {
    setSelectedEmployees(prev => 
      prev.includes(employeeId)
        ? prev.filter(id => id !== employeeId)
        : [...prev, employeeId]
    );
  };

  const handleSelectAll = () => {
    if (selectedEmployees.length === filteredEmployees.length) {
      setSelectedEmployees([]);
    } else {
      setSelectedEmployees(filteredEmployees.map(emp => emp.id));
    }
  };

  const handleBulkAction = async (action) => {
    try {
      switch (action) {
        case 'deactivate':
          await api.employees.bulkDeactivate(selectedEmployees);
          break;
        case 'send_offer':
          await api.offers.bulkSend(selectedEmployees);
          break;
        case 'assign_goal':
          // Show goal assignment modal
          break;
        case 'update_department':
          // Show department update modal
          break;
        default:
          break;
      }
      await loadEmployees();
      setSelectedEmployees([]);
      setShowBulkActions(false);
    } catch (error) {
      console.error('Error performing bulk action:', error);
    }
  };

  // ============================================================================
  // RENDER STATS CARDS
  // ============================================================================

  const renderStatsCards = () => {
    if (!stats) return null;

    const cards = [
      {
        title: 'Total Employees',
        value: stats.total_employees || 0,
        change: stats.employee_growth || 0,
        icon: Users,
        color: 'blue',
        trend: 'up'
      },
      {
        title: 'On Leave Today',
        value: stats.on_leave_today || 0,
        subtitle: `${stats.leave_percentage || 0}% of team`,
        icon: Calendar,
        color: 'orange',
        trend: null
      },
      {
        title: 'EOD Pending',
        value: stats.eod_pending || 0,
        subtitle: 'Since yesterday',
        icon: ClipboardList,
        color: 'red',
        trend: null
      },
      {
        title: 'On Bench',
        value: stats.on_bench || 0,
        subtitle: 'Available for allocation',
        icon: UserCheck,
        color: 'green',
        trend: null
      },
      {
        title: 'Active Projects',
        value: stats.active_projects || 0,
        change: stats.project_growth || 0,
        icon: Briefcase,
        color: 'purple',
        trend: 'up'
      },
      {
        title: 'Pending Tasks',
        value: stats.pending_tasks || 0,
        subtitle: 'Across all employees',
        icon: Target,
        color: 'yellow',
        trend: null
      },
      {
        title: 'Payroll This Month',
        value: `₹${(stats.payroll_total || 0).toLocaleString()}`,
        change: stats.payroll_change || 0,
        icon: DollarSign,
        color: 'green',
        trend: stats.payroll_change >= 0 ? 'up' : 'down'
      },
      {
        title: 'Avg Performance',
        value: `${stats.avg_performance || 0}%`,
        subtitle: 'Team average',
        icon: TrendingUp,
        color: 'blue',
        trend: null
      }
    ];

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {cards.map((card, index) => {
          const Icon = card.icon;
          const trendIcon = card.trend === 'up' ? ArrowUpRight : card.trend === 'down' ? ArrowDownRight : null;
          const TrendIcon = trendIcon;

          return (
            <div
              key={index}
              className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg bg-${card.color}-100`}>
                  <Icon className={`w-6 h-6 text-${card.color}-600`} />
                </div>
                {card.change !== undefined && TrendIcon && (
                  <div className={`flex items-center gap-1 text-sm ${
                    card.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    <TrendIcon className="w-4 h-4" />
                    <span>{Math.abs(card.change)}%</span>
                  </div>
                )}
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {card.value}
                </div>
                <div className="text-sm text-gray-600">
                  {card.title}
                </div>
                {card.subtitle && (
                  <div className="text-xs text-gray-500 mt-1">
                    {card.subtitle}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // ============================================================================
  // RENDER FILTERS
  // ============================================================================

  const renderFilters = () => {
    if (!showFilters) return null;

    return (
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Advanced Filters</h3>
          <button
            onClick={() => setShowFilters(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
              placeholder="Name, code, email..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Department
            </label>
            <select
              value={filters.department}
              onChange={(e) => setFilters({...filters, department: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Departments</option>
              {departments.map(dept => (
                <option key={dept.id} value={dept.id}>{dept.name}</option>
              ))}
            </select>
          </div>

          {/* Position */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Position
            </label>
            <select
              value={filters.position}
              onChange={(e) => setFilters({...filters, position: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Positions</option>
              {positions.map(pos => (
                <option key={pos.id} value={pos.id}>{pos.title}</option>
              ))}
            </select>
          </div>

          {/* Employment Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Employment Type
            </label>
            <select
              value={filters.employmentType}
              onChange={(e) => setFilters({...filters, employmentType: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="full_time">Full Time</option>
              <option value="part_time">Part Time</option>
              <option value="contract">Contract</option>
              <option value="intern">Intern</option>
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {/* Bench Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bench Status
            </label>
            <select
              value={filters.benchStatus}
              onChange={(e) => setFilters({...filters, benchStatus: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="on_bench">On Bench</option>
              <option value="allocated">Allocated</option>
            </select>
          </div>

          {/* Joining Date From */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Joining Date From
            </label>
            <input
              type="date"
              value={filters.joiningDateFrom}
              onChange={(e) => setFilters({...filters, joiningDateFrom: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Joining Date To */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Joining Date To
            </label>
            <input
              type="date"
              value={filters.joiningDateTo}
              onChange={(e) => setFilters({...filters, joiningDateTo: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Salary Min */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Salary Min (₹)
            </label>
            <input
              type="number"
              value={filters.salaryMin}
              onChange={(e) => setFilters({...filters, salaryMin: e.target.value})}
              placeholder="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Salary Max */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Salary Max (₹)
            </label>
            <input
              type="number"
              value={filters.salaryMax}
              onChange={(e) => setFilters({...filters, salaryMax: e.target.value})}
              placeholder="1000000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Boolean Filters */}
          <div className="col-span-full">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quick Filters
            </label>
            <div className="flex flex-wrap gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.hasLeaveToday}
                  onChange={(e) => setFilters({...filters, hasLeaveToday: e.target.checked})}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">On Leave Today</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.hasEODPending}
                  onChange={(e) => setFilters({...filters, hasEODPending: e.target.checked})}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">EOD Pending</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.hasTasksOverdue}
                  onChange={(e) => setFilters({...filters, hasTasksOverdue: e.target.checked})}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Overdue Tasks</span>
              </label>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            onClick={clearFilters}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Clear All
          </button>
          <button
            onClick={() => setShowFilters(false)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Apply Filters
          </button>
        </div>
      </div>
    );
  };

  // ============================================================================
  // RENDER EMPLOYEE GRID
  // ============================================================================

  const renderEmployeeGrid = () => {
    if (filteredEmployees.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Employees Found
          </h3>
          <p className="text-gray-600 mb-4">
            Try adjusting your filters or search criteria
          </p>
          <button
            onClick={clearFilters}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Clear Filters
          </button>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {/* Table Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <input
                type="checkbox"
                checked={selectedEmployees.length === filteredEmployees.length}
                onChange={handleSelectAll}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                {selectedEmployees.length > 0 
                  ? `${selectedEmployees.length} selected`
                  : `${filteredEmployees.length} employees`
                }
              </span>
            </div>

            {selectedEmployees.length > 0 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowBulkActions(true)}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Bulk Actions
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Table Body */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Position
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEmployees.map(employee => (
                <tr key={employee.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedEmployees.includes(employee.id)}
                      onChange={() => handleSelectEmployee(employee.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-blue-600 font-semibold">
                            {employee.display_name?.charAt(0) || 'E'}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {employee.display_name || 'N/A'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {employee.employee_code || 'N/A'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {employee.department?.name || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {employee.position?.title || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      employee.is_active 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {employee.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {employee.is_on_bench && (
                      <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        Bench
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${employee.performance_score || 0}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-700">
                        {employee.performance_score || 0}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleViewEmployee(employee)}
                        className="text-blue-600 hover:text-blue-900"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEditEmployee(employee)}
                        className="text-green-600 hover:text-green-900"
                        title="Edit"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleSendOffer(employee)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Send Offer"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeactivateEmployee(employee)}
                        className="text-red-600 hover:text-red-900"
                        title="Deactivate"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
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
  // MAIN RENDER
  // ============================================================================

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
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
              <LayoutDashboard className="w-8 h-8 text-blue-600" />
              HRMS Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Complete employee management system
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>

            <button
              onClick={() => handleExportData('excel')}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export
            </button>

            <button
              onClick={() => window.location.href = '/employees/register'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Employee
            </button>

            <button
              onClick={() => loadAllData()}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {renderStatsCards()}

        {/* Filters */}
        {renderFilters()}

        {/* Employee Grid */}
        {renderEmployeeGrid()}
      </div>

      {/* TODO: Add modals for:
        - Employee Detail View
        - Edit Employee
        - Deactivate Confirmation
        - Send Offer
        - Send Certificate
        - Bulk Actions
      */}
    </div>
  );
}

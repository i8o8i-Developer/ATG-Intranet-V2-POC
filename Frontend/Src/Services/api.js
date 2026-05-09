/* *
 * API Service Layer - Banao Intranet v2
 * Centralized API Integration With Axios
 * */

import axios from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const DEFAULT_TIMEOUT = 30000; // 30 Seconds

// Create Axios Instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Request Interceptor
// ============================================================================
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    const tenantId = localStorage.getItem('tenantId');
    if (tenantId) {
      config.headers['X-Tenant-Id'] = tenantId;
    }

    const workspaceId = localStorage.getItem('workspaceId');
    if (workspaceId) {
      config.headers['X-Workspace-Id'] = workspaceId;
    }

    if (import.meta.env.DEV) {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }

    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// ============================================================================
// Response Interceptor
// ============================================================================
apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`✅ API Response: ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const message = error.response?.data?.message || error.message;

    console.error(`❌ API Error [${status}]: ${message}`);

    switch (status) {
      case 401:
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.location.href = '/login';
        break;

      case 403:
        console.error('Permission Denied:', message);
        break;

      case 404:
        console.error('Resource Not Found:', message);
        break;

      case 422:
        console.error('Validation Error:', error.response?.data);
        break;

      case 500:
        console.error('Server Error:', message);
        break;

      default:
        console.error('Unexpected Error:', error);
    }

    return Promise.reject(error);
  }
);

// ============================================================================
// API Service Methods
// ============================================================================
const api = {
  get: (url, config = {}) => apiClient.get(url, config),
  post: (url, data = {}, config = {}) => apiClient.post(url, data, config),
  put: (url, data = {}, config = {}) => apiClient.put(url, data, config),
  patch: (url, data = {}, config = {}) => apiClient.patch(url, data, config),
  delete: (url, config = {}) => apiClient.delete(url, config),

  // ============================================================================
  // Authentication
  // ============================================================================
  auth: {
    login: (credentials) => apiClient.post('/users/login/', credentials),
    logout: () => apiClient.post('/users/logout/'),
    getCurrentUser: () => apiClient.get('/users/current/'),
    changePassword: (data) => apiClient.post('/users/change-password/', data),
  },

  // ============================================================================
  // HRMS / Employees
  // ============================================================================
  employees: {
    list: (params = {}) => apiClient.get('/users/employees/', { params }),
    get: (id) => apiClient.get(`/users/employees/${id}/`),
    create: (data) => apiClient.post('/users/employees/', data),
    update: (id, data) => apiClient.put(`/users/employees/${id}/`, data),
    patch: (id, data) => apiClient.patch(`/users/employees/${id}/`, data),
    delete: (id) => apiClient.delete(`/users/employees/${id}/`),
    
    // Employee Actions
    activate: (id) => apiClient.post(`/users/employees/${id}/activate/`),
    changeStatus: (id, data) => apiClient.post(`/users/employees/${id}/change-status/`, data),
    transferDepartment: (id, data) => apiClient.post(`/users/employees/${id}/transfer-department/`, data),
    assignSkill: (id, data) => apiClient.post(`/users/employees/${id}/assign-skill/`, data),
    completeOnboarding: (id) => apiClient.post(`/users/employees/${id}/complete-onboarding/`),
    saveTimezone: (id, data) => apiClient.post(`/users/employees/${id}/save-timezone/`, data),
    
    // Dashboard
    dashboard: () => apiClient.get('/users/employees/dashboard/'),
  },

  // ============================================================================
  // Departments
  // ============================================================================
  departments: {
    list: (params = {}) => apiClient.get('/users/departments/', { params }),
    get: (id) => apiClient.get(`/users/departments/${id}/`),
    create: (data) => apiClient.post('/users/departments/', data),
    update: (id, data) => apiClient.put(`/users/departments/${id}/`, data),
    delete: (id) => apiClient.delete(`/users/departments/${id}/`),
    assignDefaultSkills: (id, data) => apiClient.post(`/users/departments/${id}/assign-default-skills/`, data),
  },

  // ============================================================================
  // Positions
  // ============================================================================
  positions: {
    list: (params = {}) => apiClient.get('/users/positions/', { params }),
    get: (id) => apiClient.get(`/users/positions/${id}/`),
    create: (data) => apiClient.post('/users/positions/', data),
    update: (id, data) => apiClient.put(`/users/positions/${id}/`, data),
    delete: (id) => apiClient.delete(`/users/positions/${id}/`),
  },

  // ============================================================================
  // Skills
  // ============================================================================
  skills: {
    list: (params = {}) => apiClient.get('/users/skills/', { params }),
    get: (id) => apiClient.get(`/users/skills/${id}/`),
    create: (data) => apiClient.post('/users/skills/', data),
    update: (id, data) => apiClient.put(`/users/skills/${id}/`, data),
    delete: (id) => apiClient.delete(`/users/skills/${id}/`),
  },

  userSkills: {
    list: (params = {}) => apiClient.get('/users/user-skills/', { params }),
    create: (data) => apiClient.post('/users/user-skills/', data),
    update: (id, data) => apiClient.put(`/users/user-skills/${id}/`, data),
    delete: (id) => apiClient.delete(`/users/user-skills/${id}/`),
  },

  // ============================================================================
  // Goals & Feedback
  // ============================================================================
  goals: {
    list: (params = {}) => apiClient.get('/users/goals/', { params }),
    get: (id) => apiClient.get(`/users/goals/${id}/`),
    create: (data) => apiClient.post('/users/goals/', data),
    update: (id, data) => apiClient.put(`/users/goals/${id}/`, data),
    delete: (id) => apiClient.delete(`/users/goals/${id}/`),
  },

  goalFeedback: {
    list: (params = {}) => apiClient.get('/users/goal-feedback/', { params }),
    create: (data) => apiClient.post('/users/goal-feedback/', data),
  },

  // ============================================================================
  // Payroll & Payments
  // ============================================================================
  payments: {
    list: (params = {}) => apiClient.get('/users/payments/', { params }),
    get: (id) => apiClient.get(`/users/payments/${id}/`),
    requestSync: (data) => apiClient.post('/users/payments/request-status-sync/', data),
  },

  payroll: {
    exportAsync: (data) => apiClient.post('/users/payroll/export/', data),
    exportStatus: (taskId) => apiClient.get(`/users/payroll/export-status/${taskId}/`),
    download: (fileId) => apiClient.get(`/users/payroll/download/${fileId}/`, { responseType: 'blob' }),
  },

  // ============================================================================
  // Leaves
  // ============================================================================
  leaves: {
    list: (params = {}) => apiClient.get('/mainapp/leaves/', { params }),
    get: (id) => apiClient.get(`/mainapp/leaves/${id}/`),
    create: (data) => apiClient.post('/mainapp/leaves/', data),
    update: (id, data) => apiClient.put(`/mainapp/leaves/${id}/`, data),
    approve: (id, data) => apiClient.post(`/mainapp/leaves/${id}/approve/`, data),
    reject: (id, data) => apiClient.post(`/mainapp/leaves/${id}/reject/`, data),
    cancel: (id) => apiClient.post(`/mainapp/leaves/${id}/cancel/`),
  },

  leaveBalances: {
    list: (params = {}) => apiClient.get('/users/leave-balances/', { params }),
    accrueAll: (data) => apiClient.post('/users/leave-balances/accrue-all/', data),
  },

  leavePolicies: {
    list: (params = {}) => apiClient.get('/users/leave-policies/', { params }),
    get: (id) => apiClient.get(`/users/leave-policies/${id}/`),
    create: (data) => apiClient.post('/users/leave-policies/', data),
    update: (id, data) => apiClient.put(`/users/leave-policies/${id}/`, data),
  },

  // ============================================================================
  // EOD & Effort Reports
  // ============================================================================
  eod: {
    list: (params = {}) => apiClient.get('/tasks/eod/', { params }),
    get: (id) => apiClient.get(`/tasks/eod/${id}/`),
    create: (data) => apiClient.post('/tasks/eod/', data),
    update: (id, data) => apiClient.put(`/tasks/eod/${id}/`, data),
  },

  effortReports: {
    list: (params = {}) => apiClient.get('/users/effort-reports/', { params }),
    submit: (data) => apiClient.post('/users/effort-reports/submit/', data),
    createReminders: (data) => apiClient.post('/users/effort-reports/create-reminders/', data),
  },

  // ============================================================================
  // Projects
  // ============================================================================
  projects: {
    list: (params = {}) => apiClient.get('/projects/', { params }),
    get: (id) => apiClient.get(`/projects/${id}/`),
    create: (data) => apiClient.post('/projects/', data),
    update: (id, data) => apiClient.put(`/projects/${id}/`, data),
    delete: (id) => apiClient.delete(`/projects/${id}/`),
    
    // Project Actions
    addMember: (id, data) => apiClient.post(`/projects/${id}/add-member/`, data),
    removeMember: (id, data) => apiClient.post(`/projects/${id}/remove-member/`, data),
    updateBudget: (id, data) => apiClient.post(`/projects/${id}/update-budget/`, data),
  },

  // ============================================================================
  // Tasks
  // ============================================================================
  tasks: {
    list: (params = {}) => apiClient.get('/tasks/', { params }),
    get: (id) => apiClient.get(`/tasks/${id}/`),
    create: (data) => apiClient.post('/tasks/', data),
    update: (id, data) => apiClient.put(`/tasks/${id}/`, data),
    delete: (id) => apiClient.delete(`/tasks/${id}/`),
    markComplete: (id) => apiClient.post(`/tasks/${id}/mark-complete/`),
  },

  // ============================================================================
  // Offers & Certificates
  // ============================================================================
  offers: {
    // CRUD Operations
    list: (params = {}) => apiClient.get('/mainapp/OnboardingOffers/', { params }),
    get: (id) => apiClient.get(`/mainapp/OnboardingOffers/${id}/`),
    create: (data) => apiClient.post('/mainapp/OnboardingOffers/', data),
    update: (id, data) => apiClient.put(`/mainapp/OnboardingOffers/${id}/`, data),
    delete: (id) => apiClient.delete(`/mainapp/OnboardingOffers/${id}/`),
    
    // Offer Lifecycle
    issue: (id, data = {}) => apiClient.post(`/mainapp/OnboardingOffers/${id}/issue/`, data),
    accept: (data) => apiClient.post('/mainapp/OnboardingOffers/accept/', data),
    queueReminders: () => apiClient.post('/mainapp/OnboardingOffers/queue-reminders/'),
    
    // Legacy Send Methods
    send: (data) => apiClient.post('/mainapp/send-offer/', data),
    sendPdf: (data) => apiClient.post('/mainapp/send-pdf-offer/', data),
    
    // Preview & Download
    preview: (token) => apiClient.get(`/mainapp/offer/${token}/`),
    download: (token) => apiClient.get(`/mainapp/download-offer/${token}/`, { responseType: 'blob' }),
  },

  certificates: {
    send: (data) => apiClient.post('/mainapp/send-certificate/', data),
  },

  // ============================================================================
  // Notifications
  // ============================================================================
  notifications: {
    list: (params = {}) => apiClient.get('/mainapp/notifications/', { params }),
    markRead: (id) => apiClient.post(`/mainapp/notifications/${id}/mark-read/`),
    markAllRead: () => apiClient.post('/mainapp/notifications/mark-all-read/'),
    delete: (id) => apiClient.delete(`/mainapp/notifications/${id}/`),
  },

  // ============================================================================
  // Resignations
  // ============================================================================
  resignations: {
    list: (params = {}) => apiClient.get('/users/resignations/', { params }),
    get: (id) => apiClient.get(`/users/resignations/${id}/`),
    create: (data) => apiClient.post('/users/resignations/', data),
    approve: (id, data) => apiClient.post(`/users/resignations/${id}/approve/`, data),
  },

  // ============================================================================
  // Analytics & Reports
  // ============================================================================
  analytics: {
    headcount: (params = {}) => apiClient.get('/analytics/headcount/', { params }),
    performance: (params = {}) => apiClient.get('/analytics/performance/', { params }),
    attendance: (params = {}) => apiClient.get('/analytics/attendance/', { params }),
    payroll: (params = {}) => apiClient.get('/analytics/payroll/', { params }),
  },
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Set Authentication Token
 */
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('authToken', token);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    localStorage.removeItem('authToken');
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

/**
 * Set Tenant Context
 */
export const setTenantContext = (tenantId, workspaceId = null) => {
  if (tenantId) {
    localStorage.setItem('tenantId', tenantId);
  } else {
    localStorage.removeItem('tenantId');
  }

  if (workspaceId) {
    localStorage.setItem('workspaceId', workspaceId);
  } else {
    localStorage.removeItem('workspaceId');
  }
};

/**
 * Get Current User From Local Storage
 */
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};

/**
 * Save Current User To Local Storage
 */
export const saveCurrentUser = (user) => {
  localStorage.setItem('user', JSON.stringify(user));
};

/**
 * Clear All Auth Data
 */
export const clearAuth = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('user');
  localStorage.removeItem('tenantId');
  localStorage.removeItem('workspaceId');
  delete apiClient.defaults.headers.common['Authorization'];
};

/**
 * Handle API Errors With User-Friendly Messages
 */
export const handleApiError = (error) => {
  if (error.response) {
    // Server Responded With Error Status
    const status = error.response.status;
    const data = error.response.data;

    if (status === 422 && data.errors) {
      // Validation Errors
      return {
        type: 'validation',
        errors: data.errors,
        message: 'Please Fix The Validation Errors',
      };
    }

    return {
      type: 'error',
      message: data.message || data.detail || 'An Error Occurred',
      status,
    };
  } else if (error.request) {
    // Request Made But No Response
    return {
      type: 'error',
      message: 'No Response From Server. Please Check Your Connection.',
    };
  } else {
    // Error In Request Setup
    return {
      type: 'error',
      message: error.message || 'An Unexpected Error Occurred',
    };
  }
};

/**
 * Download File From Blob Response
 */
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default api;
export { apiClient };

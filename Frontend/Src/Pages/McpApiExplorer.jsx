import React, { useState, useEffect } from 'react';
import { Search, Code, Play, Copy, Settings, Database, Zap, FileJson } from 'lucide-react';

/**
 * MCP API Explorer - Main UI for AI-ERP Integration
 * 
 * This component exposes all backend APIs for:
 * - AI agents to discover and use endpoints
 * - Developers to test and configure MCP tools
 * - Editing request payloads in real-time
 */
export default function McpApiExplorer() {
  const [endpoints, setEndpoints] = useState([]);
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [requestPayload, setRequestPayload] = useState('{}');
  const [responseData, setResponseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterModule, setFilterModule] = useState('all');

  // API Endpoint Discovery - Load all available endpoints
  useEffect(() => {
    discoverEndpoints();
  }, []);

  const discoverEndpoints = async () => {
    // TODO: Call backend introspection API to get all available endpoints
    // For now, using static data structure
    const mockEndpoints = [
      // Enterprise Core
      {
        id: 1,
        module: 'EnterpriseCore',
        name: 'List Tenants',
        method: 'GET',
        path: '/EnterpriseCore/Tenants/',
        description: 'Get all tenants in the system',
        mcpTool: 'list_tenants',
        params: {},
        samplePayload: null,
        requiresAuth: true
      },
      {
        id: 2,
        module: 'EnterpriseCore',
        name: 'Create Workspace',
        method: 'POST',
        path: '/EnterpriseCore/Workspaces/',
        description: 'Create a new workspace',
        mcpTool: 'create_workspace',
        params: { tenant_id: 'integer', name: 'string' },
        samplePayload: { tenant_id: 1, name: 'New Workspace' },
        requiresAuth: true
      },
      
      // Users
      {
        id: 3,
        module: 'Users',
        name: 'List Employees',
        method: 'GET',
        path: '/Users/Employees/',
        description: 'Get all employees',
        mcpTool: 'list_employees',
        params: {},
        samplePayload: null,
        requiresAuth: true
      },
      {
        id: 4,
        module: 'Users',
        name: 'Create Employee',
        method: 'POST',
        path: '/Users/Employees/',
        description: 'Create a new employee profile',
        mcpTool: 'create_employee',
        params: {
          user: 'integer',
          employee_code: 'string',
          display_name: 'string',
          position: 'integer'
        },
        samplePayload: {
          user: 2,
          employee_code: 'EMP009',
          display_name: 'New Employee',
          position: 1
        },
        requiresAuth: true
      },
      
      // Projects
      {
        id: 5,
        module: 'Project',
        name: 'List Projects',
        method: 'GET',
        path: '/Project/Workspaces/',
        description: 'Get all project workspaces',
        mcpTool: 'list_projects',
        params: {},
        samplePayload: null,
        requiresAuth: true
      },
      {
        id: 6,
        module: 'Project',
        name: 'Create Project',
        method: 'POST',
        path: '/Project/Workspaces/',
        description: 'Create a new project workspace',
        mcpTool: 'create_project',
        params: {
          title: 'string',
          description: 'string',
          project_type: 'string'
        },
        samplePayload: {
          title: 'New AI Project',
          description: 'AI-powered feature development',
          project_type: 'development'
        },
        requiresAuth: true
      },
      
      // Tasks Dashboard
      {
        id: 7,
        module: 'TasksDashboard',
        name: 'List Work Items',
        method: 'GET',
        path: '/TasksDashboard/WorkItems/',
        description: 'Get all work items/tasks',
        mcpTool: 'list_work_items',
        params: {},
        samplePayload: null,
        requiresAuth: true
      },
      {
        id: 8,
        module: 'TasksDashboard',
        name: 'Create Work Item',
        method: 'POST',
        path: '/TasksDashboard/WorkItems/',
        description: 'Create a new work item/task',
        mcpTool: 'create_work_item',
        params: {
          title: 'string',
          description: 'string',
          assigned_to: 'integer',
          status: 'string'
        },
        samplePayload: {
          title: 'Implement MCP Integration',
          description: 'Build AI-ERP MCP tools',
          assigned_to: 2,
          status: 'in_progress'
        },
        requiresAuth: true
      },
      
      // Finance & Payroll
      {
        id: 9,
        module: 'FinanceAndPayroll',
        name: 'List Payroll Runs',
        method: 'GET',
        path: '/FinanceAndPayroll/PayrollRuns/',
        description: 'Get all payroll runs',
        mcpTool: 'list_payroll_runs',
        params: {},
        samplePayload: null,
        requiresAuth: true
      },
      {
        id: 10,
        module: 'FinanceAndPayroll',
        name: 'Create Payment Order',
        method: 'POST',
        path: '/FinanceAndPayroll/PaymentOrders/',
        description: 'Create a new payment order',
        mcpTool: 'create_payment_order',
        params: {
          employee: 'integer',
          amount: 'decimal',
          payment_type: 'string'
        },
        samplePayload: {
          employee: 2,
          amount: '50000.00',
          payment_type: 'salary'
        },
        requiresAuth: true
      },

      // MainApp
      {
        id: 11,
        module: 'MainApp',
        name: 'List Leave Requests',
        method: 'GET',
        path: '/MainApp/LeaveRequests/',
        description: 'Get all leave requests',
        mcpTool: 'list_leave_requests',
        params: {},
        samplePayload: null,
        requiresAuth: true
      },
      {
        id: 12,
        module: 'MainApp',
        name: 'Create Leave Request',
        method: 'POST',
        path: '/MainApp/LeaveRequests/',
        description: 'Submit a new leave request',
        mcpTool: 'create_leave_request',
        params: {
          employee: 'integer',
          start_date: 'date',
          end_date: 'date',
          leave_type: 'string',
          reason: 'string'
        },
        samplePayload: {
          employee: 2,
          start_date: '2026-05-10',
          end_date: '2026-05-12',
          leave_type: 'vacation',
          reason: 'Family trip'
        },
        requiresAuth: true
      },

      // MCP Access Layer
      {
        id: 13,
        module: 'McpAccessLayer',
        name: 'List MCP Tools',
        method: 'GET',
        path: '/McpAccessLayer/ToolDefinitions/',
        description: 'Get all configured MCP tools',
        mcpTool: 'list_mcp_tools',
        params: {},
        samplePayload: null,
        requiresAuth: true
      },
      {
        id: 14,
        module: 'McpAccessLayer',
        name: 'Execute MCP Tool',
        method: 'POST',
        path: '/McpAccessLayer/Invocations/',
        description: 'Execute an MCP tool with parameters',
        mcpTool: 'execute_mcp_tool',
        params: {
          tool_name: 'string',
          parameters: 'object',
          agent_principal: 'integer'
        },
        samplePayload: {
          tool_name: 'create_employee',
          parameters: { employee_code: 'EMP010', display_name: 'AI Agent Created' },
          agent_principal: 1
        },
        requiresAuth: true
      }
    ];

    setEndpoints(mockEndpoints);
  };

  // Filter endpoints based on search and module
  const filteredEndpoints = endpoints.filter(endpoint => {
    const matchesSearch = 
      endpoint.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.path.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesModule = filterModule === 'all' || endpoint.module === filterModule;
    
    return matchesSearch && matchesModule;
  });

  // Get unique modules for filter dropdown
  const modules = ['all', ...new Set(endpoints.map(e => e.module))];

  // Execute API call
  const executeRequest = async () => {
    if (!selectedEndpoint) return;

    setLoading(true);
    setResponseData(null);

    try {
      const options = {
        method: selectedEndpoint.method,
        headers: {
          'Content-Type': 'application/json',
          // TODO: Add authentication token from context
        }
      };

      if (selectedEndpoint.method !== 'GET' && requestPayload) {
        options.body = requestPayload;
      }

      const response = await fetch(
        `http://localhost:8000${selectedEndpoint.path}`,
        options
      );

      const data = await response.json();
      setResponseData({
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        body: data
      });
    } catch (error) {
      setResponseData({
        status: 0,
        statusText: 'Error',
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  // Copy payload to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  // Generate MCP tool config
  const generateMcpConfig = () => {
    if (!selectedEndpoint) return '';

    return JSON.stringify({
      name: selectedEndpoint.mcpTool,
      description: selectedEndpoint.description,
      inputSchema: {
        type: 'object',
        properties: selectedEndpoint.params,
        required: Object.keys(selectedEndpoint.params || {})
      },
      endpoint: {
        method: selectedEndpoint.method,
        path: selectedEndpoint.path,
        requiresAuth: selectedEndpoint.requiresAuth
      }
    }, null, 2);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Zap className="w-8 h-8 text-blue-600" />
                MCP API Explorer
              </h1>
              <p className="text-gray-600 mt-2">
                AI-ERP Integration Hub - Discover, test, and configure MCP tools for AI agents
              </p>
            </div>
            <div className="flex gap-3">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Configure MCP
              </button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="mt-6 flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search endpoints..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={filterModule}
              onChange={(e) => setFilterModule(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {modules.map(module => (
                <option key={module} value={module}>
                  {module === 'all' ? 'All Modules' : module}
                </option>
              ))}
            </select>
          </div>

          {/* Stats */}
          <div className="mt-6 grid grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-900">{endpoints.length}</div>
              <div className="text-sm text-blue-700">Total Endpoints</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-900">{modules.length - 1}</div>
              <div className="text-sm text-green-700">Modules</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-900">
                {endpoints.filter(e => e.method === 'POST').length}
              </div>
              <div className="text-sm text-purple-700">Write Operations</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-900">
                {endpoints.filter(e => e.method === 'GET').length}
              </div>
              <div className="text-sm text-orange-700">Read Operations</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Endpoints List */}
          <div className="col-span-1 bg-white rounded-lg shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Available Endpoints</h2>
              <p className="text-sm text-gray-600 mt-1">
                {filteredEndpoints.length} endpoints
              </p>
            </div>
            <div className="overflow-y-auto" style={{ maxHeight: '600px' }}>
              {filteredEndpoints.map(endpoint => (
                <button
                  key={endpoint.id}
                  onClick={() => {
                    setSelectedEndpoint(endpoint);
                    setRequestPayload(
                      endpoint.samplePayload 
                        ? JSON.stringify(endpoint.samplePayload, null, 2)
                        : '{}'
                    );
                    setResponseData(null);
                  }}
                  className={`w-full text-left p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                    selectedEndpoint?.id === endpoint.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      endpoint.method === 'GET' 
                        ? 'bg-green-100 text-green-800'
                        : endpoint.method === 'POST'
                        ? 'bg-blue-100 text-blue-800'
                        : endpoint.method === 'PUT'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {endpoint.method}
                    </span>
                    <span className="text-xs text-gray-500">{endpoint.module}</span>
                  </div>
                  <div className="font-medium text-gray-900">{endpoint.name}</div>
                  <div className="text-xs text-gray-600 mt-1 font-mono">{endpoint.path}</div>
                </button>
              ))}
            </div>
          </div>

          {/* API Details & Testing */}
          <div className="col-span-2 space-y-6">
            {selectedEndpoint ? (
              <>
                {/* Endpoint Details */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">{selectedEndpoint.name}</h2>
                      <p className="text-gray-600 mt-1">{selectedEndpoint.description}</p>
                    </div>
                    <span className={`text-xs font-semibold px-3 py-1 rounded ${
                      selectedEndpoint.method === 'GET' 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {selectedEndpoint.method}
                    </span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Endpoint Path</label>
                      <div className="mt-1 flex items-center gap-2">
                        <code className="flex-1 bg-gray-100 px-3 py-2 rounded font-mono text-sm">
                          {selectedEndpoint.path}
                        </code>
                        <button
                          onClick={() => copyToClipboard(selectedEndpoint.path)}
                          className="p-2 text-gray-600 hover:text-gray-900"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-700">MCP Tool Name</label>
                      <div className="mt-1 flex items-center gap-2">
                        <code className="flex-1 bg-gray-100 px-3 py-2 rounded font-mono text-sm">
                          {selectedEndpoint.mcpTool}
                        </code>
                        <button
                          onClick={() => copyToClipboard(selectedEndpoint.mcpTool)}
                          className="p-2 text-gray-600 hover:text-gray-900"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {Object.keys(selectedEndpoint.params || {}).length > 0 && (
                      <div>
                        <label className="text-sm font-medium text-gray-700">Parameters</label>
                        <div className="mt-1 bg-gray-100 px-3 py-2 rounded">
                          <pre className="text-sm font-mono">
                            {JSON.stringify(selectedEndpoint.params, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Request Editor */}
                {selectedEndpoint.method !== 'GET' && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                        <FileJson className="w-5 h-5" />
                        Request Payload
                      </h3>
                      <button
                        onClick={() => copyToClipboard(requestPayload)}
                        className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                      >
                        <Copy className="w-4 h-4" />
                        Copy
                      </button>
                    </div>
                    <textarea
                      value={requestPayload}
                      onChange={(e) => setRequestPayload(e.target.value)}
                      className="w-full h-48 p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter JSON payload..."
                    />
                  </div>
                )}

                {/* Execute Button */}
                <button
                  onClick={executeRequest}
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 font-semibold"
                >
                  {loading ? (
                    <>Processing...</>
                  ) : (
                    <>
                      <Play className="w-5 h-5" />
                      Execute Request
                    </>
                  )}
                </button>

                {/* Response */}
                {responseData && (
                  <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                        <Database className="w-5 h-5" />
                        Response
                      </h3>
                      <div className="flex items-center gap-3">
                        <span className={`text-sm px-3 py-1 rounded font-semibold ${
                          responseData.status >= 200 && responseData.status < 300
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {responseData.status} {responseData.statusText}
                        </span>
                        <button
                          onClick={() => copyToClipboard(JSON.stringify(responseData.body, null, 2))}
                          className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                        >
                          <Copy className="w-4 h-4" />
                          Copy
                        </button>
                      </div>
                    </div>
                    <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                      <pre className="text-sm font-mono">
                        {JSON.stringify(responseData.body || responseData, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* MCP Configuration */}
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                      <Code className="w-5 h-5" />
                      MCP Tool Configuration
                    </h3>
                    <button
                      onClick={() => copyToClipboard(generateMcpConfig())}
                      className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <Copy className="w-4 h-4" />
                      Copy Config
                    </button>
                  </div>
                  <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                    <pre className="text-sm font-mono">{generateMcpConfig()}</pre>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <Code className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Select an Endpoint
                </h3>
                <p className="text-gray-600">
                  Choose an endpoint from the list to view details, test requests, and generate MCP configuration
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

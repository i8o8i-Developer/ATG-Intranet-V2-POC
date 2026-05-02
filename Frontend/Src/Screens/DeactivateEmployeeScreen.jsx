import React, { useState } from "react";

import { apiPost } from "../Api/Client.js";
import { formatDateTime, toggleSet } from "./Shared/ScreenUtils.jsx";

export function DeactivateEmployeeScreen({ data, reload }) {
  const [departmentId, setDepartmentId] = useState("");
  const [selected, setSelected] = useState(new Set());
  const employees = (data.employees || []).filter((employee) => !departmentId || String(employee.department) === String(departmentId));

  const deactivateOne = async (employeeId) => {
    await apiPost("/MainApp/deactivate-employee/", { employee_id: employeeId });
    reload();
  };

  const deactivateSelected = async () => {
    await apiPost("/MainApp/deactivate-multiple-employee/", { employee_ids: Array.from(selected) });
    setSelected(new Set());
    reload();
  };

  return <section className="deactivate-page"><h1>Deactivate Employee</h1><div className="deactivate-controls"><select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}><option value="">All Departments</option>{(data.departments || []).map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}</select><button className="primary-button">Show Users</button></div><button className="danger-button" onClick={deactivateSelected}>Deactivate Selected</button><table className="erp-table striped narrow"><thead><tr><th><input type="checkbox" onChange={(event) => setSelected(event.target.checked ? new Set(employees.map((employee) => employee.id)) : new Set())} /></th><th>User Name</th><th>Last Login</th><th>Status</th><th>Action</th></tr></thead><tbody>{employees.map((employee) => <tr key={employee.id}><td><input type="checkbox" checked={selected.has(employee.id)} onChange={() => setSelected(toggleSet(selected, employee.id))} /></td><td>{employee.username || employee.display_name}</td><td>{formatDateTime(employee.profile_payload?.last_login || employee.updated_at)}</td><td>{employee.status}</td><td><button className="warning-button" onClick={() => deactivateOne(employee.id)}>Deactivate</button></td></tr>)}</tbody></table></section>;
}
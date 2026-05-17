import React, { useState } from "react";
import { Modal } from "./Shared/ScreenComponents.jsx";
import "../Styles/DeactivateScreen.css";

import { apiPost } from "../Api/Client.js";
import { formatDateTime, toggleSet } from "./Shared/ScreenUtils.jsx";

export function DeactivateEmployeeScreen({ data, reload }) {
  const [departmentId, setDepartmentId] = useState("");
  const [selected, setSelected] = useState(new Set());
  const [confirmTarget, setConfirmTarget] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [bulkConfirmOpen, setBulkConfirmOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const employees = (data.employees || []).filter((employee) => !departmentId || String(employee.department) === String(departmentId));

  const deactivateOne = async () => {
    if (!confirmTarget) return;
    setBusy(true);
    setError("");
    try {
      await apiPost("/MainApp/deactivate-employee/", { employee_id: confirmTarget, reason });
      setConfirmOpen(false);
      setConfirmTarget(null);
      setReason("");
      reload();
    } catch (err) {
      setError(err?.payload?.detail || err?.message || "Failed To Deactivate Employee.");
    } finally {
      setBusy(false);
    }
  };

  const deactivateSelected = async () => {
    setBusy(true);
    setError("");
    try {
      await apiPost("/MainApp/deactivate-multiple-employee/", { employee_ids: Array.from(selected), reason });
      setSelected(new Set());
      setBulkConfirmOpen(false);
      setReason("");
      reload();
    } catch (err) {
      setError(err?.payload?.detail || err?.message || "Failed To Deactivate Selected Employees.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="Deactivate-Page">
      <h1>Deactivate Employee</h1>

      {error && <div style={{ fontSize: 13, padding: "8px 14px", marginBottom: 12, borderRadius: 6, background: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca" }}>{error}</div>}

      <div className="Deactivate-Controls">
        <select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
          <option value="">All Departments</option>
          {(data.departments || []).map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
        </select>
        <button className="Primary-Button" onClick={() => setDepartmentId(departmentId)}>Show Users</button>
      </div>

      {selected.size > 0 && (
        <div style={{ marginBottom: 12 }}>
          <button className="Danger-Button" onClick={() => setBulkConfirmOpen(true)}>Deactivate Selected ({selected.size})</button>
        </div>
      )}

      <table className="Erp-TableStripedNarrow">
        <thead>
          <tr>
            <th><input type="checkbox" onChange={(event) => setSelected(event.target.checked ? new Set(employees.map((employee) => employee.id)) : new Set())} /></th>
            <th>User Name</th>
            <th>Last Login</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee.id}>
              <td><input type="checkbox" checked={selected.has(employee.id)} onChange={() => setSelected(toggleSet(selected, employee.id))} /></td>
              <td>{employee.username || employee.display_name}</td>
              <td>{formatDateTime(employee.profile_payload?.last_login || employee.updated_at)}</td>
              <td>{employee.status}</td>
              <td>
                {employee.status !== "Exited" && (
                  <button className="Warning-Button" onClick={() => { setConfirmTarget(employee.id); setConfirmOpen(true); }}>Deactivate</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {confirmOpen && (
        <Modal title="Confirm Deactivation" onClose={() => { setConfirmOpen(false); setConfirmTarget(null); setError(""); }}>
          <div style={{ padding: "8px 0" }}>
            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 6, padding: "12px 16px", marginBottom: 16 }}>
              <strong style={{ color: "#dc2626", display: "block", marginBottom: 4 }}>Login Access Will Be Revoked</strong>
              <span style={{ fontSize: 13, color: "#991b1b" }}>
                This User Will No Longer Be Able To Log In To The Intranet. All Their Data (Projects, Tasks, Assignments, Documents, Feedback) Will Remain Intact. This Action Can Be Reversed By An Admin.
              </span>
            </div>
            <label>Reason For Deactivation<textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Optional: Provide a reason..." style={{ width: "100%", marginTop: 4 }} /></label>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button className="Danger-Button" onClick={deactivateOne} disabled={busy}>Confirm Deactivation</button>
            <button className="Soft-Button" onClick={() => { setConfirmOpen(false); setConfirmTarget(null); setError(""); }}>Cancel</button>
          </div>
        </Modal>
      )}

      {bulkConfirmOpen && (
        <Modal title={`Deactivate ${selected.size} Employees`} onClose={() => { setBulkConfirmOpen(false); setError(""); }}>
          <div style={{ padding: "8px 0" }}>
            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 6, padding: "12px 16px", marginBottom: 16 }}>
              <strong style={{ color: "#dc2626", display: "block", marginBottom: 4 }}>Login Access Will Be Revoked For {selected.size} Users</strong>
              <span style={{ fontSize: 13, color: "#991b1b" }}>
                These Users Will No Longer Be Able To Log In To The Intranet. All Their Data Will Remain Intact. This Action Can Be Reversed By An Admin.
              </span>
            </div>
            <label>Reason (Applies To All)<textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Optional: Provide A Reason..." style={{ width: "100%", marginTop: 4 }} /></label>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button className="Danger-Button" onClick={deactivateSelected} disabled={busy}>Confirm Deactivation</button>
            <button className="Soft-Button" onClick={() => { setBulkConfirmOpen(false); setError(""); }}>Cancel</button>
          </div>
        </Modal>
      )}
    </section>
  );
}

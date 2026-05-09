import React, { useEffect, useState } from "react";

import { apiPost } from "../Api/Client.js";
import { Panel, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import { employeeName, findById, formatDate, isCompleted, isoDate } from "./Shared/ScreenUtils.jsx";

export function LeaveApplyScreen({ data, selectedEmployeeId, reload }) {
  const [form, setForm] = useState({ employee_id: selectedEmployeeId || "", leave_type: "Paid", starts_on: isoDate(new Date()), ends_on: isoDate(new Date()), reason: "" });
  const [result, setResult] = useState(null);
  const user = data.me?.user || data.me?.account || data.me || {};
  const isSuperAdmin = Boolean(user.is_superuser || user.isSuperuser || user.is_staff || user.isStaff);
  const currentEmployeeId = selectedEmployeeId || data.me?.employees?.[0]?.id || form.employee_id;
  const allLeaveRows = data.leaveOverview?.results?.length ? data.leaveOverview.results : data.leaveRequests || [];
  const leaveRows = isSuperAdmin
    ? allLeaveRows
    : allLeaveRows.filter((item) => String(item.employee || item.employee_id) === String(currentEmployeeId));
  const visibleBalances = isSuperAdmin
    ? data.leaveBalances || []
    : (data.leaveBalances || []).filter((item) => String(item.employee) === String(currentEmployeeId));
  const employee = findById(data.employees, form.employee_id || selectedEmployeeId) || data.employees?.[0] || {};

  useEffect(() => {
    const fallbackEmployeeId = selectedEmployeeId || data.employees?.[0]?.id;
    if (!form.employee_id && fallbackEmployeeId) setForm((current) => ({ ...current, employee_id: fallbackEmployeeId }));
  }, [selectedEmployeeId, form.employee_id, data.employees]);

  const submit = async () => {
    const response = await apiPost("/MainApp/leave/apply/", form);
    setResult(response);
    reload();
  };

  const reviewLeave = async (id, action) => {
    if (!id) return;
    await apiPost(`/MainApp/LeaveRequests/${id}/${action}/`, action === "reject" ? { reason: "Rejected From Leave Console" } : {});
    reload();
  };

  const leaveTone = (status = "") => {
    const value = String(status).toLowerCase();
    if (["approved", "completed", "done"].includes(value)) return "green";
    if (value === "rejected") return "red";
    return "gold";
  };

  const requestColumns = isSuperAdmin ? ["Employee", "Type", "Starts", "Ends", "Days", "Status", "Action"] : ["Employee", "Type", "Starts", "Ends", "Days", "Status"];
  const requestRows = leaveRows.map((item) => {
    const base = [item.employee_name || employeeName(data, item.employee || item.employee_id), item.leave_type, formatDate(item.starts_on), formatDate(item.ends_on), item.requested_days, <StatusPill key="status" tone={leaveTone(item.status)}>{item.status}</StatusPill>];
    if (isSuperAdmin) {
      base.push(
        <span className="Table-Actions" key="actions">
          <button className="Soft-Button Small" onClick={() => reviewLeave(item.id, "approve")} disabled={String(item.status).toLowerCase() === "approved"}>Approve</button>
          <button className="Soft-Button Small Danger" onClick={() => reviewLeave(item.id, "reject")} disabled={String(item.status).toLowerCase() === "rejected"}>Reject</button>
        </span>,
      );
    }
    return base;
  });

  return (
    <section className="Leave-Screen Screen-Stack">
      <section className="Page-Heading"><div><span>Main App / Leave</span><h1>{isSuperAdmin ? "Leave Console" : "Apply Leave"}</h1></div><StatusPill tone="gold">{leaveRows.filter((item) => !isCompleted(item.status) && String(item.status).toLowerCase() !== "approved").length} Pending</StatusPill></section>
      <section className="Split-Grid Two-One">
        <Panel title="Leave Request" subtitle="Submits To Main App Leave Workflow.">
          <div className="Form-Grid Two">
            <label>Employee{isSuperAdmin ? <select value={form.employee_id} onChange={(event) => setForm({ ...form, employee_id: event.target.value })}>{(data.employees || []).map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select> : <input value={employee.display_name || ""} readOnly />}</label>
            <label>Leave Type<select value={form.leave_type} onChange={(event) => setForm({ ...form, leave_type: event.target.value })}><option>Paid</option><option>Sick</option><option>Casual</option><option>Unpaid</option><option>Comp Off</option></select></label>
            <label>Starts On<input type="date" value={form.starts_on} onChange={(event) => setForm({ ...form, starts_on: event.target.value })} /></label>
            <label>Ends On<input type="date" value={form.ends_on} onChange={(event) => setForm({ ...form, ends_on: event.target.value })} /></label>
          </div>
          <label>Reason<textarea value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} /></label>
          <button className="Primary-Button" onClick={submit} disabled={!form.employee_id || !form.starts_on || !form.ends_on}>Submit Leave</button>
          {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
        </Panel>
        <Panel title="Leave Wallets"><SimpleTable columns={["Employee", "Balance", "Accrued", "Used"]} rows={visibleBalances.slice(0, isSuperAdmin ? 50 : 8).map((item) => [employeeName(data, item.employee), item.balance || item.available_balance || item.amount, item.accrued || "-", item.used || "-"])} /></Panel>
      </section>
      <Panel title="Leave Requests"><SimpleTable columns={requestColumns} rows={requestRows} /></Panel>
    </section>
  );
}
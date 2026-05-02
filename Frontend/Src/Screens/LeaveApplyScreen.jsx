import React, { useEffect, useState } from "react";

import { apiPost } from "../Api/Client.js";
import { Panel, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import { employeeName, findById, formatDate, isCompleted, isoDate } from "./Shared/ScreenUtils.jsx";

export function LeaveApplyScreen({ data, selectedEmployeeId, reload }) {
  const [form, setForm] = useState({ employee_id: selectedEmployeeId || "", leave_type: "Paid", starts_on: isoDate(new Date()), ends_on: isoDate(new Date()), reason: "" });
  const [result, setResult] = useState(null);
  const leaveRows = data.leaveOverview?.results?.length ? data.leaveOverview.results : data.leaveRequests || [];
  const employee = findById(data.employees, form.employee_id || selectedEmployeeId) || data.employees?.[0] || {};

  useEffect(() => {
    if (!form.employee_id && selectedEmployeeId) setForm((current) => ({ ...current, employee_id: selectedEmployeeId }));
  }, [selectedEmployeeId, form.employee_id]);

  const submit = async () => {
    const response = await apiPost("/MainApp/leave/apply/", form);
    setResult(response);
    reload();
  };

  return (
    <section className="leave-screen screen-stack">
      <section className="page-heading"><div><span>MainApp / Leave</span><h1>Apply Leave</h1></div><StatusPill tone="gold">{leaveRows.filter((item) => !isCompleted(item.status)).length} Pending</StatusPill></section>
      <section className="split-grid two-one">
        <Panel title="Leave Request" subtitle="Submits To MainApp Leave Workflow.">
          <div className="form-grid two">
            <label>Employee<input value={employee.display_name || ""} readOnly /></label>
            <label>Leave Type<select value={form.leave_type} onChange={(event) => setForm({ ...form, leave_type: event.target.value })}><option>Paid</option><option>Sick</option><option>Casual</option><option>Unpaid</option><option>Comp Off</option></select></label>
            <label>Starts On<input type="date" value={form.starts_on} onChange={(event) => setForm({ ...form, starts_on: event.target.value })} /></label>
            <label>Ends On<input type="date" value={form.ends_on} onChange={(event) => setForm({ ...form, ends_on: event.target.value })} /></label>
          </div>
          <label>Reason<textarea value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} /></label>
          <button className="primary-button" onClick={submit} disabled={!form.employee_id || !form.starts_on || !form.ends_on}>Submit Leave</button>
          {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
        </Panel>
        <Panel title="Leave Wallets"><SimpleTable columns={["Employee", "Balance", "Accrued", "Used"]} rows={(data.leaveBalances || []).slice(0, 8).map((item) => [employeeName(data, item.employee), item.balance || item.available_balance || item.amount, item.accrued || "-", item.used || "-"])} /></Panel>
      </section>
      <Panel title="Leave Requests"><SimpleTable columns={["Employee", "Type", "Starts", "Ends", "Days", "Status"]} rows={leaveRows.map((item) => [item.employee_name || employeeName(data, item.employee || item.employee_id), item.leave_type, formatDate(item.starts_on), formatDate(item.ends_on), item.requested_days, <StatusPill key="status" tone={isCompleted(item.status) ? "green" : item.status === "Rejected" ? "red" : "gold"}>{item.status}</StatusPill>])} /></Panel>
    </section>
  );
}
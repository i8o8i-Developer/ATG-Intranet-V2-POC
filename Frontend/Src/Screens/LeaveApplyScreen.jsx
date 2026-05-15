import React, { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import "../Styles/LeaveScreen.css";

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
  const isDirectReportLeave = (item) => (data.employees || []).some((employee) => (
    String(employee.id) === String(item.employee || item.employee_id)
    && String(employee.manager || employee.manager_id) === String(currentEmployeeId)
  ));
  const isOwnLeave = (item) => String(item.employee || item.employee_id) === String(currentEmployeeId);
  const canReviewLeave = (item) => isSuperAdmin || (isDirectReportLeave(item) && String(item.employee || item.employee_id) !== String(currentEmployeeId));
  const canReviewAnyLeave = isSuperAdmin || allLeaveRows.some(canReviewLeave);
  const leaveRows = isSuperAdmin
    ? allLeaveRows
    : allLeaveRows.filter((item) => isOwnLeave(item) || isDirectReportLeave(item));
  const visibleBalances = isSuperAdmin
    ? data.leaveBalances || []
    : (data.leaveBalances || []).filter((item) => String(item.employee) === String(currentEmployeeId));
  const employee = findById(data.employees, form.employee_id || selectedEmployeeId) || data.employees?.[0] || {};
  const [calMonth, setCalMonth] = useState(new Date().getMonth());
  const [calYear, setCalYear] = useState(new Date().getFullYear());

  const calendarDays = useMemo(() => {
    const days = [];
    const firstDay = new Date(calYear, calMonth, 1).getDay();
    const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
    const today = new Date();
    for (let i = 0; i < firstDay; i++) days.push(null);
    for (let d = 1; d <= daysInMonth; d++) {
      const date = new Date(calYear, calMonth, d);
      const iso = isoDate(date);
      const leaves = (data.leaveRequests || []).filter((lr) => iso >= String(lr.starts_on).slice(0, 10) && iso <= String(lr.ends_on).slice(0, 10));
      days.push({ day: d, iso, isToday: iso === isoDate(today), isPast: date < new Date(today.getFullYear(), today.getMonth(), today.getDate()), leaves });
    }
    return days;
  }, [calMonth, calYear, data.leaveRequests]);

  useEffect(() => {
    const fallbackEmployeeId = selectedEmployeeId || data.employees?.[0]?.id;
    if (!form.employee_id && fallbackEmployeeId) setForm((current) => ({ ...current, employee_id: fallbackEmployeeId }));
  }, [selectedEmployeeId, form.employee_id, data.employees]);

  const submit = async () => {
    const response = await apiPost("/MainApp/leave/apply/", form);
    setResult(response);
    reload(["leaveRequests", "leaveBalances", "leaveOverview", "notifications", "employees"]);
  };

  const reviewLeave = async (id, action) => {
    if (!id) return;
    await apiPost(`/MainApp/LeaveRequests/${id}/${action}/`, action === "reject" ? { reason: "Rejected From Leave Console" } : {});
    reload(["leaveRequests", "leaveBalances", "leaveOverview", "notifications", "employees"]);
  };

  const leaveTone = (status = "") => {
    const value = String(status).toLowerCase();
    if (["approved", "completed", "done"].includes(value)) return "green";
    if (value === "rejected") return "red";
    return "gold";
  };

  const requestColumns = canReviewAnyLeave ? ["Employee", "Type", "Starts", "Ends", "Days", "Status", "Action"] : ["Employee", "Type", "Starts", "Ends", "Days", "Status"];
  const requestRows = leaveRows.map((item) => {
    const base = [item.employee_name || employeeName(data, item.employee || item.employee_id), item.leave_type, formatDate(item.starts_on), formatDate(item.ends_on), item.requested_days, <StatusPill key="status" tone={leaveTone(item.status)}>{item.status}</StatusPill>];
    if (canReviewAnyLeave) {
      base.push(
        <span className="Table-Actions" key="actions">
          {canReviewLeave(item) && <button className="Soft-Button Small" onClick={() => reviewLeave(item.id, "approve")} disabled={String(item.status).toLowerCase() === "approved"}>Approve</button>}
          {canReviewLeave(item) && <button className="Soft-Button Small Danger" onClick={() => reviewLeave(item.id, "reject")} disabled={String(item.status).toLowerCase() === "rejected"}>Reject</button>}
        </span>,
      );
    }
    return base;
  });

  return (
    <section className="Leave-Screen Screen-Stack">
      <section className="Page-Heading"><div><span>Main App / Leave</span><h1>{canReviewAnyLeave ? "Leave Console" : "Apply Leave"}</h1></div><StatusPill tone="gold">{leaveRows.filter((item) => !isCompleted(item.status) && String(item.status).toLowerCase() !== "approved").length} Pending</StatusPill></section>
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
          {result && <div className="error-banner">{result?.detail || result?.message || (result?.status === "Success" ? "Leave Submitted Successfully." : "Leave Submission Completed.")}</div>}
        </Panel>
        <Panel title="Leave Wallets"><SimpleTable columns={["Employee", "Balance", "Accrued", "Used"]} rows={visibleBalances.slice(0, isSuperAdmin ? 50 : 8).map((item) => [employeeName(data, item.employee), item.balance || item.available_balance || item.amount, item.accrued || "-", item.used || "-"])} /></Panel>
      </section>
      <Panel title="Leave Calendar" subtitle={`${calMonth + 1}/${calYear}`}
        right={
          <span style={{ display: "flex", gap: 6 }}>
            <button className="Soft-Button Small" onClick={() => { if (calMonth === 0) { setCalMonth(11); setCalYear(calYear - 1); } else setCalMonth(calMonth - 1); }}><ChevronLeft size={14} /></button>
            <button className="Soft-Button Small" onClick={() => { if (calMonth === 11) { setCalMonth(0); setCalYear(calYear + 1); } else setCalMonth(calMonth + 1); }}><ChevronRight size={14} /></button>
          </span>
        }
      >
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 4, textAlign: "center" }}>
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => <strong key={d} style={{ fontSize: 11, color: "#64748b", padding: "4px 0" }}>{d}</strong>)}
          {calendarDays.map((day, i) => !day ? <span key={i} /> : (
            <div key={i} style={{ padding: "6px 0", borderRadius: 6, fontSize: 12, fontWeight: day.isToday ? 700 : 400, background: day.isToday ? "#eef2ff" : day.leaves.length > 0 ? "#fef2f2" : "transparent", color: day.leaves.length > 0 ? "#dc2626" : day.isPast ? "#94a3b8" : "#0f172a" }}>
              <div>{day.day}</div>
              {day.leaves.length > 0 && <div style={{ fontSize: 9, color: "#dc2626" }}>{day.leaves.length} leave{day.leaves.length > 1 ? "s" : ""}</div>}
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Leave Requests"><SimpleTable columns={requestColumns} rows={requestRows} /></Panel>
    </section>
  );
}

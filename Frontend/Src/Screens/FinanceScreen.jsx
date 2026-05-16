import React, { useState, useMemo } from "react";
import { Check, X, Search as SearchIcon, ChevronLeft, ChevronRight } from "lucide-react";
import "../Styles/FinanceScreen.css";

import { apiGet, apiPost } from "../Api/Client.js";
import { money } from "./Shared/ScreenUtils.jsx";

const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];

export function FinanceScreen({ data, reload }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDeptNames, setSelectedDeptNames] = useState(new Set());
  const [showApprovedOnly, setShowApprovedOnly] = useState(false);
  const [bulkSelected, setBulkSelected] = useState(new Set());
  const [monthIndex, setMonthIndex] = useState(new Date().getMonth());
  const [year, setYear] = useState(new Date().getFullYear());
  const [localRows, setLocalRows] = useState(null);
  const [prevRows, setPrevRows] = useState(null);
  const [prevMonthLabel, setPrevMonthLabel] = useState("");
  const [approvalData, setApprovalData] = useState(null);
  const [error, setError] = useState("");

  const rows = localRows || data.financeRows || [];
  const departments = data.financeDashboard?.departments || data.departments || [];

  const filtered = useMemo(() => {
    return rows.filter((row) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const name = (row.display_name || row.username || "").toLowerCase();
        if (!name.includes(q)) return false;
      }
      const rowDept = String(row.department || row.department_name || "").toLowerCase();
      if (selectedDeptNames.size > 0 && !selectedDeptNames.has(rowDept)) return false;
      if (showApprovedOnly) {
        const status = String(row.manager_status || row.finance_status || "").toLowerCase();
        if (status !== "approved") return false;
      }
      return true;
    });
  }, [rows, searchQuery, selectedDeptNames, showApprovedOnly]);

  const toggleDeptName = (name) => {
    const key = String(name || "").toLowerCase();
    setSelectedDeptNames((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const fetchMonth = (m, y) => apiGet(`/FinanceAndPayroll/payments/?pay_month=${m + 1}&month_name=${MONTH_NAMES[m]}&year=${y}`).then((p) => p?.user_list || []);

  const changeMonth = (delta) => {
    let m = monthIndex + delta;
    let y = year;
    if (m < 0) { m = 11; y -= 1; }
    if (m > 11) { m = 0; y += 1; }
    setMonthIndex(m);
    setYear(y);
    fetchMonth(m, y).then((list) => setLocalRows(list));
    // 
    let pm = m - 1;
    let py = y;
    if (pm < 0) { pm = 11; py -= 1; }
    fetchMonth(pm, py).then((list) => { setPrevRows(list); setPrevMonthLabel(MONTH_NAMES[pm]); });
  };

  const openApproval = (row) => setApprovalData({ ...row, bonus: "0", note: "" });
  const submitApproval = async () => {
    if (!approvalData) return;
    setError("");
    try {
      await apiPost("/FinanceAndPayroll/payment-approval/", {
        employee: approvalData.id, userid: approvalData.user_id,
        normalPay: approvalData.base_pay || 0, bonus: Number(approvalData.bonus) || 0,
        bounty: approvalData.bounty || 0, payNote: approvalData.note || "",
        show_month: monthIndex + 1, show_year: year,
      });
      reload(["financeDashboard", "financeRows", "payrollRuns", "payrollLineItems", "payslipDocuments"]);
      setApprovalData(null);
    } catch (err) {
      setError(err?.payload?.detail || err?.message || "Approval failed.");
    }
  };

  return (
    <section className="Finance-Screen">
      <aside>
        <h2>All<br />Teams</h2>
        {departments.map((department) => {
            const deptKey = String(department.name || department.code || department.id || "").toLowerCase();
            return (
              <label key={department.id}>
                <input type="checkbox" checked={selectedDeptNames.has(deptKey)} onChange={() => toggleDeptName(department.name || department.code || "")} />
                {department.name}
              </label>
            );
          })}
      </aside>
      <main>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
          <h1 style={{ margin: 0 }}>Payroll</h1>
          <button className="Soft-Button Small" onClick={() => changeMonth(-1)}><ChevronLeft size={16} /></button>
          <strong style={{ minWidth: 140, textAlign: "center" }}>{MONTH_NAMES[monthIndex]} {year}</strong>
          <button className="Soft-Button Small" onClick={() => changeMonth(1)}><ChevronRight size={16} /></button>
          {prevRows && prevRows.length > 0 && (() => {
            const currTotal = filtered.reduce((s, r) => s + Number(r.base_pay || 0) + Number(r.bonus || 0), 0);
            const prevTotal = prevRows.reduce((s, r) => s + Number(r.base_pay || 0) + Number(r.bonus || 0), 0);
            const diff = currTotal - prevTotal;
            const pct = prevTotal ? Math.round((diff / prevTotal) * 100) : 0;
            return <span style={{ fontSize: 12, color: diff >= 0 ? "#059669" : "#dc2626", fontWeight: 600 }}>vs {prevMonthLabel}: {diff >= 0 ? "+" : ""}₹{diff.toLocaleString()} ({pct}%)</span>;
          })()}
        </div>
        <div className="Finance-Search">
          <input placeholder="Search By Name" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
          <button className="Primary-Button" onClick={() => { const inp = document.querySelector(".Finance-Search input"); if (inp) inp.focus(); }}><SearchIcon size={16} /> Search</button>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <input type="checkbox" checked={showApprovedOnly} onChange={() => setShowApprovedOnly((v) => !v)} />
            Show Approved Only
          </label>
          {bulkSelected.size > 0 && (
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <strong style={{ fontSize: 12 }}>{bulkSelected.size} selected</strong>
              <button className="Primary-Button Small" onClick={async () => {
                const ids = Array.from(bulkSelected);
                for (const id of ids) {
                  const row = filtered.find((r) => String(r.id) === String(id));
                  if (row) try { await apiPost("/FinanceAndPayroll/payment-approval/", { employee: row.id, normalPay: row.base_pay || 0, bonus: Number(row.bonus || 0), bounty: row.bounty || 0 }); } catch {}
                }
                setBulkSelected(new Set());
                reload(["financeDashboard", "financeRows", "payrollRuns", "payrollLineItems"]);
              }}>Approve All Selected</button>
              <button className="Soft-Button Small" onClick={() => setBulkSelected(new Set())}>Clear</button>
            </span>
          )}
        </div>
        <table className="Erp-Table">
          <thead>
            <tr>
              <th><input type="checkbox" checked={bulkSelected.size === filtered.length && filtered.length > 0} onChange={() => { if (bulkSelected.size === filtered.length) setBulkSelected(new Set()); else setBulkSelected(new Set(filtered.map((r) => String(r.id)))); }} /></th>
              <th>Name</th><th>Department</th><th>Status</th><th>Bank</th>
              <th>Base Pay</th><th>Bonus</th><th>Bounty</th><th>Total</th><th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => {
              const isPaid = String(row.manager_status || row.finance_status || "").toLowerCase() === "approved";
              return (
                <tr key={row.id}>
                  <td><input type="checkbox" checked={bulkSelected.has(String(row.id))} onChange={() => setBulkSelected((prev) => { const next = new Set(prev); if (next.has(String(row.id))) next.delete(String(row.id)); else next.add(String(row.id)); return next; })} /></td>
                  <td>{row.display_name || row.username}</td>
                  <td>{row.department}</td>
                  <td className={isPaid ? "" : "Danger-Text"}>{row.manager_status || row.finance_status || "Pending"}</td>
                  <td>{(data.bankAccounts || []).some((a) => String(a.employee) === String(row.id) && a.verification_status === "Verified") ? <Check className="Ok-Icon" /> : <X className="Bad-Icon" />}</td>
                  <td>{money(row.base_pay)}</td>
                  <td>{money(row.bonus)}</td>
                  <td>{money(row.bounty || row.task_bounty)}</td>
                  <td>{money((row.base_pay || 0) + (row.bonus || 0) + (row.bounty || row.task_bounty || 0))}</td>
                  <td>
                    {isPaid ? (
                      <span style={{ color: "#10b981", fontWeight: 600 }}>Approved</span>
                    ) : (
                      <button className="Primary-Button Small" onClick={() => openApproval(row)}>Approve</button>
                    )}
                  </td>
                </tr>
              );
            })}
            {!filtered.length && <tr><td colSpan="10" style={{ textAlign: "center", padding: "24px", color: "#94a3b8" }}>No Payroll Entries Found.</td></tr>}
          </tbody>
        </table>
      </main>

      {approvalData && (
        <div className="Modal-Backdrop" onClick={() => setApprovalData(null)}>
          <section className="Modal" onClick={(e) => e.stopPropagation()} style={{ width: "min(500px, calc(100vw - 56px))" }}>
            <div className="Modal-Body">
              <h2>Approve Payroll</h2>
              <p style={{ marginBottom: 16, color: "#64748b" }}>{approvalData.display_name || approvalData.username} — {MONTH_NAMES[monthIndex]} {year}</p>
              <label>Base Pay<input value={money(approvalData.base_pay)} readOnly /></label>
              <label>Bonus<input type="number" min="0" value={approvalData.bonus} onChange={(e) => setApprovalData({ ...approvalData, bonus: e.target.value })} /></label>
              <label>Note<textarea value={approvalData.note} onChange={(e) => setApprovalData({ ...approvalData, note: e.target.value })} placeholder="Approval Note..." /></label>
              {error && <div className="error-banner">{error}</div>}
              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <button className="Primary-Button" onClick={submitApproval}>Approve & Generate Payslip</button>
                <button className="Soft-Button" onClick={() => setApprovalData(null)}>Cancel</button>
              </div>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
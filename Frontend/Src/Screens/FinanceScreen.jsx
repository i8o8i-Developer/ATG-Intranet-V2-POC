import React, { useState, useMemo } from "react";
import { Check, X, Search as SearchIcon } from "lucide-react";
import "../Styles/FinanceScreen.css";

import { apiPost } from "../Api/Client.js";
import { money } from "./Shared/ScreenUtils.jsx";

export function FinanceScreen({ data, reload }) {
  const rows = data.financeRows || [];
  const departments = data.financeDashboard?.departments || data.departments || [];
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDepts, setSelectedDepts] = useState(new Set());
  const [showApprovedOnly, setShowApprovedOnly] = useState(false);

  const filtered = useMemo(() => {
    return rows.filter((row) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const name = (row.display_name || row.username || "").toLowerCase();
        if (!name.includes(q)) return false;
      }
      if (selectedDepts.size > 0 && !selectedDepts.has(String(row.department_id || row.department))) return false;
      if (showApprovedOnly) {
        const status = String(row.manager_status || row.finance_status || "").toLowerCase();
        if (status !== "approved") return false;
      }
      return true;
    });
  }, [rows, searchQuery, selectedDepts, showApprovedOnly]);

  const toggleDept = (deptId) => {
    setSelectedDepts((prev) => {
      const next = new Set(prev);
      if (next.has(String(deptId))) next.delete(String(deptId));
      else next.add(String(deptId));
      return next;
    });
  };

  const approve = async (row) => {
    await apiPost("/FinanceAndPayroll/payment-approval/", { employee: row.id, userid: row.user_id, normalPay: row.base_pay || 0, show_month: data.financeDashboard?.month, show_year: data.financeDashboard?.year });
    reload(["financeDashboard", "financeRows", "payrollRuns", "payrollLineItems"]);
  };

  return (
    <section className="Finance-Screen">
      <aside>
        <h2>All<br />Teams</h2>
        {departments.map((department) => (
          <label key={department.id}>
            <input type="checkbox" checked={selectedDepts.has(String(department.id))} onChange={() => toggleDept(department.id)} />
            {department.name}
          </label>
        ))}
      </aside>
      <main>
        <h1>Showing Payroll For {data.financeDashboard?.month_name || "May"}</h1>
        <div className="Finance-Search">
          <input placeholder="Search By Name" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
          <button className="Primary-Button" onClick={() => {}}><SearchIcon size={16} /> Search</button>
        </div>
        <label>
          <input type="checkbox" checked={showApprovedOnly} onChange={() => setShowApprovedOnly((v) => !v)} />
          {" "}Show Approved
        </label>
        <table className="Erp-Table">
          <thead>
            <tr>
              <th>Name</th><th>Department</th><th>Days Left</th><th>Manager Status</th>
              <th>Bank Details</th><th>Base Pay</th><th>Per Task Pay</th><th>Bounty</th>
              <th>Extra Payment</th><th>Total</th><th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id}>
                <td>{row.display_name || row.username}</td>
                <td>{row.department}</td>
                <td>---</td>
                <td className={String(row.manager_status || "").toLowerCase() === "approved" ? "" : "Danger-Text"}>{row.manager_status}</td>
                <td>{(data.bankAccounts || []).some((account) => String(account.employee) === String(row.id)) ? <Check className="Ok-Icon" /> : <X className="Bad-Icon" />}</td>
                <td>{money(row.base_pay)}</td>
                <td>{money(row.pay_per_task)}</td>
                <td>0</td>
                <td><input className="Mini-Input" defaultValue="0" /></td>
                <td>{money(row.base_pay)}</td>
                <td><button className="Primary-Button Small" onClick={() => approve(row)}>Approve</button></td>
              </tr>
            ))}
            {!filtered.length && <tr><td colSpan="11" style={{ textAlign: "center", padding: "24px", color: "#94a3b8" }}>No Payroll Entries Found.</td></tr>}
          </tbody>
        </table>
      </main>
    </section>
  );
}
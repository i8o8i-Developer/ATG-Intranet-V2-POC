import React, { useMemo, useState } from "react";
import { Download, AlertTriangle } from "lucide-react";
import "../Styles/PayrollScreen.css";

import { Panel, SimpleTable, StatCard } from "./Shared/ScreenComponents.jsx";
import { downloadCsv, money } from "./Shared/ScreenUtils.jsx";

// 
const PTRC_THRESHOLD = 25000;
const PTRC_AMOUNT = 200;
const DAYS_IN_MONTH = 30;

function calcNormalPay(row) {
  const basePay = Number(row.base_pay || 0);
  const payType = String(row.pay_type || "").toLowerCase();
  const payPerTask = Number(row.pay_per_task || 0);
  const bounty = Number(row.bounty || row.task_bounty || 0);

  if (payType === "performance based" || payType === "performance") {
    const tasks = Number(row.task_count || bounty || 0);
    return tasks * (payPerTask || 100);
  }
  if (payType === "fixed") {
    const leaves = Number(row.leaves || row.leaves_taken || 0);
    const bench = Number(row.bench_days || 0);
    const absence = Math.min(leaves + bench, DAYS_IN_MONTH);
    const deduction = Math.round((absence / DAYS_IN_MONTH) * basePay);
    return Math.max(0, basePay - deduction);
  }
  if (payType === "full-time" || payType === "monthly") {
    return basePay;
  }
  return basePay; // Default / Not Assigned
}

function calcPTrc(normalPay, bonus) {
  return (normalPay + (bonus || 0)) >= PTRC_THRESHOLD ? PTRC_AMOUNT : 0;
}

function statusLabel(code) {
  const map = { APV: "Approved", RVK: "Revoked", PTP: "Postponed", PD: "Paid", NA: "N/A" };
  return map[code] || code || "Pending";
}

export function PayrollDownloadsScreen({ data }) {
  const sheet = data.financeDashboard?.user_list || [];
  const paySnapshots = data.paymentSnapshots || [];
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [employmentType, setEmploymentType] = useState("all");

  const departments = useMemo(() => ["all", ...new Set(sheet.map((r) => r.department).filter(Boolean))], [sheet]);
  const employmentTypes = useMemo(() => ["all", ...new Set(sheet.map((r) => r.employment_type).filter(Boolean))], [sheet]);

  // 
  const rows = useMemo(() => {
    return sheet
      .filter((row) => {
        const term = `${row.display_name || ""} ${row.username || ""} ${row.department || ""}`.toLowerCase();
        if (search && !term.includes(search.toLowerCase())) return false;
        if (department !== "all" && row.department !== department) return false;
        if (employmentType !== "all" && row.employment_type !== employmentType) return false;
        return true;
      })
      .map((row) => {
        const snapshot = paySnapshots.find((s) => String(s.employee) === String(row.id));

        const normalPay = snapshot ? Number(snapshot.normal_pay || 0) : calcNormalPay(row);
        const bonus = snapshot ? Number(snapshot.bonus || 0) : Number(row.bonus || 0);
        const totalPay = normalPay + bonus;
        const ptrc = snapshot ? Number(snapshot.deduction || 0) : calcPTrc(normalPay, bonus);
        const netSalary = totalPay - ptrc;

        const mStatus = snapshot?.manager_status || row.manager_status || "NA";
        const fStatus = snapshot?.finance_status || row.finance_status || "NA";

        return {
          id: row.id,
          name: row.display_name || row.username || "-",
          username: row.username || "-",
          department: row.department || "-",
          empType: row.employment_type || "-",
          payType: row.pay_type || "Not Assigned",
          basePay: normalPay,
          bonus,
          payPerTask: Number(row.pay_per_task || 0),
          bounty: Number(row.bounty || row.task_bounty || 0),
          totalPay,
          ptrc,
          netSalary,
          mStatus,
          fStatus,
          taskCount: Number(row.task_count || 0),
          payFor: row.pay_for || "ATG",
        };
      });
  }, [sheet, paySnapshots, search, department, employmentType]);

  const totalEmployees = rows.length;
  const totalGross = rows.reduce((s, r) => s + r.totalPay, 0);
  const totalDeductions = rows.reduce((s, r) => s + r.ptrc, 0);
  const totalNet = rows.reduce((s, r) => s + r.netSalary, 0);
  const monthLabel = data.financeDashboard?.month_name || "Current";
  const yearLabel = data.financeDashboard?.year || new Date().getFullYear();

  const downloadSheet = () =>
    downloadCsv(
      `Payroll_${monthLabel}_${yearLabel}.csv`,
      [
        "Employee", "Username", "Department", "Employment Type", "Pay Type",
        "Pay Per Task", "Task Count", "Base Pay", "Bonus", "Bounty",
        "Total Pay", "PTRC Deduction", "Net Salary",
        "Manager Status", "Finance Status", "Pay For",
      ],
      rows.map((r) => [
        r.name, r.username, r.department, r.empType, r.payType,
        r.payPerTask, r.taskCount, r.basePay, r.bonus, r.bounty,
        r.totalPay, r.ptrc, r.netSalary,
        statusLabel(r.mStatus), statusLabel(r.fStatus), r.payFor,
      ]),
    );

  return (
    <section className="Payroll-Download-Screen Screen-Stack">
      <section className="Page-Heading">
        <div>
          <span>Finance / Payroll</span>
          <h1>Payroll Downloads — {monthLabel} {yearLabel}</h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b" }}>
            Full-time = Base Pay · Fixed = Base − ((Leaves+Bench)/30 × Base) · Performance = Tasks × Pay/Task · PTRC = ₹200 if Total ≥ ₹25,000
          </p>
        </div>
        <div className="Button-Row">
          <button className="Primary-Button" onClick={downloadSheet}><Download size={16} /> Download CSV</button>
        </div>
      </section>

      <div className="Stat-Grid Four">
        <StatCard label="Employees" value={totalEmployees} />
        <StatCard label="Total Gross" value={`₹${totalGross.toLocaleString()}`} />
        <StatCard label="Total PTRC" value={`₹${totalDeductions.toLocaleString()}`} />
        <StatCard label="Total Net" value={`₹${totalNet.toLocaleString()}`} />
      </div>

      <Panel title="Filters" subtitle="Filter Before Download">
        <div className="Form-Grid Three">
          <label>Search<input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Name, Username, Department" /></label>
          <label>Department<select value={department} onChange={(e) => setDepartment(e.target.value)}>{departments.map((item) => <option key={item} value={item}>{item === "all" ? "All Departments" : item}</option>)}</select></label>
          <label>Employment Type<select value={employmentType} onChange={(e) => setEmploymentType(e.target.value)}>{employmentTypes.map((item) => <option key={item} value={item}>{item === "all" ? "All Types" : item}</option>)}</select></label>
        </div>
      </Panel>

      <Panel
        title="Payroll Sheet"
        subtitle={`${rows.length} employees · ₹${totalNet.toLocaleString()} projected net payout`}
        right={<span className="Soft-Button Small" onClick={downloadSheet}><Download size={13} /> CSV</span>}
      >
        <SimpleTable
          columns={["Employee", "Dept", "Type", "Pay Type", "Base Pay", "Bonus", "Total", "PTRC", "Net", "Manager", "Finance"]}
          rows={rows.map((r) => [
            r.name,
            r.department,
            r.empType,
            <span key={`pt-${r.id}`} style={{ fontSize: 11, padding: "2px 6px", borderRadius: 4, background: r.payType === "Not Assigned" ? "#fef2f2" : "#f0fdf4", color: r.payType === "Not Assigned" ? "#dc2626" : "#16a34a" }}>{r.payType}</span>,
            `₹${r.basePay.toLocaleString()}`,
            `₹${r.bonus.toLocaleString()}`,
            `₹${r.totalPay.toLocaleString()}`,
            r.ptrc > 0 ? <span key={`ptrc-${r.id}`} style={{ color: "#dc2626", fontWeight: 600 }}>-₹{r.ptrc}</span> : "—",
            <strong key={`net-${r.id}`} style={{ color: "#059669" }}>₹{r.netSalary.toLocaleString()}</strong>,
            <span key={`ms-${r.id}`} style={{ fontSize: 11, padding: "2px 6px", borderRadius: 4, background: r.mStatus === "APV" || r.mStatus === "Approved" ? "#f0fdf4" : "#fefce8", color: r.mStatus === "APV" || r.mStatus === "Approved" ? "#16a34a" : "#ca8a04" }}>{statusLabel(r.mStatus)}</span>,
            <span key={`fs-${r.id}`} style={{ fontSize: 11, padding: "2px 6px", borderRadius: 4, background: r.fStatus === "APV" || r.fStatus === "Approved" ? "#f0fdf4" : "#fefce8", color: r.fStatus === "APV" || r.fStatus === "Approved" ? "#16a34a" : "#ca8a04" }}>{statusLabel(r.fStatus)}</span>,
          ])}
        />
      </Panel>

      <section className="Split-Grid">
        <Panel title="Pay Periods">
          <SimpleTable columns={["Name", "Starts", "Ends", "Status"]} rows={(data.payPeriods || []).map((item) => [item.name, item.starts_on, item.ends_on, item.status])} />
        </Panel>
        <Panel title="Payslip Documents">
          <SimpleTable columns={["ID", "Line", "Status", "Storage"]} rows={(data.payslipDocuments || []).map((item) => [item.id, item.payroll_line_item, item.status, item.storage_reference || "-"])} />
        </Panel>
      </section>
    </section>
  );
}

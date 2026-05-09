import React, { useMemo, useState } from "react";
import { Download } from "Lucide-React";

import { Panel, SimpleTable, StatCard } from "./Shared/ScreenComponents.jsx";
import { downloadCsv, employeeName, money } from "./Shared/ScreenUtils.jsx";

export function PayrollDownloadsScreen({ data }) {
  const sheet = data.financeDashboard?.user_list || [];
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [employmentType, setEmploymentType] = useState("all");

  const departments = useMemo(() => ["all", ...new Set(sheet.map((row) => row.department).filter(Boolean))], [sheet]);
  const employmentTypes = useMemo(() => ["all", ...new Set(sheet.map((row) => row.employment_type).filter(Boolean))], [sheet]);

  const filtered = sheet.filter((row) => {
    const term = `${row.display_name || ""} ${row.username || ""} ${row.department || ""}`.toLowerCase();
    if (search && !term.includes(search.toLowerCase())) return false;
    if (department !== "all" && row.department !== department) return false;
    if (employmentType !== "all" && row.employment_type !== employmentType) return false;
    return true;
  });

  const totalGross = filtered.reduce((sum, row) => sum + Number(row.base_pay || 0), 0);
  const monthLabel = data.financeDashboard?.month_name || "Current";
  const yearLabel = data.financeDashboard?.year || new Date().getFullYear();

  const downloadSheet = () =>
    downloadCsv(
      `payroll-${monthLabel}-${yearLabel}.csv`,
      ["Employee", "Username", "Department", "EmploymentType", "PayType", "BasePay", "PayPerTask", "ManagerStatus", "FinanceStatus", "PaymentStatus"],
      filtered.map((row) => [
        row.display_name,
        row.username,
        row.department,
        row.employment_type,
        row.pay_type || "-",
        row.base_pay || 0,
        row.pay_per_task || 0,
        row.manager_status || "Pending",
        row.finance_status || "Pending",
        row.payment_status || "-",
      ]),
    );

  const downloadPayslipIndex = () =>
    downloadCsv(
      "payslip-index.csv",
      ["Payslip", "Employee", "LineItem", "Status", "StorageReference"],
      (data.payslipDocuments || []).map((item) => {
        const line = (data.payrollLineItems || []).find((row) => String(row.id) === String(item.payroll_line_item)) || {};
        return [item.id, employeeName(data, line.employee), item.payroll_line_item, item.status, item.storage_reference || "-"];
      }),
    );

  const downloadOrders = () =>
    downloadCsv(
      "payment-orders.csv",
      ["Provider", "Employee", "Amount", "Currency", "Status", "Receipt"],
      (data.paymentOrders || []).map((item) => [item.provider, employeeName(data, item.employee), item.amount, item.currency, item.status, item.receipt || "-"]),
    );

  return (
    <section className="Payroll-Download-ScreenScreen-Stack">
      <section className="Page-Heading">
        <div>
          <span>Finance / Payroll</span>
          <h1>Payroll Downloads — {monthLabel} {yearLabel}</h1>
        </div>
        <div className="Button-Row">
          <button className="Primary-Button" onClick={downloadSheet}><Download size={16} /> Download Full Sheet</button>
          <button className="Outline-Button" onClick={downloadPayslipIndex}><Download size={16} /> Payslip Index</button>
          <button className="Outline-Button" onClick={downloadOrders}><Download size={16} /> Payment Orders</button>
        </div>
      </section>

      <div className="Stat-GridFour">
        <StatCard label="Employees" value={filtered.length} />
        <StatCard label="Gross (BasePay)" value={money(totalGross)} />
        <StatCard label="PayPeriods" value={(data.payPeriods || []).length} />
        <StatCard label="Payslips" value={(data.payslipDocuments || []).length} />
      </div>

      <Panel title="Filters" subtitle="FilterTheBulkSheetBeforeDownload.">
        <div className="Form-GridThree">
          <label>Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name, Username, Department" /></label>
          <label>Department<select value={department} onChange={(event) => setDepartment(event.target.value)}>{departments.map((item) => <option key={item} value={item}>{item === "all" ? "AllDepartments" : item}</option>)}</select></label>
          <label>Employment Type<select value={employmentType} onChange={(event) => setEmploymentType(event.target.value)}>{employmentTypes.map((item) => <option key={item} value={item}>{item === "all" ? "AllTypes" : item}</option>)}</select></label>
        </div>
      </Panel>

      <Panel title="PayrollSheet (AllMembers)" subtitle="Source: /FinanceAndPayroll/payments/ — Includes Pay Type For Every Employee.">
        <SimpleTable
          columns={["Employee", "Department", "Employment", "PayType", "BasePay", "PayPerTask", "Manager", "Finance", "Payment"]}
          rows={filtered.map((row) => [
            row.display_name,
            row.department,
            row.employment_type,
            row.pay_type || "-",
            money(row.base_pay),
            money(row.pay_per_task),
            row.manager_status || "Pending",
            row.finance_status || "Pending",
            row.payment_status || "-",
          ])}
        />
      </Panel>

      <section className="Split-Grid">
        <Panel title="PayPeriods">
          <SimpleTable columns={["Name", "Starts", "Ends", "Status"]} rows={(data.payPeriods || []).map((item) => [item.name, item.starts_on, item.ends_on, item.status])} />
        </Panel>
        <Panel title="PayslipDocuments">
          <SimpleTable columns={["ID", "Line", "Status", "Storage"]} rows={(data.payslipDocuments || []).map((item) => [item.id, item.payroll_line_item, item.status, item.storage_reference || "-"])} />
        </Panel>
      </section>
    </section>
  );
}

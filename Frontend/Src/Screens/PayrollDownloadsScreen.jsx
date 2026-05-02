import React, { useState } from "react";
import { Download } from "lucide-react";

import { apiGet } from "../Api/Client.js";
import { Panel, SimpleTable, StatCard } from "./Shared/ScreenComponents.jsx";
import { downloadCsv, employeeName, findById, money } from "./Shared/ScreenUtils.jsx";

export function PayrollDownloadsScreen({ data, selectedEmployeeId }) {
  const [calculation, setCalculation] = useState(null);
  const legacyRows = data.financeRows || [];
  const payrollRows = (data.payrollLineItems || []).length
    ? (data.payrollLineItems || []).map((item) => ({ employee: employeeName(data, item.employee), gross: item.gross_amount, deduction: item.deduction_amount, net: item.net_amount, status: item.status, payroll_run: item.payroll_run }))
    : legacyRows.map((item) => ({ employee: item.display_name || item.username, gross: item.base_pay || 0, deduction: 0, net: item.base_pay || 0, status: item.manager_status || "Pending", payroll_run: data.financeDashboard?.month_name || "Current" }));
  const employee = findById(data.employees, selectedEmployeeId) || data.employees?.[0] || {};

  const downloadPayroll = () => downloadCsv("payroll-download.csv", ["Employee", "Payroll Run", "Gross", "Deduction", "Net", "Status"], payrollRows.map((item) => [item.employee, item.payroll_run, item.gross, item.deduction, item.net, item.status]));
  const downloadPayslips = () => downloadCsv("payslip-index.csv", ["Payslip", "Line Item", "Status", "Storage Reference", "External Reference"], (data.payslipDocuments || []).map((item) => [item.id, item.payroll_line_item, item.status, item.storage_reference, item.external_id || item.external_reference]));
  const downloadOrders = () => downloadCsv("payment-orders.csv", ["Provider", "Employee", "Amount", "Currency", "Status", "Receipt"], (data.paymentOrders || []).map((item) => [item.provider, employeeName(data, item.employee), item.amount, item.currency, item.status, item.receipt]));
  const calculatePayroll = async () => setCalculation(await apiGet(`/FinanceAndPayroll/api/calculate-payroll/?employee=${selectedEmployeeId || ""}`));

  return (
    <section className="payroll-download-screen screen-stack">
      <section className="page-heading"><div><span>Finance / Payroll</span><h1>Payroll Downloads</h1></div><div className="button-row"><button className="outline-button" onClick={downloadPayroll}><Download size={16} /> Payroll CSV</button><button className="outline-button" onClick={downloadPayslips}><Download size={16} /> Payslip Index</button><button className="outline-button" onClick={downloadOrders}><Download size={16} /> Payment Orders</button></div></section>
      <div className="stat-grid four"><StatCard label="Payroll Rows" value={payrollRows.length} /><StatCard label="Pay Periods" value={(data.payPeriods || []).length} /><StatCard label="Payslips" value={(data.payslipDocuments || []).length} /><StatCard label="Payment Orders" value={(data.paymentOrders || []).length} /></div>
      <Panel title="Calculate Payroll" subtitle={employee.display_name ? `Using ${employee.display_name}` : "Using The Connected Workspace Context."}><button className="primary-button" onClick={calculatePayroll}>{selectedEmployeeId ? "Calculate Current Payroll" : "Calculate Workspace Payroll"}</button>{calculation && <pre>{JSON.stringify(calculation, null, 2)}</pre>}</Panel>
      <Panel title="Payroll Line Items"><SimpleTable columns={["Employee", "Run", "Gross", "Deduction", "Net", "Status"]} rows={payrollRows.map((item) => [item.employee, item.payroll_run, money(item.gross), money(item.deduction), money(item.net), item.status])} /></Panel>
      <section className="split-grid"><Panel title="Pay Periods"><SimpleTable columns={["Name", "Starts", "Ends", "Status"]} rows={(data.payPeriods || []).map((item) => [item.name, item.starts_on, item.ends_on, item.status])} /></Panel><Panel title="Payslip Documents"><SimpleTable columns={["ID", "Line", "Status", "Storage"]} rows={(data.payslipDocuments || []).map((item) => [item.id, item.payroll_line_item, item.status, item.storage_reference || "-"])} /></Panel></section>
    </section>
  );
}
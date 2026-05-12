import React from "react";
import { Check, X } from "lucide-react";
import "../Styles/FinanceScreen.css";

import { apiPost } from "../Api/Client.js";
import { money } from "./Shared/ScreenUtils.jsx";

export function FinanceScreen({ data, reload }) {
  const rows = data.financeRows || [];
  const departments = data.financeDashboard?.departments || data.departments || [];

  const approve = async (row) => {
    await apiPost("/FinanceAndPayroll/payment-approval/", { employee: row.id, userid: row.user_id, normalPay: row.base_pay || 0, show_month: data.financeDashboard?.month, show_year: data.financeDashboard?.year });
    reload();
  };

  return <section className="Finance-Screen"><aside><h2>All<br />Teams</h2>{departments.map((department) => <label key={department.id}><input type="checkbox" />{department.name}</label>)}</aside><main><h1>Showing Payroll For {data.financeDashboard?.month_name || "May"}</h1><div className="Finance-Search"><input placeholder="Search By Name" /><button className="Primary-Button">Search</button></div><label><input type="checkbox" /> Show Approved</label><table className="Erp-Table"><thead><tr><th>Name</th><th>Department</th><th>Days Left</th><th>Manager Status</th><th>Bank Details</th><th>Base Pay</th><th>Per Task Pay</th><th>Bounty</th><th>Extra Payment</th><th>Total</th><th /></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{row.display_name || row.username}</td><td>{row.department}</td><td>---</td><td className="Danger-Text">{row.manager_status}</td><td>{(data.bankAccounts || []).some((account) => String(account.employee) === String(row.id)) ? <Check className="Ok-Icon" /> : <X className="Bad-Icon" />}</td><td>{money(row.base_pay)}</td><td>{money(row.pay_per_task)}</td><td>0</td><td><input className="Mini-Input" defaultValue="0" /></td><td>{money(row.base_pay)}</td><td><button className="Primary-Button Small" onClick={() => approve(row)}>Approve</button></td></tr>)}</tbody></table></main></section>;
}
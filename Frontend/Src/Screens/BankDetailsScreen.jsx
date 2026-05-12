import React, { useEffect, useState } from "react";
import "../Styles/BankScreen.css";

import { apiPost } from "../Api/Client.js";
import { Panel, SimpleTable } from "./Shared/ScreenComponents.jsx";
import { findById } from "./Shared/ScreenUtils.jsx";

export function BankDetailsScreen({ data, selectedEmployeeId, reload }) {
  const employee = findById(data.employees, selectedEmployeeId) || data.employees?.[0] || {};
  const account = (data.bankAccounts || []).find((item) => String(item.employee) === String(selectedEmployeeId)) || data.bankAccounts?.[0] || {};
  const [form, setForm] = useState({ ifsc: account.ifsc_code || "", account: account.metadata?.legacy_account_number || "", confirm: "", upi: account.upi_id || "" });

  useEffect(() => setForm({ ifsc: account.ifsc_code || "", account: account.metadata?.legacy_account_number || "", confirm: "", upi: account.upi_id || "" }), [account.id]);

  const save = async () => {
    await apiPost("/FinanceAndPayroll/Bankdetails/", { employee: selectedEmployeeId, Ac_No: form.account, Ac_IFSC: form.ifsc, upi: form.upi });
    reload();
  };

  return <section className="Form-Page"><h1>Bank Details</h1><label>Employee<input value={employee.display_name || ""} readOnly /></label><label>Account IFSC<input value={form.ifsc} onChange={(event) => setForm({ ...form, ifsc: event.target.value })} /></label><label>Account Number<input type="password" value={form.account} onChange={(event) => setForm({ ...form, account: event.target.value })} /></label><label>Confirm Account Number<input value={form.confirm} onChange={(event) => setForm({ ...form, confirm: event.target.value })} placeholder="Confirm Bank Account Number" /></label><label>UPI<input value={form.upi} onChange={(event) => setForm({ ...form, upi: event.target.value })} /></label><button className="Primary-Button" onClick={save} disabled={!selectedEmployeeId || (form.confirm && form.confirm !== form.account)}>Update</button><Panel title="Current Bank Details"><SimpleTable columns={["Account Number", "IFSC Code", "UPI Address", "Status"]} rows={(data.bankAccounts || []).filter((item) => !selectedEmployeeId || String(item.employee) === String(selectedEmployeeId)).map((item) => [item.masked_account_number, item.ifsc_code, item.upi_id, item.verification_status])} /></Panel></section>;
}
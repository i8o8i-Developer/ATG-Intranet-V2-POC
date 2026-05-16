import React, { useEffect, useState } from "react";
import "../Styles/BankScreen.css";

import { apiPost } from "../Api/Client.js";
import { Panel, SimpleTable } from "./Shared/ScreenComponents.jsx";
import { findById } from "./Shared/ScreenUtils.jsx";

export function BankDetailsScreen({ data, selectedEmployeeId, reload }) {
  const employee = findById(data.employees, selectedEmployeeId) || data.employees?.[0] || {};
  const account = (data.bankAccounts || []).find((item) => String(item.employee) === String(selectedEmployeeId)) || data.bankAccounts?.[0] || {};
  const [form, setForm] = useState({ ifsc: account.ifsc_code || "", account: account.metadata?.legacy_account_number || "", confirm: "", upi: account.upi_id || "" });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => setForm({ ifsc: account.ifsc_code || "", account: account.metadata?.legacy_account_number || "", confirm: "", upi: account.upi_id || "" }), [account.id]);

  const save = async () => {
    setSaving(true);
    setMessage("");
    try {
      await apiPost("/FinanceAndPayroll/Bankdetails/", { employee: selectedEmployeeId, Ac_No: form.account, Ac_IFSC: form.ifsc, upi: form.upi });
      setMessage("Bank details saved successfully.");
      reload();
    } catch (err) {
      setMessage(err?.payload?.detail || "Failed to save bank details.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="Form-Page" style={{ padding: "24px 28px" }}>
      <h1 style={{ marginBottom: 20, fontSize: 22, fontWeight: 700 }}>Bank Details</h1>
      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: 20, maxWidth: 500 }}>
        <label style={{ display: "block", marginBottom: 12 }}>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Employee</span>
          <input value={employee.display_name || ""} readOnly style={{ width: "100%", padding: "8px 10px", marginTop: 4, border: "1px solid #e2e8f0", borderRadius: 6, fontSize: 14, background: "#f8fafc" }} />
        </label>
        <label style={{ display: "block", marginBottom: 12 }}>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>IFSC Code</span>
          <input value={form.ifsc} onChange={(e) => setForm({ ...form, ifsc: e.target.value })} style={{ width: "100%", padding: "8px 10px", marginTop: 4, border: "1px solid #e2e8f0", borderRadius: 6, fontSize: 14 }} />
        </label>
        <label style={{ display: "block", marginBottom: 12 }}>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Account Number</span>
          <input value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })} style={{ width: "100%", padding: "8px 10px", marginTop: 4, border: "1px solid #e2e8f0", borderRadius: 6, fontSize: 14 }} />
        </label>
        <label style={{ display: "block", marginBottom: 12 }}>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Confirm Account Number</span>
          <input value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} placeholder="Re-Enter Account Number" style={{ width: "100%", padding: "8px 10px", marginTop: 4, border: "1px solid #e2e8f0", borderRadius: 6, fontSize: 14 }} />
          {form.confirm && form.confirm !== form.account && <span style={{ fontSize: 11, color: "#ef4444" }}>Account Numbers Do Not Match</span>}
        </label>
        <label style={{ display: "block", marginBottom: 16 }}>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>UPI ID</span>
          <input value={form.upi} onChange={(e) => setForm({ ...form, upi: e.target.value })} style={{ width: "100%", padding: "8px 10px", marginTop: 4, border: "1px solid #e2e8f0", borderRadius: 6, fontSize: 14 }} />
        </label>
        {message && <div style={{ fontSize: 13, padding: "8px 12px", borderRadius: 6, marginBottom: 12, background: message.includes("success") ? "#f0fdf4" : "#fef2f2", color: message.includes("success") ? "#16a34a" : "#dc2626" }}>{message}</div>}
        <button className="Primary-Button" onClick={save} disabled={saving || !selectedEmployeeId || (form.confirm && form.confirm !== form.account)}>{saving ? "Saving..." : "Update Bank Details"}</button>
      </div>
      <Panel title="Current Bank Details">
        <SimpleTable columns={["Account Number", "IFSC Code", "UPI Address", "Status"]} rows={(data.bankAccounts || []).filter((item) => !selectedEmployeeId || String(item.employee) === String(selectedEmployeeId)).map((item) => [item.masked_account_number, item.ifsc_code, item.upi_id, item.verification_status])} />
      </Panel>
    </section>
  );
}
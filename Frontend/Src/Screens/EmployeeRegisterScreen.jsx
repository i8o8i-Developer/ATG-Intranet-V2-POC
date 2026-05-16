import React, { useMemo, useState } from "react";
import { Search, Download, ChevronDown, ChevronUp, Users, DollarSign, CreditCard, BadgeDollarSign } from "lucide-react";
import { Panel, SimpleTable, StatusPill, Modal } from "./Shared/ScreenComponents.jsx";
import { downloadCsv, employeeName, formatDate, money } from "./Shared/ScreenUtils.jsx";
import "../Styles/ProjectScreen.css";

export function EmployeeRegisterScreen({ data, reload }) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("employee_code");
  const [sortDir, setSortDir] = useState("asc");
  const [selectedEmp, setSelectedEmp] = useState(null);

  const employees = data.employees || [];
  const payProfiles = data.payProfiles || [];
  const lineItems = data.payrollLineItems || [];

  const sorted = useMemo(() => {
    const rows = employees.map((emp) => {
      const pay = payProfiles.find((p) => String(p.employee) === String(emp.id));
      const latest = lineItems.filter((li) => String(li.employee) === String(emp.id)).sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))[0];
      return {
        id: emp.id,
        employee_code: emp.employee_code || "-",
        display_name: emp.display_name || employeeName(data, emp.id) || "-",
        department: emp.department_name || "-",
        position: emp.position_title || "-",
        employment_type: emp.employment_type || "-",
        base_pay: Number(pay?.base_pay || 0),
        pay_type: pay?.pay_type || "-",
        gross: Number(latest?.gross_amount || 0),
        deduction: Number(latest?.deduction_amount || 0),
        net: Number(latest?.net_amount || 0),
        status: latest?.status || "Pending",
        joined_on: emp.joined_on,
        contact: emp.contact_number || "-",
        city: emp.city || "-",
      };
    }).filter((row) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return row.employee_code.toLowerCase().includes(q) || row.display_name.toLowerCase().includes(q) || row.department.toLowerCase().includes(q);
    });

    rows.sort((a, b) => {
      const aVal = a[sortKey] ?? "";
      const bVal = b[sortKey] ?? "";
      const cmp = typeof aVal === "number" ? aVal - bVal : String(aVal).localeCompare(String(bVal));
      return sortDir === "asc" ? cmp : -cmp;
    });
    return rows;
  }, [employees, payProfiles, lineItems, search, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
  };

  const totalPayroll = sorted.reduce((s, r) => s + r.gross, 0);
  const totalNet = sorted.reduce((s, r) => s + r.net, 0);
  const totalDeduction = sorted.reduce((s, r) => s + r.deduction, 0);

  const SortIcon = ({ column }) => sortKey === column ? (sortDir === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} />) : null;

  return (
    <section className="Screen-Stack" style={{ padding: "24px 28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>HR / Employee Register</span>
          <h1 style={{ margin: "4px 0 0", fontSize: 26, fontWeight: 700, color: "#0f172a" }}>Employee Register</h1>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <div className="Search-Box" style={{ width: 260 }}>
            <Search size={16} />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search By Name, ID, Or Department…" style={{ border: 0, outline: "none", flex: 1, fontSize: 13 }} />
          </div>
          <button className="Outline-Button" onClick={() => downloadCsv(`EmployeeRegister.csv`, ["ATG ID", "Employee Name", "Department", "Type", "Base Pay", "Pay Type", "Gross Pay", "PTRC Deducted", "Net Salary", "Status"], sorted.map((r) => [r.employee_code, r.display_name, r.department, r.employment_type, r.base_pay, r.pay_type, r.gross, r.deduction, r.net, r.status]))}><Download size={14} /> Export CSV</button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { icon: <Users size={20} />, label: "Total Employees", value: employees.length, color: "#3b82f6" },
          { icon: <DollarSign size={20} />, label: "Total Payroll (Gross)", value: `₹${totalPayroll.toLocaleString()}`, color: "#10b981" },
          { icon: <CreditCard size={20} />, label: "Total Deductions", value: `₹${totalDeduction.toLocaleString()}`, color: "#f59e0b" },
          { icon: <BadgeDollarSign size={20} />, label: "Total Net Payout", value: `₹${totalNet.toLocaleString()}`, color: "#8b5cf6" },
        ].map((card) => (
          <div key={card.label} style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "16px 20px", display: "flex", alignItems: "center", gap: 14, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: `${card.color}15`, display: "flex", alignItems: "center", justifyContent: "center", color: card.color }}>{card.icon}</div>
            <div><span style={{ fontSize: 12, color: "#64748b", fontWeight: 500 }}>{card.label}</span><strong style={{ display: "block", fontSize: 20, color: "#0f172a", marginTop: 2 }}>{card.value}</strong></div>
          </div>
        ))}
      </div>

      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                {[
                  ["employee_code", "ATG ID"],
                  ["display_name", "Employee Name"],
                  ["department", "Department"],
                  ["employment_type", "Type"],
                  ["base_pay", "Base Pay"],
                  ["pay_type", "Pay Type"],
                  ["gross", "Gross Pay"],
                  ["deduction", "PTRC Deducted"],
                  ["net", "Net Salary"],
                  ["status", "Status"],
                ].map(([key, label]) => (
                  <th key={key} onClick={() => toggleSort(key)} style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#475569", cursor: "pointer", whiteSpace: "nowrap", userSelect: "none" }}>
                    {label} <SortIcon column={key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => (
                <tr key={row.id} onClick={() => setSelectedEmp(row)} style={{ cursor: "pointer", borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "#fff" : "#fafafa", transition: "background 0.1s" }}
                  onMouseEnter={(e) => e.currentTarget.style.background = "#eef2ff"}
                  onMouseLeave={(e) => e.currentTarget.style.background = i % 2 === 0 ? "#fff" : "#fafafa"}>
                  <td style={{ padding: "10px 14px", fontWeight: 600, color: "#2563eb" }}>{row.employee_code}</td>
                  <td style={{ padding: "10px 14px", fontWeight: 500, color: "#0f172a" }}>{row.display_name}</td>
                  <td style={{ padding: "10px 14px", color: "#475569" }}>{row.department}</td>
                  <td style={{ padding: "10px 14px" }}><StatusPill tone={row.employment_type === "Intern" ? "blue" : row.employment_type === "Full-Time" ? "green" : "gold"}>{row.employment_type}</StatusPill></td>
                  <td style={{ padding: "10px 14px", fontVariantNumeric: "tabular-nums" }}>₹{row.base_pay.toLocaleString()}</td>
                  <td style={{ padding: "10px 14px", color: "#64748b" }}>{row.pay_type}</td>
                  <td style={{ padding: "10px 14px", fontVariantNumeric: "tabular-nums", fontWeight: 500 }}>₹{row.gross.toLocaleString()}</td>
                  <td style={{ padding: "10px 14px", color: "#dc2626", fontVariantNumeric: "tabular-nums" }}>₹{row.deduction.toLocaleString()}</td>
                  <td style={{ padding: "10px 14px", fontWeight: 600, color: "#059669", fontVariantNumeric: "tabular-nums" }}>₹{row.net.toLocaleString()}</td>
                  <td style={{ padding: "10px 14px" }}><StatusPill tone={row.status === "Paid" ? "green" : "gold"}>{row.status}</StatusPill></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!sorted.length && <div style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>No employees found matching your search.</div>}
      </div>

      {selectedEmp && (
        <div className="Modal-Backdrop" onClick={() => setSelectedEmp(null)}>
          <section className="Modal" onClick={(e) => e.stopPropagation()} style={{ width: "min(600px, calc(100vw - 56px))" }}>
            <div className="Modal-Body">
              <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20, paddingBottom: 16, borderBottom: "1px solid #e2e8f0" }}>
                <div style={{ width: 48, height: 48, borderRadius: "50%", background: "#3b82f6", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, fontWeight: 700 }}>{selectedEmp.display_name.charAt(0)}</div>
                <div><h2 style={{ margin: 0, fontSize: 18 }}>{selectedEmp.display_name}</h2><span style={{ color: "#64748b", fontSize: 13 }}>{selectedEmp.employee_code} · {selectedEmp.department}</span></div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                {[
                  ["Employee Code", selectedEmp.employee_code],
                  ["Department", selectedEmp.department],
                  ["Position", selectedEmp.position],
                  ["Employment Type", selectedEmp.employment_type],
                  ["Base Pay", `₹${selectedEmp.base_pay.toLocaleString()}`],
                  ["Pay Type", selectedEmp.pay_type],
                  ["Gross Pay", `₹${selectedEmp.gross.toLocaleString()}`],
                  ["PTRC Deducted", `₹${selectedEmp.deduction.toLocaleString()}`],
                  ["Net Salary", `₹${selectedEmp.net.toLocaleString()}`],
                  ["Status", selectedEmp.status],
                  ["City", selectedEmp.city],
                  ["Contact", selectedEmp.contact],
                  ["Joined", selectedEmp.joined_on ? formatDate(selectedEmp.joined_on) : "-"],
                ].map(([label, value]) => (
                  <div key={label} style={{ padding: "8px 0" }}>
                    <dt style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 2 }}>{label}</dt>
                    <dd style={{ margin: 0, fontSize: 14, color: "#0f172a", fontWeight: 500 }}>{value}</dd>
                  </div>
                ))}
              </div>
              {/* Salary Revision History */}
              {(() => {
                const empPayProfiles = (data.payProfiles || []).filter((p) => String(p.employee) === String(selectedEmp.id)).sort((a, b) => new Date(b.effective_at || 0) - new Date(a.effective_at || 0));
                if (!empPayProfiles.length) return null;
                return (
                  <div style={{ marginTop: 16, paddingTop: 12, borderTop: "1px solid #e2e8f0" }}>
                    <h4 style={{ margin: "0 0 8px", fontSize: 14 }}>Salary Revision History</h4>
                    {empPayProfiles.map((p, i) => (
                      <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 12, borderBottom: "1px solid #f1f5f9" }}>
                        <span style={{ color: "#64748b" }}>{formatDate(p.effective_at)}</span>
                        <span>₹{Number(p.base_pay || 0).toLocaleString()}</span>
                        <span style={{ color: "#64748b" }}>{p.pay_type} {Number(p.performance_pay || 0) > 0 ? `+ ₹${Number(p.performance_pay).toLocaleString()}` : ""}</span>
                      </div>
                    ))}
                  </div>
                );
              })()}
              <div style={{ marginTop: 16, paddingTop: 12, borderTop: "1px solid #e2e8f0", display: "flex", gap: 8 }}>
                <button className="Soft-Button" onClick={() => setSelectedEmp(null)}>Close</button>
              </div>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}

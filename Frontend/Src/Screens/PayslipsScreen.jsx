import React, { useMemo, useState } from "react";
import { Download, FileText } from "lucide-react";
import "../Styles/PayslipScreen.css";

import { EmptyState, Modal, Panel, SimpleTable, StatCard, StatusPill } from "./Shared/ScreenComponents.jsx";
import { employeeName, money } from "./Shared/ScreenUtils.jsx";

export function PayslipsScreen({ data }) {
  const me = data.me || {};
  const isSuperAdmin = Boolean(me.user?.is_superuser || me.user?.is_staff || me.is_superuser || me.is_staff);
  const myEmployeeId = me.employees?.[0]?.id;

  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);

  const lineItems = data.payrollLineItems || [];
  const payslips = data.payslipDocuments || [];

  const rows = useMemo(() => {
    return payslips.map((doc) => {
      const line = lineItems.find((item) => String(item.id) === String(doc.payroll_line_item)) || {};
      const empName = employeeName(data, line.employee);
      return {
        id: doc.id,
        employee: line.employee,
        employeeName: empName,
        runId: line.payroll_run,
        gross: line.gross_amount,
        deduction: line.deduction_amount,
        net: line.net_amount,
        status: doc.status || line.status || "Pending",
        storage: doc.storage_reference || doc.metadata?.url || "",
        metadata: doc.metadata || {},
        period: line.metadata?.period || doc.metadata?.period || "",
      };
    });
  }, [data, lineItems, payslips]);

  const visible = isSuperAdmin
    ? rows
    : rows.filter((row) => String(row.employee) === String(myEmployeeId));
  const filtered = visible.filter((row) => !search || row.employeeName.toLowerCase().includes(search.toLowerCase()));

  const totalNet = filtered.reduce((sum, row) => sum + Number(row.net || 0), 0);

  const openPayslip = async (row) => {
    if (row.storage && /^https?:\/\//.test(row.storage)) {
      try {
        const resp = await fetch(row.storage);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = `payslip_${row.id}.pdf`; a.click();
        URL.revokeObjectURL(url);
      } catch { window.open(row.storage, "_blank", "noopener"); }
    } else {
      setSelected(row);
    }
  };

  return (
    <section className="Payslip-Screen Screen-Stack">
      <section className="Page-Heading">
        <div>
          <span>Finance / Payslips</span>
          <h1>{isSuperAdmin ? "All Payslips" : "My Payslips"}</h1>
        </div>
        <StatusPill tone="blue">{filtered.length} Available</StatusPill>
      </section>

      <div className="Stat-Grid Four">
        <StatCard label="Payslips" value={filtered.length} />
        <StatCard label="Total Net" value={money(totalNet)} />
        <StatCard label="Pay Periods" value={(data.payPeriods || []).length} />
        <StatCard label="Pending" value={filtered.filter((row) => String(row.status).toLowerCase() === "pending").length} />
      </div>

      {isSuperAdmin && (
        <Panel title="Search" subtitle="Filter All Payslips By Employee Name.">
          <div className="Form-Grid">
            <label>Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Employee Name" /></label>
          </div>
        </Panel>
      )}

      <Panel title="Payslips" subtitle="Source: /Finance And Payroll / Payslip Documents/.">
        <SimpleTable
          columns={["Employee", "Pay Run", "Period", "Gross", "Deduction", "Net", "Status", "Action"]}
          rows={filtered.map((row) => [
            row.employeeName,
            row.runId || "-",
            row.period || "-",
            money(row.gross),
            money(row.deduction),
            money(row.net),
            <StatusPill key="status" tone={String(row.status).toLowerCase() === "issued" || String(row.status).toLowerCase() === "paid" ? "green" : "gold"}>{row.status}</StatusPill>,
            <span className="Table-Actions" key="actions">
              <button className="Soft-Button Small" onClick={() => openPayslip(row)}><FileText size={13} /> View</button>
              {row.storage && /^https?:\/\//.test(row.storage) && (
                <a className="Soft-Button Small" href={row.storage} target="_blank" rel="noreferrer" download><Download size={13} /> Download</a>
              )}
            </span>,
          ])}
        />
        {!filtered.length && <EmptyState label="No Payslips Available Yet." />}
      </Panel>

      {selected && (
        <Modal title={`Payslip — ${selected.employeeName}`} onClose={() => setSelected(null)} wide>
          <dl className="Details-Grid">
            <div><dt>Employee</dt><dd>{selected.employeeName}</dd></div>
            <div><dt>Pay Run</dt><dd>{selected.runId || "-"}</dd></div>
            <div><dt>Period</dt><dd>{selected.period || "-"}</dd></div>
            <div><dt>Gross</dt><dd>{money(selected.gross)}</dd></div>
            <div><dt>Deduction</dt><dd>{money(selected.deduction)}</dd></div>
            <div><dt>Net</dt><dd>{money(selected.net)}</dd></div>
            <div><dt>Status</dt><dd>{selected.status}</dd></div>
            <div><dt>Reference</dt><dd>{selected.storage || "Not Yet Uploaded."}</dd></div>
          </dl>
          {selected.metadata?.components && (
            <Panel title="Components">
              <SimpleTable columns={["Name", "Amount"]} rows={Object.entries(selected.metadata.components).map(([key, value]) => [key, money(value)])} />
            </Panel>
          )}
        </Modal>
      )}
    </section>
  );
}

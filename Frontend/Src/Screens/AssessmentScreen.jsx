import React, { useMemo, useState } from "react";
import { ChevronDown, Search, X } from "lucide-react";

import { apiPost } from "../Api/Client.js";
import { EmptyState, Modal, Panel, SimpleTable, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { employeeName, formatDate, isCompleted } from "./Shared/ScreenUtils.jsx";

export function AssessmentScreen({ data, reload }) {
  const [tab, setTab] = useState("results");
  const [search, setSearch] = useState("");
  const [assignOpen, setAssignOpen] = useState(false);

  const rows = useMemo(() => {
    const source = data.assessmentRows?.length ? data.assessmentRows : data.assessmentAssignments || [];
    return source.filter((row) => {
      if (!search) return true;
      const term = `${row.employee_name || ""} ${row.assessment_title || ""} ${row.note || row.status || ""}`.toLowerCase();
      return term.includes(search.toLowerCase());
    });
  }, [data.assessmentRows, data.assessmentAssignments, search]);

  const startAssignment = async (id) => {
    await apiPost(`/Assesment/AssessmentAssignments/${id}/start/`, {});
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };
  const submitAssignment = async (id) => {
    const url = window.prompt("Provider Submission URL (Optional)");
    await apiPost(`/Assesment/AssessmentAssignments/${id}/submit/`, { provider_url: url || "", score: null });
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };
  const syncAssignment = async (id) => {
    await apiPost(`/Assesment/AssessmentAssignments/${id}/sync-provider-status/`, {});
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };

  return (
    <section className="assessment-screen screen-stack">
      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          ["results", "Assessment Results"],
          ["assign", "Assign Assessment"],
        ]}
      />
      {tab === "results" && (
        <Panel title="Assessment Results">
          <div className="toolbar-row">
            <div className="search-box">
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search Here..." />
              <Search size={17} />
              {search && <X size={17} onClick={() => setSearch("")} />}
            </div>
          </div>
          <table className="erp-table">
            <thead>
              <tr><th>Intern Name</th><th>Week Since Joining</th><th>Latest Assessment</th><th>Number</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {rows.map((row, index) => {
                const status = String(row.status || row.note || "").toLowerCase();
                return (
                  <tr key={row.id || index}>
                    <td><ChevronDown size={15} />{row.employee_name || row.employee || row.name}</td>
                    <td>{row.weeks_since_join || row.week_since_join || "-"} Weeks</td>
                    <td>{row.assessment_title || row.latest_assessment || row.assessment}</td>
                    <td>{row.assessment_sequence_number || row.assessment_number || row.attempts_count || 1}</td>
                    <td><StatusPill tone={isCompleted(row.status || row.note) ? "green" : "gold"}>{row.note || row.status || "Incomplete"}</StatusPill></td>
                    <td className="table-actions">
                      {!status.includes("progress") && !status.includes("submit") && !status.includes("complete") && (
                        <button className="soft-button small" onClick={() => startAssignment(row.id)}>Start</button>
                      )}
                      {!status.includes("submit") && !status.includes("complete") && (
                        <button className="soft-button small" onClick={() => submitAssignment(row.id)}>Submit</button>
                      )}
                      <button className="soft-button small" onClick={() => syncAssignment(row.id)}>Sync</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!rows.length && <EmptyState label="No Assessment Results Returned." />}
        </Panel>
      )}
      {tab === "assign" && (
        <Panel
          title="Assign Assessment"
          right={<button className="primary-button small" onClick={() => setAssignOpen(true)}>New Assignment</button>}
        >
          <SimpleTable
            columns={["Template", "Status", "Tags", "Updated"]}
            rows={(data.assessmentTemplates || []).map((tpl) => [tpl.title, tpl.status, (tpl.tags || []).join(", "), formatDate(tpl.updated_at)])}
          />
          {!(data.assessmentTemplates || []).length && <EmptyState label="No Templates Returned." />}
        </Panel>
      )}
      {assignOpen && <AssignModal data={data} onClose={() => setAssignOpen(false)} reload={reload} />}
    </section>
  );
}

function AssignModal({ data, onClose, reload }) {
  const [templateId, setTemplateId] = useState(data.assessmentTemplates?.[0]?.id || "");
  const [employees, setEmployees] = useState([]);
  const [busy, setBusy] = useState(false);

  const toggle = (id) => setEmployees((prev) => prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]);

  const save = async () => {
    if (!templateId || !employees.length) return;
    setBusy(true);
    try {
      await apiPost(`/Assesment/AssessmentTemplates/${templateId}/assign/`, { employees, due_at: null });
      reload(["assessmentAssignments", "assessmentLegacy"]);
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Assign Assessment" onClose={onClose} wide>
      <label>Template
        <select value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
          <option value="">Select Template</option>
          {(data.assessmentTemplates || []).map((tpl) => <option key={tpl.id} value={tpl.id}>{tpl.title}</option>)}
        </select>
      </label>
      <h4>Employees</h4>
      <div className="checkbox-grid">
        {(data.employees || []).map((emp) => (
          <label key={emp.id} className="inline-checkbox">
            <input type="checkbox" checked={employees.includes(emp.id)} onChange={() => toggle(emp.id)} />
            {emp.display_name || employeeName(data, emp.id)}
          </label>
        ))}
      </div>
      <button className="primary-button" onClick={save} disabled={busy || !templateId || !employees.length}>Assign To {employees.length || "0"} Employees</button>
    </Modal>
  );
}

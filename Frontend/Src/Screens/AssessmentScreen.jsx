import React, { useMemo, useState } from "react";
import { ChevronDown, Search, X } from "Lucide-React";

import { apiPost } from "../Api/Client.js";
import { EmptyState, Modal, Panel, SimpleTable, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { employeeName, formatDate, isCompleted } from "./Shared/ScreenUtils.jsx";

export function AssessmentScreen({ data, reload }) {
  const [tab, setTab] = useState("results");
  const [search, setSearch] = useState("");
  const [assignOpen, setAssignOpen] = useState(false);

  const rows = useMemo(() => {
    const source = data.assessmentRows?.length ? data.assessmentRows : data.assessmentAssignments || [];
    return source.map((row) => {
      const latest = row.assessments?.[0] || {};
      return {
        ...row,
        ...latest,
        assignment_id: row.assignment_id ?? latest.assignment_id ?? row.id ?? null,
        employee_name: row.employee_name || row.employee || row.name || "-",
        assessment_title: row.assessment_title || latest.assessment_title || row.latest_assessment || row.assessment || "-",
        assessment_sequence_number: row.assessment_sequence_number || latest.sequence_number || row.assessment_number || row.attempts_count || 1,
        weeks_since_join: row.weeks_since_join ?? latest.weeks_since_join ?? row.week_since_join ?? null,
        status: row.status || latest.status || row.note || "Assigned",
        note: row.note || latest.note || "",
      };
    }).filter((row) => {
      if (!search) return true;
      const term = `${row.employee_name || ""} ${row.assessment_title || ""} ${row.note || row.status || ""}`.toLowerCase();
      return term.includes(search.toLowerCase());
    });
  }, [data.assessmentRows, data.assessmentAssignments, search]);

  const startAssignment = async (id) => {
    if (!id) return;
    await apiPost(`/Assesment/AssessmentAssignments/${id}/start/`, {});
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };
  const submitAssignment = async (id) => {
    if (!id) return;
    const url = window.prompt("ProviderSubmissionURL (Optional)");
    await apiPost(`/Assesment/AssessmentAssignments/${id}/submit/`, { provider_url: url || "", score: null });
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };
  const syncAssignment = async (id) => {
    if (!id) return;
    await apiPost(`/Assesment/AssessmentAssignments/${id}/sync-provider-status/`, {});
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };

  return (
    <section className="Assessment-ScreenScreen-Stack">
      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          ["results", "AssessmentResults"],
          ["assign", "AssignAssessment"],
        ]}
      />
      {tab === "results" && (
        <Panel title="AssessmentResults">
          <div className="Toolbar-Row">
            <div className="Search-Box">
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="SearchHere..." />
              <Search size={17} />
              {search && <X size={17} onClick={() => setSearch("")} />}
            </div>
          </div>
          <table className="Erp-Table">
            <thead>
              <tr><th>Intern Name</th><th>Week Since Joining</th><th>Latest Assessment</th><th>Number</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {rows.map((row, index) => {
                const status = String(row.status || row.note || "").toLowerCase();
                const assignmentId = row.assignment_id;
                return (
                  <tr key={assignmentId || row.employee_id || index}>
                    <td><ChevronDown size={15} />{row.employee_name || row.employee || row.name}</td>
                    <td>{row.weeks_since_join || row.week_since_join || "-"} Weeks</td>
                    <td>{row.assessment_title || row.latest_assessment || row.assessment}</td>
                    <td>{row.assessment_sequence_number || row.assessment_number || row.attempts_count || 1}</td>
                    <td><StatusPill tone={isCompleted(row.status || row.note) ? "green" : "gold"}>{row.note || row.status || "Incomplete"}</StatusPill></td>
                    <td className="Table-Actions">
                      {!status.includes("progress") && !status.includes("submit") && !status.includes("complete") && assignmentId && (
                        <button className="Soft-ButtonSmall" onClick={() => startAssignment(assignmentId)}>Start</button>
                      )}
                      {!status.includes("submit") && !status.includes("complete") && assignmentId && (
                        <button className="Soft-ButtonSmall" onClick={() => submitAssignment(assignmentId)}>Submit</button>
                      )}
                      {assignmentId ? (
                        <button className="Soft-ButtonSmall" onClick={() => syncAssignment(assignmentId)}>Sync</button>
                      ) : (
                        <span className="Muted-Text">No Assignment Id</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!rows.length && <EmptyState label="NoAssessmentResultsReturned." />}
        </Panel>
      )}
      {tab === "assign" && (
        <Panel
          title="AssignAssessment"
          right={<button className="Primary-ButtonSmall" onClick={() => setAssignOpen(true)}>New Assignment</button>}
        >
          <SimpleTable
            columns={["Template", "Status", "Tags", "Updated"]}
            rows={(data.assessmentTemplates || []).map((tpl) => [tpl.title, tpl.status, (tpl.tags || []).join(", "), formatDate(tpl.updated_at)])}
          />
          {!(data.assessmentTemplates || []).length && <EmptyState label="NoTemplatesReturned." />}
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
    <Modal title="AssignAssessment" onClose={onClose} wide>
      <label>Template
        <select value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
          <option value="">Select Template</option>
          {(data.assessmentTemplates || []).map((tpl) => <option key={tpl.id} value={tpl.id}>{tpl.title}</option>)}
        </select>
      </label>
      <h4>Employees</h4>
      <div className="Checkbox-Grid">
        {(data.employees || []).map((emp) => (
          <label key={emp.id} className="Inline-Checkbox">
            <input type="checkbox" checked={employees.includes(emp.id)} onChange={() => toggle(emp.id)} />
            {emp.display_name || employeeName(data, emp.id)}
          </label>
        ))}
      </div>
      <button className="Primary-Button" onClick={save} disabled={busy || !templateId || !employees.length}>Assign To {employees.length || "0"} Employees</button>
    </Modal>
  );
}

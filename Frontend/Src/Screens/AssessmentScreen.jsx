import React, { useMemo, useState } from "react";
import { ChevronDown, Plus, Search, X } from "lucide-react";
import "../Styles/AssessmentScreen.css";

import { apiPost } from "../Api/Client.js";
import { EmptyState, Modal, Panel, SimpleTable, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { employeeName, formatDate, isCompleted } from "./Shared/ScreenUtils.jsx";

export function AssessmentScreen({ data, reload }) {
  const [tab, setTab] = useState("results");
  const [search, setSearch] = useState("");
  const [assignOpen, setAssignOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

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
    const score = window.prompt("Enter score (0-100):", "70");
    const parsed = Math.max(0, Math.min(100, Number(score) || 0));
    await apiPost(`/Assesment/AssessmentAssignments/${id}/submit/`, { score: parsed, percentage: parsed, status: "Submitted" });
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };
  const syncAssignment = async (id) => {
    if (!id) return;
    await apiPost(`/Assesment/AssessmentAssignments/${id}/sync-provider-status/`, {});
    reload(["assessmentAssignments", "assessmentLegacy"]);
  };

  return (
    <section className="Assessment-Screen Screen-Stack">
      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          ["results", "Assessment Results"],
          ["assign", "Assign Assessment"],
          ["create", "Create Template"],
        ]}
      />
      {tab === "results" && (
        <Panel title="Assessment Results">
          <div className="Toolbar-Row">
            <div className="Search-Box">
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search Here..." />
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
                      {!status.includes("progress") && !isCompleted(row.status || row.note) && assignmentId && (
                        <button className="Soft-Button Small" onClick={() => startAssignment(assignmentId)}>Start</button>
                      )}
                      {!isCompleted(row.status || row.note) && assignmentId && (
                        <button className="Soft-Button Small" onClick={() => submitAssignment(assignmentId)}>Submit</button>
                      )}
                      {assignmentId ? (
                        <button className="Soft-Button Small" onClick={() => syncAssignment(assignmentId)}>Sync</button>
                      ) : (
                        <span className="Muted-Text">No Assignment ID</span>
                      )}
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
          right={<button className="Primary-Button Small" onClick={() => setAssignOpen(true)}>New Assignment</button>}
        >
          <SimpleTable
            columns={["Template", "Status", "Tags", "Updated"]}
            rows={(data.assessmentTemplates || []).map((tpl) => [tpl.title, tpl.status, (tpl.tags || []).join(", "), formatDate(tpl.updated_at)])}
          />
          {!(data.assessmentTemplates || []).length && <EmptyState label="No Templates Returned." />}
        </Panel>
      )}
      {tab === "create" && (
        <Panel
          title="Create Assessment Template"
          right={<button className="Primary-Button Small" onClick={() => setCreateOpen(true)}><Plus size={14} /> New Template</button>}
        >
          <SimpleTable
            columns={["Title", "Type", "Status", "Questions", "Updated"]}
            rows={(data.assessmentTemplates || []).map((tpl) => [
              tpl.title,
              tpl.assessment_type || "-",
              <StatusPill key={tpl.id} tone={tpl.status === "Active" ? "green" : tpl.status === "Draft" ? "gold" : "slate"}>{tpl.status}</StatusPill>,
              (tpl.question_payload || []).length,
              formatDate(tpl.updated_at),
            ])}
          />
          {!(data.assessmentTemplates || []).length && <EmptyState label="No Templates Yet. Create One!" />}
        </Panel>
      )}
      {assignOpen && <AssignModal data={data} onClose={() => setAssignOpen(false)} reload={reload} />}
      {createOpen && <CreateTemplateModal data={data} onClose={() => setCreateOpen(false)} reload={reload} />}
    </section>
  );
}

function CreateTemplateModal({ data, onClose, reload }) {
  const [form, setForm] = useState({ title: "", assessment_type: "Compliance", department: "", status: "Draft", instructions: "", passing_score: 70, duration_minutes: 30, questions: [{ question: "", options: ["", "", "", ""], correct: 0 }] });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const addQuestion = () => setForm({ ...form, questions: [...form.questions, { question: "", options: ["", "", "", ""], correct: 0 }] });
  const removeQuestion = (i) => setForm({ ...form, questions: form.questions.filter((_, idx) => idx !== i) });
  const setQuestion = (i, val) => { const qs = [...form.questions]; qs[i] = { ...qs[i], question: val }; setForm({ ...form, questions: qs }); };
  const setOption = (qi, oi, val) => { const qs = [...form.questions]; qs[qi] = { ...qs[qi], options: qs[qi].options.map((o, idx) => idx === oi ? val : o) }; setForm({ ...form, questions: qs }); };
  const setCorrect = (qi, oi) => { const qs = [...form.questions]; qs[qi] = { ...qs[qi], correct: oi }; setForm({ ...form, questions: qs }); };

  const save = async () => {
    if (!form.title.trim()) { setError("Title is required."); return; }
    setBusy(true); setError("");
    try {
      await apiPost("/Assesment/AssessmentTemplates/", {
        title: form.title,
        assessment_type: form.assessment_type,
        department: form.department || null,
        status: form.status,
        instructions: form.instructions,
        passing_score: Number(form.passing_score) || 0,
        duration_minutes: Number(form.duration_minutes) || 0,
        question_payload: form.questions,
      });
      reload(["assessmentTemplates", "assessmentAssignments", "assessmentLegacy"]);
      onClose();
    } catch (err) {
      setError(err?.payload?.title?.[0] || err?.payload?.detail || err?.message || "Failed To Create Template.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Create Assessment Template" onClose={onClose} wide>
      <div className="Form-Grid Two">
        <label>Title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="React Navigation Check" /></label>
        <label>Type<select value={form.assessment_type} onChange={(e) => setForm({ ...form, assessment_type: e.target.value })}><option>Compliance</option><option>Technical</option><option>Behavioral</option></select></label>
        <label>Department<select value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}><option value="">All Departments</option>{(data.departments || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
        <label>Status<select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option>Draft</option><option>Active</option></select></label>
        <label>Passing Score (%)<input type="number" min="0" max="100" value={form.passing_score} onChange={(e) => setForm({ ...form, passing_score: e.target.value })} /></label>
        <label>Duration (min)<input type="number" min="0" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} /></label>
      </div>
      <label>Instructions<textarea value={form.instructions} onChange={(e) => setForm({ ...form, instructions: e.target.value })} placeholder="Instructions For The Assessment..." /></label>
      <h4>Questions ({form.questions.length}) <button className="Soft-Button Small" onClick={addQuestion}><Plus size={13} /> Add</button></h4>
      {form.questions.map((q, qi) => (
        <div key={qi} style={{ border: "1px solid #e2e8f0", borderRadius: 8, padding: 12, marginBottom: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <strong>Q{qi + 1}</strong>
            {form.questions.length > 1 && <button className="Soft-Button Small Danger" onClick={() => removeQuestion(qi)}>Remove</button>}
          </div>
          <input value={q.question} onChange={(e) => setQuestion(qi, e.target.value)} placeholder="Question Text..." style={{ width: "100%", marginBottom: 8 }} />
          {q.options.map((opt, oi) => (
            <label key={oi} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4, fontSize: 13 }}>
              <input type="radio" name={`correct-${qi}`} checked={q.correct === oi} onChange={() => setCorrect(qi, oi)} />
              <input value={opt} onChange={(e) => setOption(qi, oi, e.target.value)} placeholder={`Option ${oi + 1}`} style={{ flex: 1 }} />
              {q.correct === oi && <span style={{ color: "#10b981", fontSize: 11 }}>Correct Answer</span>}
            </label>
          ))}
        </div>
      ))}
      {error && <div className="error-banner">{error}</div>}
      <button className="Primary-Button" onClick={save} disabled={busy || !form.title}>Create Template</button>
    </Modal>
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

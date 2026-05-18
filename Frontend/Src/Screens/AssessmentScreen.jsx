import React, { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, Plus, Search, X } from "lucide-react";
import "../Styles/AssessmentScreen.css";

import { apiPost } from "../Api/Client.js";
import { EmptyState, Modal, Panel, SimpleTable, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { employeeName, formatDate, isCompleted, resolveActiveEmployee } from "./Shared/ScreenUtils.jsx";

export function AssessmentScreen({ data, selectedEmployeeId, reload }) {
  const [tab, setTab] = useState("results");
  const [search, setSearch] = useState("");
  const [assignOpen, setAssignOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const linkedEmployee = resolveActiveEmployee(data);
  const myEmployeeId = linkedEmployee?.id || selectedEmployeeId;

  const rows = useMemo(() => {
    const source = data.assessmentRows?.length ? data.assessmentRows : data.assessmentAssignments || [];
    return source
      .filter((row) => {
        const rowEmployeeId = row.employee || row.employee_id || row.employeeId;
        return !rowEmployeeId || !myEmployeeId || String(rowEmployeeId) === String(myEmployeeId);
      })
      .map((row) => {
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

  const [takeAssessment, setTakeAssessment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [assessmentError, setAssessmentError] = useState("");
  const [timeLeft, setTimeLeft] = useState(null);
  const timerRef = useRef(null);

  const startAssignment = async (id) => {
    if (!id) return;
    try {
      await apiPost(`/Assesment/AssessmentAssignments/${id}/start/`, {});
      reload(["assessmentAssignments", "assessmentLegacy"]);
    } catch (e) { setAssessmentError("Failed To Start Assessment."); }
  };

  const openTakeAssessment = async (row) => {
    const templates = data.assessmentTemplates || [];
    const template = templates.find((t) => String(t.id) === String(row.assessment || row.assessment_id));
    if (!template) { setAssessmentError("No Questions Available For This Assessment."); return; }
    setAnswers({});
    setAssessmentError("");
    const duration = Number(template.duration_minutes || 0);
    if (duration > 0) setTimeLeft(duration * 60);
    else setTimeLeft(null);
    setTakeAssessment({ assignmentId: row.assignment_id, questions: template.question_payload || [], title: template.title || "Assessment" });
  };

  useEffect(() => {
    if (!takeAssessment || timeLeft === null || timeLeft <= 0) return;
    if (timeLeft <= 0) { submitAnswers(); return; }
    timerRef.current = setInterval(() => setTimeLeft((prev) => { if (prev <= 1) { clearInterval(timerRef.current); submitAnswers(); return 0; } return prev - 1; }), 1000);
    return () => clearInterval(timerRef.current);
  }, [takeAssessment, timeLeft]);

  const submitAnswers = async () => {
    if (!takeAssessment) return;
    setSubmitting(true);
    const questions = takeAssessment.questions;
    let correct = 0;
    const details = questions.map((q, i) => {
      const isCorrect = Number(answers[i]) === Number(q.correct);
      if (isCorrect) correct++;
      return { question: q.question || q.q || "", selected: answers[i], correct: q.correct, isCorrect, options: q.options || [] };
    });
    const score = questions.length > 0 ? Math.round((correct / questions.length) * 100) : 0;
    try {
      await apiPost(`/Assesment/AssessmentAssignments/${takeAssessment.assignmentId}/submit/`, { score, percentage: score, status: "Submitted", answer_payload: answers });
      setAssessmentResult({ score, correct, total: questions.length, details });
      setAssessmentError("");
      reload(["assessmentAssignments", "assessmentLegacy"]);
    } catch (err) {
      setAssessmentError(err?.payload?.detail || "Submit failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const syncAssignment = async (id) => {
    if (!id) return;
    try {
      await apiPost(`/Assesment/AssessmentAssignments/${id}/sync-provider-status/`, {});
      reload(["assessmentAssignments", "assessmentLegacy"]);
    } catch (e) { setAssessmentError("Sync Failed."); }
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
      {assessmentError && <div style={{ fontSize: 13, padding: "8px 14px", marginBottom: 12, borderRadius: 6, background: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca" }}>{assessmentError}</div>}
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
                      {isCompleted(row.status || row.note) ? (
                        <span className="Muted-Text" style={{ color: "#10b981", fontWeight: 600 }}>Completed</span>
                      ) : (
                        <span className="Muted-Text" style={{ color: "#64748b", fontSize: 12 }}>Pending</span>
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
      {takeAssessment && !assessmentResult && (
        <div className="Modal-Backdrop" onClick={() => { setTakeAssessment(null); setAnswers({}); }}>
          <section className="Modal Wide" onClick={(e) => e.stopPropagation()} style={{ width: "min(700px, calc(100vw - 56px))" }}>
            <div className="Modal-Body" style={{ maxHeight: "80vh", overflow: "auto" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h2>{takeAssessment.title}</h2>
                {timeLeft !== null && <span style={{ fontSize: 14, fontWeight: 700, color: timeLeft < 60 ? "#ef4444" : "#0f172a" }}>{Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, "0")} Min</span>}
              </div>
              <p style={{ color: "#64748b", marginBottom: 16, fontSize: 13 }}>Answer The Questions Below And Submit To Complete The Assessment.</p>
              {takeAssessment.questions.map((q, qi) => (
                <div key={qi} style={{ marginBottom: 16, padding: 14, border: "1px solid #e2e8f0", borderRadius: 8, background: "#fafafa" }}>
                  <p style={{ fontWeight: 600, marginBottom: 8, fontSize: 14 }}>Q{qi + 1}. {q.question || q.q || ""}</p>
                  {(q.options || []).map((opt, oi) => (
                    <label key={oi} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", marginBottom: 4, borderRadius: 6, cursor: "pointer", background: Number(answers[qi]) === oi ? "#eef2ff" : "#fff", border: "1px solid", borderColor: Number(answers[qi]) === oi ? "#3b82f6" : "#e2e8f0" }}>
                      <input type="radio" name={`q-${qi}`} checked={Number(answers[qi]) === oi} onChange={() => setAnswers({ ...answers, [qi]: oi })} />
                      <span style={{ fontSize: 13 }}>{opt}</span>
                    </label>
                  ))}
                </div>
              ))}
              {!takeAssessment.questions.length && <p style={{ color: "#94a3b8" }}>No Questions Configured For This Assessment Template.</p>}
              <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <button className="Primary-Button" onClick={submitAnswers} disabled={submitting || !takeAssessment.questions.length}>{submitting ? "Submitting..." : "Submit Answers"}</button>
                <button className="Soft-Button" onClick={() => { setTakeAssessment(null); setAnswers({}); }}>Cancel</button>
              </div>
            </div>
          </section>
        </div>
      )}
      {assessmentResult && (
        <div className="Modal-Backdrop" onClick={() => { setAssessmentResult(null); setAnswers({}); }}>
          <section className="Modal" onClick={(e) => e.stopPropagation()} style={{ width: "min(600px, calc(100vw - 56px))" }}>
            <div className="Modal-Body" style={{ maxHeight: "80vh", overflow: "auto" }}>
              <h2>Assessment Results</h2>
              <div style={{ textAlign: "center", padding: "24px 0" }}>
                <div style={{ fontSize: 48, fontWeight: 700, color: assessmentResult.score >= 70 ? "#10b981" : "#ef4444" }}>{assessmentResult.score}%</div>
                <p style={{ color: "#64748b", fontSize: 14 }}>{assessmentResult.correct} of {assessmentResult.total} Correct Answers</p>
              </div>
              {assessmentResult.details.map((d, i) => (
                <div key={i} style={{ marginBottom: 12, padding: 12, borderRadius: 8, border: "1px solid", borderColor: d.isCorrect ? "#bbf7d0" : "#fecaca", background: d.isCorrect ? "#f0fdf4" : "#fef2f2" }}>
                  <p style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>Q{i + 1}. {d.question}</p>
                  {d.options.map((opt, oi) => (
                    <div key={oi} style={{ fontSize: 12, padding: "3px 8px", marginBottom: 2, borderRadius: 4, background: oi === d.correct ? "#bbf7d0" : oi === Number(d.selected) && !d.isCorrect ? "#fecaca" : "transparent" }}>
                      {opt} {oi === d.correct ? " ✓" : ""} {oi === Number(d.selected) && !d.isCorrect ? " ✗" : ""}
                    </div>
                  ))}
                </div>
              ))}
              <button className="Primary-Button" onClick={() => { setAssessmentResult(null); setTakeAssessment(null); setAnswers({}); }} style={{ marginTop: 12 }}>Close</button>
            </div>
          </section>
        </div>
      )}
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
      const payload = {
        title: form.title,
        assessment_type: form.assessment_type,
        status: form.status,
        instructions: form.instructions,
        passing_score: Number(form.passing_score) || 0,
        duration_minutes: Number(form.duration_minutes) || 0,
        question_payload: form.questions,
      };
      if (form.department) payload.department = form.department;
      await apiPost("/Assesment/AssessmentTemplates/", payload);
      reload(["assessmentTemplates", "assessmentAssignments", "assessmentLegacy"]);
      onClose();
    } catch (err) {
      const codeErr = err?.payload?.code?.[0];
      const titleErr = err?.payload?.title?.[0];
      const typeErr = err?.payload?.assessment_type?.[0];
      const deptErr = err?.payload?.department?.[0];
      const qpErr = err?.payload?.question_payload?.[0];
      const detail = codeErr || titleErr || typeErr || deptErr || qpErr || err?.payload?.detail || err?.message || "Failed To Create Template.";
      setError(detail);
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

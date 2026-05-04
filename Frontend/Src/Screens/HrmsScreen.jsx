import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle, Briefcase, CheckCircle, ChevronDown, ChevronUp,
  Clock, FileText, Info, Menu, MoreHorizontal, Search, Target,
  TrendingUp, Users, X, Zap,
} from "lucide-react";

import { EmptyState, MilestoneRail, Modal, Panel, Progress, SimpleTable, Tabs } from "./Shared/ScreenComponents.jsx";
import { apiPatch, apiPost } from "../Api/Client.js";
import {
  calendarDays, filterForEmployee, findDailyStatus, formatDate,
  groupBy, indexById, isCompleted, isoDate, lastDays, money, progressForTask,
  projectName, toggleSet,
} from "./Shared/ScreenUtils.jsx";

/* ─── colour helpers ─────────────────────────────────────────── */
const AVATAR_COLORS = ["#6366f1","#0ea5e9","#10b981","#f59e0b","#ec4899","#8b5cf6","#14b8a6","#f97316"];
function avatarColor(name = "") {
  let n = 0;
  for (let i = 0; i < name.length; i += 1) n += name.charCodeAt(i);
  return AVATAR_COLORS[n % AVATAR_COLORS.length];
}
function initials(name = "") {
  return name.trim().split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "?";
}

/* ─── HrmsScreen ─────────────────────────────────────────────── */
export function HrmsScreen({ data, reload }) {
  const [tab, setTab]           = useState("team");
  const [search, setSearch]     = useState("");
  const [expanded, setExpanded] = useState(new Set());
  const [eodEmployee, setEodEmployee] = useState(null);
  const [goalEmployee, setGoalEmployee] = useState(null);
  const [showGoalModal, setShowGoalModal] = useState(false);

  const employees   = (data.employees || []).filter((e) =>
    e.display_name?.toLowerCase().includes(search.toLowerCase()) ||
    e.department_name?.toLowerCase().includes(search.toLowerCase()),
  );
  const departments = groupBy(employees, (e) => e.department_name || "Unassigned");

  const totalEmp   = (data.employees || []).length;
  const activeEmp  = (data.employees || []).filter((e) => e.status === "Active").length;
  const benchEmp   = (data.employees || []).filter((e) => e.status === "OnBench").length;
  const deptCount  = new Set((data.employees || []).map((e) => e.department_name).filter(Boolean)).size;

  useEffect(() => {
    if (!expanded.size && departments.size)
      setExpanded(new Set([departments.keys().next().value]));
  }, [departments.size]);

  const toggleAll = () =>
    expanded.size === departments.size
      ? setExpanded(new Set())
      : setExpanded(new Set(Array.from(departments.keys())));

  return (
    <section className="hrms-v2">
      {/* ── Hero ── */}
      <div className="hrms-hero">
        <div className="hrms-hero-left">
          <span className="hrms-kicker">Human Resources</span>
          <h1 className="hrms-hero-title">Team Management</h1>
          <p className="hrms-hero-sub">Workforce Overview, EOD Tracking, And Project Health.</p>
          <button className="primary-button" onClick={() => setShowGoalModal(true)} style={{ marginTop: "12px" }}>
            <Target size={14} /> Assign Goal
          </button>
        </div>
        <div className="hrms-kpi-row">
          {[
            { label: "Total", value: totalEmp,  cls: "" },
            { label: "Active", value: activeEmp, cls: "green" },
            { label: "On Bench", value: benchEmp, cls: "gold" },
            { label: "Departments", value: deptCount, cls: "blue" },
          ].map(({ label, value, cls }) => (
            <div key={label} className={`hrms-kpi ${cls}`}>
              <strong>{value}</strong>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="hrms-tab-shell">
        <Tabs
          value={tab}
          onChange={setTab}
          items={[["team", "Team"], ["sanity", "Project Sanity"], ["finance", "Project Finance"]]}
        />
      </div>

      {/* ── Team ── */}
      {tab === "team" && (
        <div className="hrms-body">
          <div className="hrms-toolbar">
            <div className="hrms-search">
              <Search size={16} />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search Employees Or Departments…"
              />
            </div>
            <button className="outline-button" onClick={toggleAll}>
              <Menu size={14} />
              {expanded.size === departments.size ? "Collapse All" : "Expand All"}
            </button>
          </div>
          <div className="hrms-dept-stack">
            {Array.from(departments.entries()).map(([deptName, rows]) => {
              const assigned     = rows.filter((e) => e.status === "Active").length;
              const bench        = rows.filter((e) => e.status === "OnBench").length;
              const notAssigned  = Math.max(rows.length - assigned - bench, 0);
              const isOpen       = expanded.has(deptName);
              return (
                <div className="hrms-dept-card" key={deptName}>
                  <button
                    className="hrms-dept-head"
                    onClick={() => setExpanded(toggleSet(expanded, deptName))}
                  >
                    <div className="hrms-dept-left">
                      <span className="hrms-dept-icon"><Users size={16} /></span>
                      <strong>{deptName}</strong>
                      <span className="hrms-dept-badge">{rows.length}</span>
                    </div>
                    <div className="hrms-dept-right">
                      <span className="hrms-pill green">Assigned: {assigned}</span>
                      <span className="hrms-pill red">Not Assigned: {notAssigned}</span>
                      <span className="hrms-pill slate">On-Bench: {bench}</span>
                      {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  </button>
                  {isOpen && (
                    <HrmsTeamTable
                      rows={rows}
                      data={data}
                      setEodEmployee={setEodEmployee}
                      setGoalEmployee={setGoalEmployee}
                      reload={reload}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {tab === "sanity"  && <ProjectSanity  data={data} />}
      {tab === "finance" && <ProjectFinance data={data} />}

      {eodEmployee && (
        <EodSummaryModal
          employee={eodEmployee}
          data={data}
          onClose={() => setEodEmployee(null)}
          reload={reload}
        />
      )}
      {goalEmployee && (
        <GoalOverviewModal
          employee={goalEmployee}
          data={data}
          onClose={() => setGoalEmployee(null)}
        />
      )}
      {showGoalModal && (
        <GoalAssignModal
          data={data}
          onClose={() => setShowGoalModal(false)}
          reload={reload}
        />
      )}
    </section>
  );
}

/* ─── HrmsTeamTable ──────────────────────────────────────────── */
function HrmsTeamTable({ rows, data, setEodEmployee, setGoalEmployee, reload }) {
  return (
    <div className="hrms-table-wrap">
      <table className="hrms-emp-table">
        <thead>
          <tr>
            <th>Name / Joining Date</th>
            <th>Skill Level</th>
            <th>Project</th>
            <th>Remarks</th>
            <th>BA</th>
            <th>BC (This Month)</th>
            <th>EOD &amp; Attendance</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((emp) => (
            <EmployeeRow
              key={emp.id}
              employee={emp}
              data={data}
              setEodEmployee={setEodEmployee}
              setGoalEmployee={setGoalEmployee}
              reload={reload}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─── EmployeeRow ────────────────────────────────────────────── */
const PERF_OPTIONS = [
  { label: "Good Performer",   color: "#10b981" },
  { label: "Medium Performer", color: "#f59e0b" },
  { label: "Low Performer",    color: "#f97316" },
  { label: "On Notice",        color: "#ef4444" },
  { label: "On Bench",         color: "#94a3b8" },
];

function EmployeeRow({ employee, data, setEodEmployee, setGoalEmployee, reload }) {
  const [showPerfMenu, setShowPerfMenu] = useState(false);
  const [showSkillMenu, setShowSkillMenu] = useState(false);
  const [showMenu,     setShowMenu]     = useState(false);
  const [eodPopover,   setEodPopover]   = useState(null); // iso date string or null
  const [saving,       setSaving]       = useState(false);
  const menuRef   = useRef(null);
  const perfRef   = useRef(null);
  const remarkRef = useRef(null);

  const days       = lastDays(7);
  const projectMap = indexById(data.projects);
  const assignments = (data.teamAssignments || []).filter(
    (a) => String(a.employee) === String(employee.id),
  );
  const skillOptions = (data.skills || []).filter(
    (item) => !item.department || String(item.department) === String(employee.department),
  );
  const skills = (data.userSkills || []).filter(
    (s) => String(s.employee) === String(employee.id),
  );
  const empProjects = assignments
    .map((a) => projectMap.get(String(a.project))?.name)
    .filter(Boolean);

  const skill     = skills[0];
  const prof      = skill?.proficiency ?? 1;
  const profLabel = prof >= 3 ? "Advanced" : prof >= 2 ? "Intermediate" : "Basic";
  const profCls   = prof >= 3 ? "adv" : prof >= 2 ? "mid" : "bas";

  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setShowMenu(false);
      if (perfRef.current && !perfRef.current.contains(e.target)) setShowPerfMenu(false);
      if (!e.target.closest?.(".hrms-skill-wrap")) setShowSkillMenu(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const saveRemark = useCallback(async () => {
    if (!remarkRef.current || saving) return;
    setSaving(true);
    try {
      await apiPatch(`/Users/EmployeeProfiles/${employee.id}/`, {
        profile_payload: { ...employee.profile_payload, remarks: remarkRef.current.value },
      });
      if (reload) reload(["employees", "notifications"]);
    } catch { /* silent */ }
    setSaving(false);
  }, [employee.id, employee.profile_payload, saving, reload]);

  const patchProfilePayload = async (patch) => {
    await apiPatch(`/Users/EmployeeProfiles/${employee.id}/`, {
      profile_payload: { ...employee.profile_payload, ...patch },
    });
    if (reload) reload(["employees", "notifications"]);
  };

  const savePerformance = async (label) => {
    setSaving(true);
    try {
      await patchProfilePayload({ performance: label || "" });
      setShowPerfMenu(false);
    } finally {
      setSaving(false);
    }
  };

  const saveSkillLevel = async (proficiency) => {
    const skillId = skill?.skill || skillOptions[0]?.id;
    if (!skillId || saving) return;
    setSaving(true);
    try {
      await apiPost(`/Users/EmployeeProfiles/${employee.id}/assign-skill/`, {
        skill: skillId,
        proficiency,
        rating: Math.min(proficiency * 3, 10),
      });
      setShowSkillMenu(false);
      if (reload) reload(["employees", "userSkills", "notifications"]);
    } finally {
      setSaving(false);
    }
  };

  const assignGoal = async () => {
    const due = new Date();
    due.setDate(due.getDate() + 14);
    setSaving(true);
    try {
      await apiPost("/Users/Goals/", {
        employee: employee.id,
        title: `HRMS Follow Up For ${employee.display_name}`,
        description: "Created From HRMS Action Menu.",
        due_on: isoDate(due),
        status: "Open",
        metadata: { source: "hrms-action-menu" },
      });
      if (reload) reload(["goals", "employees", "notifications"]);
    } finally {
      setSaving(false);
      setShowMenu(false);
    }
  };

  const sendInterview = async () => {
    if (!employee.user || saving) return;
    setSaving(true);
    try {
      await apiPost(`/Users/api/interviewgod/send-interview/${employee.user}/`, { dry_run: false, send_links: true });
      if (reload) reload(["employees"]);
    } finally {
      setSaving(false);
      setShowMenu(false);
    }
  };

  const ic = initials(employee.display_name);
  const ac = avatarColor(employee.display_name);
  const currentPerformance = employee.profile_payload?.performance || "";
  const perfMatch = PERF_OPTIONS.find((opt) => opt.label === currentPerformance);
  const perfColor = perfMatch?.color || "transparent";

  return (
    <tr className="hrms-emp-row" style={{ borderLeft: perfMatch ? `4px solid ${perfColor}` : "4px solid transparent" }}>
      {/* Name */}
      <td>
        <div className="hrms-name-cell">
          <span className="hrms-avatar" style={{ background: ac }}>{ic}</span>
          <div className="hrms-name-stack" ref={perfRef}>
            <button
              className="hrms-name-btn"
              onClick={() => setShowPerfMenu(!showPerfMenu)}
            >
              {perfMatch && <span className="hrms-perf-dot" style={{ background: perfMatch.color }} />}
              <strong>{employee.display_name}</strong>
              {showPerfMenu ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
            <small className="hrms-join-date">Joined: {formatDate(employee.joined_on)}</small>
            {showPerfMenu && (
              <div className="hrms-perf-menu">
                <button
                  className="hrms-perf-close"
                  onClick={() => setShowPerfMenu(false)}
                >
                  <X size={13} />
                </button>
                {PERF_OPTIONS.map((opt) => (
                  <button 
                    key={opt.label} 
                    className={`hrms-perf-opt ${currentPerformance === opt.label ? "active" : ""}`}
                    onClick={() => savePerformance(opt.label)} 
                    disabled={saving}
                  >
                    <span className="hrms-perf-dot" style={{ background: opt.color }} />
                    {opt.label}
                    {currentPerformance === opt.label && <CheckCircle size={14} />}
                  </button>
                ))}
                <button className="hrms-perf-opt muted" onClick={() => savePerformance("")} disabled={saving}>
                  {saving ? "Saving..." : "Unselect"}
                </button>
              </div>
            )}
          </div>
          <button className="hrms-info-btn" title="View Profile">
            <Info size={14} />
          </button>
        </div>
      </td>

      {/* Skill */}
      <td>
        <div className="hrms-skill-wrap">
          <button 
            className={`hrms-skill-badge ${profCls} ${saving ? "saving" : ""}`} 
            onClick={() => !saving && setShowSkillMenu(!showSkillMenu)} 
            title={skill?.skill_name || "Assign Skill Level"}
            disabled={saving}
            style={{ boxShadow: perfMatch ? `0 0 0 2px ${perfColor}33` : "none" }}
          >
            <AlertTriangle size={11} />
            {saving ? "Saving..." : profLabel}
            <ChevronDown size={11} />
          </button>
          {showSkillMenu && (
            <div className="hrms-skill-menu">
              <strong>{skill?.skill_name || skillOptions[0]?.name || "Department Skill"}</strong>
              {[
                [1, "Basic"],
                [2, "Intermediate"],
                [3, "Advanced"],
              ].map(([value, label]) => (
                <button 
                  key={value} 
                  className={prof === value ? "active" : ""}
                  onClick={() => saveSkillLevel(value)} 
                  disabled={saving}
                >
                  {label}
                  {prof === value && <CheckCircle size={14} />}
                </button>
              ))}
              {!skill?.skill && !skillOptions.length && <small>No Skill Exists For This Department.</small>}
            </div>
          )}
        </div>
      </td>

      {/* Projects */}
      <td>
        <div className="hrms-proj-stack">
          {empProjects.length
            ? empProjects.slice(0, 3).map((name) => (
                <span key={name} className="hrms-proj-tag">{name}</span>
              ))
            : <span className="hrms-no-proj">—</span>}
        </div>
      </td>

      {/* Remarks */}
      <td>
        <textarea
          ref={remarkRef}
          className="hrms-remark"
          defaultValue={employee.profile_payload?.remarks || ""}
          placeholder="Add Remarks…"
          onBlur={saveRemark}
        />
      </td>

      {/* BA / BC */}
      <td className="hrms-num">0</td>
      <td className="hrms-num">0</td>

      {/* EOD & Attendance */}
      <td>
        <div className="hrms-att-cell">
          <div className="hrms-att-strip">
            {days.map((day) => {
              const ds = findDailyStatus(data.dailyStatus, employee.id, day.iso);
              const isOpen = eodPopover === day.iso;
              return (
                <div key={day.iso} className="hrms-att-wrap" onMouseLeave={() => setEodPopover(null)}>
                  <button
                    className={`hrms-att-day ${ds ? "submitted" : "missing"}`}
                    onClick={() => setEodPopover(isOpen ? null : day.iso)}
                    onMouseEnter={() => setEodPopover(day.iso)}
                    title={day.iso}
                  >
                    {day.label}
                  </button>
                  {isOpen && (
                    <div className="hrms-eod-pop">
                      <button
                        className="hrms-eod-pop-close"
                        onClick={() => setEodPopover(null)}
                      >
                        <X size={13} />
                      </button>
                      <strong className="hrms-eod-pop-name">{employee.display_name}</strong>
                      <small className="hrms-eod-pop-date">{day.iso} · EOD Report</small>
                      {ds ? (
                        <div className="hrms-eod-pop-project">
                          <span>{ds.metadata?.project || "Project"}</span>
                          <p>{ds.summary || "No Summary Provided."}</p>
                        </div>
                      ) : (
                        <div className="hrms-eod-pop-project missing">
                          <span>No EOD Submitted</span>
                          <p>Use View More To Submit Or Review The Full EOD Calendar.</p>
                        </div>
                      )}
                      <div className={`hrms-eod-pop-status ${ds ? "" : "missing"}`}>
                        <span className="dot" /> {ds ? "Submitted" : "Missing"}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <button
            className="hrms-view-more"
            onClick={() => setEodEmployee(employee)}
          >
            View More <ChevronDown size={14} />
          </button>
        </div>
      </td>

      {/* Actions */}
      <td>
        <div className="hrms-action-wrap" ref={menuRef}>
          <button
            className="icon-button"
            onClick={() => setShowMenu(!showMenu)}
          >
            <MoreHorizontal size={16} />
          </button>
          {showMenu && (
            <div className="hrms-ctx-menu">
              <button onClick={assignGoal} disabled={saving}>
                <Target size={13} /> Assign Goal
              </button>
              <button onClick={() => { setGoalEmployee(employee); setShowMenu(false); }}>
                <Clock size={13} /> Goal Overview
              </button>
              <button
                onClick={() => { setEodEmployee(employee); setShowMenu(false); }}
              >
                <FileText size={13} /> EOD Summary
              </button>
              <button onClick={sendInterview} disabled={saving || !employee.user}>
                <Zap size={13} /> Send Interview
              </button>
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}

function GoalOverviewModal({ employee, data, onClose }) {
  const goals = (data.goals || []).filter((goal) => String(goal.employee) === String(employee.id));
  const feedback = data.goalFeedback || [];

  return (
    <Modal onClose={onClose} wide title={`${employee.display_name} Goals`}>
      <div className="eod-tab-body">
        {goals.length ? (
          <SimpleTable
            columns={["Goal", "Status", "Due On", "Feedback"]}
            rows={goals.map((goal) => [
              goal.title,
              goal.status,
              formatDate(goal.due_on),
              feedback.filter((item) => String(item.goal) === String(goal.id)).length,
            ])}
          />
        ) : (
          <EmptyState label="No Goals Assigned Yet." />
        )}
      </div>
    </Modal>
  );
}

/* ─── GoalAssignModal ────────────────────────────────────────── */
function GoalAssignModal({ data, onClose, reload }) {
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    employee: "",
    title: "",
    description: "",
    due_on: "",
    status: "Open",
  });
  const [errors, setErrors] = useState({});

  const employees = data.employees || [];
  const today = new Date().toISOString().split("T")[0];

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.employee) newErrors.employee = "Please select an employee";
    if (!formData.title.trim()) newErrors.title = "Please enter a goal title";
    if (!formData.description.trim()) newErrors.description = "Please enter a goal description";
    if (!formData.due_on) newErrors.due_on = "Please select a due date";
    return newErrors;
  };

  const handleSubmit = async () => {
    const newErrors = validate();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setSubmitting(true);
    try {
      await apiPost("/Users/Goals/", {
        employee: formData.employee,
        title: formData.title,
        description: formData.description,
        due_on: formData.due_on,
        status: formData.status,
        metadata: { source: "hrms-goal-modal" },
      });
      if (reload) reload(["goals", "employees", "notifications"]);
      onClose();
    } catch (error) {
      setErrors({ submit: error.message || "Failed to create goal" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal onClose={onClose} title="Assign Goal">
      <div style={{ display: "grid", gap: "16px", padding: "8px 0" }}>
        {/* Employee Selector */}
        <div>
          <label className="form-label">
            Employee <span style={{ color: "var(--danger)" }}>*</span>
          </label>
          <select
            className={`form-input ${errors.employee ? "error" : ""}`}
            value={formData.employee}
            onChange={(e) => handleChange("employee", e.target.value)}
          >
            <option value="">Select Employee</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.display_name} ({emp.department_name || "No Department"})
              </option>
            ))}
          </select>
          {errors.employee && <small className="error-text">{errors.employee}</small>}
        </div>

        {/* Goal Title */}
        <div>
          <label className="form-label">
            Goal Title <span style={{ color: "var(--danger)" }}>*</span>
          </label>
          <input
            type="text"
            className={`form-input ${errors.title ? "error" : ""}`}
            placeholder="Enter goal title"
            value={formData.title}
            onChange={(e) => handleChange("title", e.target.value)}
          />
          {errors.title && <small className="error-text">{errors.title}</small>}
        </div>

        {/* Goal Description */}
        <div>
          <label className="form-label">
            Goal Description <span style={{ color: "var(--danger)" }}>*</span>
          </label>
          <textarea
            className={`form-input ${errors.description ? "error" : ""}`}
            placeholder="Enter goal description"
            value={formData.description}
            onChange={(e) => handleChange("description", e.target.value)}
            rows={4}
            style={{ resize: "vertical", minHeight: "80px" }}
          />
          {errors.description && <small className="error-text">{errors.description}</small>}
        </div>

        {/* Due Date and Status Row */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <label className="form-label">
              Due Date <span style={{ color: "var(--danger)" }}>*</span>
            </label>
            <input
              type="date"
              className={`form-input ${errors.due_on ? "error" : ""}`}
              value={formData.due_on}
              onChange={(e) => handleChange("due_on", e.target.value)}
              min={today}
            />
            {errors.due_on && <small className="error-text">{errors.due_on}</small>}
          </div>

          <div>
            <label className="form-label">Status</label>
            <select
              className="form-input"
              value={formData.status}
              onChange={(e) => handleChange("status", e.target.value)}
            >
              <option value="Open">Open</option>
              <option value="InProgress">In Progress</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Error Message */}
        {errors.submit && (
          <div className="error-banner">
            <AlertTriangle size={14} />
            <span>{errors.submit}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "8px" }}>
          <button className="outline-button" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button className="primary-button" onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Assigning..." : "Assign Goal"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

/* ─── EodSummaryModal ────────────────────────────────────────── */
function EodSummaryModal({ employee, data, onClose, reload }) {
  const [tab, setTab]         = useState("calendar");
  const [calMonth, setCalMonth] = useState(new Date());
  const [submitting, setSubmitting] = useState(false);
  const [eodText, setEodText] = useState("");

  const statuses  = (data.dailyStatus || []).filter(
    (s) => String(s.employee) === String(employee.id),
  );
  const tasks     = filterForEmployee(data.tasks, employee.id);
  const monthDays = calendarDays(calMonth);
  const monthLabel = calMonth.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  const today     = isoDate(new Date());
  const orderedTasks = [...tasks].sort((left, right) => Number(left.bounty || 0) - Number(right.bounty || 0) || new Date(left.due_at || 0) - new Date(right.due_at || 0));
  const completedTasks = orderedTasks.filter((task) => isCompleted(task.status)).length;
  const averageProgress = orderedTasks.length
    ? Math.round(orderedTasks.reduce((sum, task) => sum + progressForTask(task, data.tasks || []), 0) / orderedTasks.length)
    : 0;
  const totalBountyCount = orderedTasks.reduce((sum, task) => sum + Number(task.bounty || 0), 0);
  const credentials = employee.profile_payload?.demo_credentials || null;

  const prevMonth = () =>
    setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() - 1, 1));
  const nextMonth = () =>
    setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() + 1, 1));

  const submitEod = async () => {
    if (!eodText.trim() || submitting) return;
    setSubmitting(true);
    try {
      await apiPost("/TasksDashboard/DailyStatusEntries/", {
        employee: employee.id,
        status_date: today,
        summary: eodText.trim(),
      });
      setEodText("");
      if (reload) reload(["dailyStatus"]);
    } catch { /* silent */ }
    setSubmitting(false);
  };

  const ic = initials(employee.display_name);
  const ac = avatarColor(employee.display_name);
  const todayStatus = findDailyStatus(statuses, employee.id, today);

  return (
    <Modal onClose={onClose} wide title="">
      <div className="eod-modal-hero">
        <span className="eod-modal-avatar" style={{ background: ac }}>{ic}</span>
        <div>
          <h2 className="eod-modal-name">{employee.display_name}</h2>
          <p className="eod-modal-sub">
            {employee.department_name || "—"} · Joined {formatDate(employee.joined_on)}
          </p>
        </div>
        <div className="eod-modal-today">
          {todayStatus
            ? <span className="hrms-pill green"><CheckCircle size={12} /> EOD Submitted Today</span>
            : <span className="hrms-pill red">No EOD Today</span>}
        </div>
      </div>

      <div className="eod-kpi-grid">
        <article className="eod-kpi-card">
          <span>Assigned Tasks</span>
          <strong>{orderedTasks.length}</strong>
          <small>Current Workload</small>
        </article>
        <article className="eod-kpi-card">
          <span>Completed</span>
          <strong>{completedTasks}</strong>
          <small>Finished Bounties</small>
        </article>
        <article className="eod-kpi-card">
          <span>Average Progress</span>
          <strong>{averageProgress}%</strong>
          <small>Status And Task Metadata</small>
        </article>
        <article className="eod-kpi-card">
          <span>Total Bounty Count</span>
          <strong>{totalBountyCount}</strong>
          <small>Numbered Bounties</small>
        </article>
        <article className="eod-credential-card">
          <span>Seed Login</span>
          <strong>{credentials?.username || employee.username || "—"}</strong>
          <small>User Id: {credentials?.user_id || employee.user || "—"}</small>
          <small>Password: {credentials?.password || "—"}</small>
        </article>
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        items={[["calendar", "Calendar"], ["submit", "Submit EOD"], ["bounties", "Bounties"], ["summaries", "EOD Summaries"]]}
      />

      {/* Calendar */}
      {tab === "calendar" && (
        <div className="eod-cal-wrap">
          <div className="eod-cal-nav">
            <button className="outline-button" onClick={prevMonth}>← Previous</button>
            <h3>{monthLabel}</h3>
            <button className="outline-button" onClick={nextMonth}>Next →</button>
          </div>
          <div className="eod-cal-grid">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
              <strong key={d} className="eod-cal-hdr">{d}</strong>
            ))}
            {monthDays.map((day, i) =>
              !day ? (
                <span key={i} />
              ) : (
                <button
                  key={i}
                  className={`eod-cal-day ${
                    findDailyStatus(statuses, employee.id, day.iso)
                      ? "submitted"
                      : day.future
                      ? "future"
                      : "empty"
                  }`}
                >
                  <strong>{day.day}</strong>
                  <small>{day.iso === today ? "Today" : ""}</small>
                </button>
              ),
            )}
          </div>
        </div>
      )}

      {/* Submit EOD */}
      {tab === "submit" && (
        <div className="eod-submit-wrap">
          <div className="eod-submit-card">
            <h3>Submit EOD Report For Today ({today})</h3>
            {todayStatus ? (
              <div className="eod-already-submitted">
                <CheckCircle size={20} />
                <div>
                  <strong>EOD Already Submitted</strong>
                  <p>{todayStatus.summary}</p>
                </div>
              </div>
            ) : (
              <>
                <textarea
                  value={eodText}
                  onChange={(e) => setEodText(e.target.value)}
                  placeholder="Describe What You Worked On Today…"
                  className="eod-text-input"
                />
                <button
                  className="primary-button"
                  onClick={submitEod}
                  disabled={submitting || !eodText.trim()}
                >
                  {submitting ? "Submitting…" : "Submit EOD"}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Bounties */}
      {tab === "bounties" && (
        <div className="eod-tab-body">
          {orderedTasks.length ? (
            <SimpleTable
              columns={["Bounty #", "Task", "Project", "Status", "Progress", "Due"]}
              rows={orderedTasks.slice(0, 20).map((task) => {
                const progress = Math.round(progressForTask(task, data.tasks || []));
                return [
                  Math.round(Number(task.bounty || 0)),
                  task.title,
                  projectName(data, task.project),
                  task.status,
                  <span key={`progress-${task.id}`} className="eod-progress-cell"><Progress value={progress} /><small>{progress}%</small></span>,
                  formatDate(task.due_at || task.updated_at || task.created_at),
                ];
              })}
            />
          ) : (
            <EmptyState label="No Bounties Assigned Yet." />
          )}
        </div>
      )}

      {/* EOD Summaries */}
      {tab === "summaries" && (
        <div className="eod-tab-body">
          <div className="eod-summary-list">
            {lastDays(14).reverse().map((day) => {
              const ds = findDailyStatus(statuses, employee.id, day.iso);
              return (
                <div key={day.iso} className={`eod-summary-row ${ds ? "has" : "no"}`}>
                  <div className="eod-sum-date"><strong>{day.iso}</strong></div>
                  {ds ? (
                    <div className="eod-sum-content">
                      <span className="eod-sum-proj">{ds.metadata?.project || "—"}</span>
                      <p>{ds.summary || "No Summary Text."}</p>
                    </div>
                  ) : (
                    <div className="eod-sum-content empty">No EOD Submitted</div>
                  )}
                  <span className={`eod-sum-badge ${ds ? "submitted" : "missing"}`}>
                    <span className="dot" />
                    {ds ? "Submitted" : "Missing"}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Modal>
  );
}

/* ─── ProjectSanity ──────────────────────────────────────────── */
function ProjectSanity({ data }) {
  const byProject = groupBy(data.milestones || [], (m) => String(m.project));
  return (
    <div className="hrms-body">
      <div className="hrms-sanity-list">
        {(data.projects || []).map((project) => {
          const milestones = byProject.get(String(project.id)) || [];
          const done = milestones.filter((m) => isCompleted(m.status)).length;
          const pct  = milestones.length
            ? Math.round((done / milestones.length) * 100)
            : 0;
          return (
            <div className="hrms-sanity-card" key={project.id}>
              <div className="hrms-sanity-left">
                <span className="hrms-sanity-priority">P{project.priority}</span>
                <div className="hrms-sanity-meta">
                  <strong>{project.name}</strong>
                  <small>{project.project_type || project.status || "—"}</small>
                </div>
              </div>
              <div className="hrms-sanity-mid">
                <MilestoneRail milestones={milestones} />
                <small className="hrms-milestone-ct">{done}/{milestones.length} Milestones</small>
              </div>
              <div className="hrms-sanity-right">
                <span className="hrms-pct">{pct}%</span>
                <span className={`hrms-health ${
                  project.health === "Escalated" ? "danger" :
                  project.health === "On Track"  ? "ok"     : ""
                }`}>
                  {project.health || "Null"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── ProjectFinance ─────────────────────────────────────────── */
function ProjectFinance({ data }) {
  const totalBounty = (data.tasks || []).reduce(
    (sum, t) => sum + Number(t.bounty || 0), 0,
  );
  return (
    <div className="hrms-body">
      <div className="hrms-fin-kpis">
        {[
          { icon: <Briefcase size={18} />, label: "Total Projects",    value: (data.projects || []).length },
          { icon: <CheckCircle size={18} />, label: "Total Tasks",     value: (data.tasks || []).length },
          { icon: <TrendingUp size={18} />, label: "Total Bounty",     value: Math.round(totalBounty) },
          { icon: <Users size={18} />,      label: "Team Assignments", value: (data.teamAssignments || []).length },
        ].map(({ icon, label, value }) => (
          <div key={label} className="hrms-fin-kpi">
            <span className="hrms-fin-icon">{icon}</span>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <Panel title="Project Finance Breakdown">
        <SimpleTable
          columns={["Project", "Health", "Team Size", "Tasks", "Bounty Pool"]}
          rows={(data.projects || []).map((project) => [
            project.name,
            project.health || "—",
            (data.teamAssignments || []).filter((a) => a.project === project.id).length,
            (data.tasks || []).filter((t) => t.project === project.id).length,
            "₹" + money(
              (data.tasks || [])
                .filter((t) => t.project === project.id)
                .reduce((sum, t) => sum + Number(t.bounty || 0), 0),
            ),
          ])}
        />
      </Panel>
    </div>
  );
}
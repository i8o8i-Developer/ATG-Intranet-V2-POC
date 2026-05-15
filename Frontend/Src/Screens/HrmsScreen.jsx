import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle, Briefcase, CheckCircle, ChevronDown, ChevronUp,
  Clock, FileText, Info, Menu, MoreHorizontal, Search, Target,
  TrendingUp, Users, X, Zap,
} from "lucide-react";

import { EmptyState, MilestoneRail, Modal, Panel, Progress, SimpleTable, Tabs } from "./Shared/ScreenComponents.jsx";
import { apiPatch, apiPost } from "../Api/Client.js";
import "../Styles/HrmsSanity.css";
import "../Styles/HrmsFinance.css";
import "../Styles/HrmsModal.css";
import {
  calendarDays, employeeName, filterForEmployee, findDailyStatus, formatDate,
  getAttendanceStatus, groupBy, indexById, isCompleted, isoDate, lastDays, money, progressForTask,
  projectName, toggleSet,
} from "./Shared/ScreenUtils.jsx";

/* ─── Colour Helpers ─────────────────────────────────────────── */
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
  const departments = groupBy(employees, (e) => e.department_name || "Not Assigned");

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
    <section className="Hrms-V2">
      {/* ── Hero ── */}
      <div className="Hrms-Hero">
        <div className="Hrms-Hero-Left">
          <span className="Hrms-Kicker">Human Resources</span>
          <h1 className="Hrms-Hero-Title">Team Management</h1>
          <p className="Hrms-Hero-Sub">Workforce Overview, EOD Tracking, And Project Health.</p>
          <div className="Hrms-Hero-Actions">
            <button className="Primary-Button" onClick={() => setTab("goals")} style={{ marginTop: "12px" }}>
              <Target size={14} /> Goals Workspace
            </button>
          </div>
        </div>
        <div className="Hrms-Kpi-Row">
          {[
            { label: "Total", value: totalEmp,  cls: "" },
            { label: "Active", value: activeEmp, cls: "green" },
            { label: "On Bench", value: benchEmp, cls: "gold" },
            { label: "Departments", value: deptCount, cls: "blue" },
          ].map(({ label, value, cls }) => (
            <div key={label} className={`Hrms-Kpi ${cls.charAt(0).toUpperCase() + cls.slice(1)}`}>
              <strong>{value}</strong>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="Hrms-Tab-Shell">
        <Tabs
          value={tab}
          onChange={setTab}
          items={[["team", "Team"], ["goals", "Goals"], ["sanity", "Project Sanity"], ["finance", "Project Finance"]]}
        />
      </div>

      {/* ── Team ── */}
      {tab === "team" && (
        <div className="Hrms-Body">
          <div className="Hrms-Toolbar">
            <div className="Hrms-Search">
              <Search size={16} />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search Employees Or Departments…"
              />
            </div>
            <button className="Outline-Button" onClick={toggleAll}>
              <Menu size={14} />
              {expanded.size === departments.size ? "Collapse All" : "Expand All"}
            </button>
          </div>
          <div className="Hrms-Dept-Stack">
            {Array.from(departments.entries()).map(([deptName, rows]) => {
              const assigned     = rows.filter((e) => e.status === "Active").length;
              const bench        = rows.filter((e) => e.status === "OnBench").length;
              const notAssigned  = Math.max(rows.length - assigned - bench, 0);
              const isOpen       = expanded.has(deptName);
              return (
                <div className="Hrms-Dept-Card" key={deptName}>
                  <button
                    className="Hrms-Dept-Head"
                    onClick={() => setExpanded(toggleSet(expanded, deptName))}
                  >
                    <div className="Hrms-Dept-Left">
                      <span className="Hrms-Dept-Icon"><Users size={16} /></span>
                      <div>
                        <strong>{deptName}</strong>
                        {(() => {
                          const lead = rows.find((e) => !e.manager) || rows[0];
                          return lead ? <span className="Hrms-Dept-Lead">Lead: {employeeName(data, lead.id)}</span> : null;
                        })()}
                      </div>
                      <span className="Hrms-Dept-Badge">{rows.length}</span>
                    </div>
                    <div className="Hrms-Dept-Right">
                      <span className="Hrms-Pill Green">Assigned: {assigned}</span>
                      <span className="Hrms-Pill Red">Not Assigned: {notAssigned}</span>
                      <span className="Hrms-Pill Slate">On Bench: {bench}</span>
                      {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  </button>
                  {isOpen && (
                    <HrmsTeamTable
                      rows={rows}
                      data={data}
                      setEodEmployee={setEodEmployee}
                      setGoalEmployee={setGoalEmployee}
                      setShowGoalModal={setShowGoalModal}
                      reload={reload}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {tab === "goals"   && <HrmsGoalsWorkspace data={data} setGoalEmployee={setGoalEmployee} reload={reload} />}
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
          defaultEmployeeId={showGoalModal === true ? null : showGoalModal}
          onClose={() => setShowGoalModal(false)}
          reload={reload}
        />
      )}
    </section>
  );
}

/* ─── HrmsTeamTable ──────────────────────────────────────────── */
function HrmsTeamTable({ rows, data, setEodEmployee, setGoalEmployee, setShowGoalModal, reload }) {
  return (
    <div className="Hrms-Table-Wrap">
      <table className="Hrms-Emp-Table">
        <thead>
          <tr>
            <th>Name / Joining Date</th>
            <th>Skill Level</th>
            <th>Project</th>
            <th>Remarks</th>
            <th>BA</th>
            <th>BC (This Month)</th>
            <th>EOD & Attendance</th>
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
              setShowGoalModal={setShowGoalModal}
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

function createGoalDraft(employee = "") {
  const due = new Date();
  due.setDate(due.getDate() + 14);
  return {
    employee,
    title: "",
    description: "",
    due_on: isoDate(due),
    status: "Open",
  };
}

function validateGoalDraft(formData) {
  const errors = {};
  if (!formData.employee) errors.employee = "Please Select An Employee";
  if (!formData.title.trim()) errors.title = "Please Enter A Goal Title";
  if (!formData.description.trim()) errors.description = "Please Enter A Goal Description";
  if (!formData.due_on) errors.due_on = "Please Select A Due Date";
  return errors;
}

function goalStatusMeta(status = "") {
  const normalized = String(status || "").toLowerCase();
  if (isCompleted(normalized)) return { label: "Completed", tone: "green", progress: 100 };
  if (normalized.includes("progress") || normalized.includes("review")) return { label: "In Progress", tone: "blue", progress: 68 };
  if (normalized.includes("cancel")) return { label: "Cancelled", tone: "slate", progress: 0 };
  return { label: status || "Open", tone: "gold", progress: 18 };
}

function isGoalOverdue(goal) {
  if (!goal?.due_on || isCompleted(goal?.status)) return false;
  const dueDate = new Date(goal.due_on);
  if (Number.isNaN(dueDate.getTime())) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return dueDate < today;
}

function EmployeeRow({ employee, data, setEodEmployee, setGoalEmployee, setShowGoalModal, reload }) {
  const [showPerfMenu, setShowPerfMenu] = useState(false);
  const [showSkillMenu, setShowSkillMenu] = useState(false);
  const [showMenu,     setShowMenu]     = useState(false);
  const [eodPopover,   setEodPopover]   = useState(null); 
  const [saving,       setSaving]       = useState(false);
  const [profilePayload, setProfilePayload] = useState(employee.profile_payload || {});
  const lastPropPayload = useRef(employee.profile_payload);

  const [optimisticSkill, setOptimisticSkill] = useState(null);
  const lastPropSkill = useRef(null);
  const [updatedField, setUpdatedField] = useState("");
  const menuRef   = useRef(null);
  const perfRef   = useRef(null);
  const remarkRef = useRef(null);
  const flashTimerRef = useRef(null);

  const days       = lastDays(7);
  const projectMap = indexById(data.projects);
  const assignments = (data.teamAssignments || []).filter(
    (a) => String(a.employee) === String(employee.id),
  );
  const skillOptions = (data.skills || []).filter(
    (item) => !item.department || String(item.department) === String(employee.department),
  );
  
  const departmentSkillId = skillOptions[0]?.id;
  const serverSkill = (data.userSkills || []).find(
    (us) => String(us.employee) === String(employee.id) && String(us.skill) === String(departmentSkillId)
  );

  const empProjects = assignments
    .map((a) => projectMap.get(String(a.project))?.name)
    .filter(Boolean);

  const skill     = optimisticSkill || serverSkill;
  const prof      = skill?.proficiency ?? 1;
  const profLabel = prof >= 3 ? "Advanced" : prof >= 2 ? "Intermediate" : "Basic";
  const profCls   = prof >= 3 ? "Adv" : prof >= 2 ? "Mid" : "Bas";
  const skillLabel = skill?.skill_name || skillOptions[0]?.name || "Department Skill";

  const now = new Date();
  const thisMonth = now.getMonth();
  const thisYear = now.getFullYear();
  const employeeTasks = (data.tasks || []).filter((t) => String(t.owner) === String(employee.id));
  const ba = employeeTasks.reduce((sum, t) => sum + Math.max(0, Number(t.bounty || 0)), 0);
  const bc = employeeTasks
    .filter((t) => isCompleted(t.status) && t.completed_at && new Date(t.completed_at).getMonth() === thisMonth && new Date(t.completed_at).getFullYear() === thisYear)
    .reduce((sum, t) => sum + Math.max(0, Number(t.bounty || 0)), 0);

  useEffect(() => {
    if (JSON.stringify(employee.profile_payload) !== JSON.stringify(lastPropPayload.current)) {
      setProfilePayload(employee.profile_payload || {});
      lastPropPayload.current = employee.profile_payload;
    }
  }, [employee.profile_payload]);

  useEffect(() => {
    const nextSkill = serverSkill ? {
      skill: serverSkill.skill,
      skill_name: serverSkill.skill_name,
      proficiency: serverSkill.proficiency,
      rating: serverSkill.rating,
    } : null;

    if (JSON.stringify(nextSkill) !== JSON.stringify(lastPropSkill.current)) {
      setOptimisticSkill(nextSkill);
      lastPropSkill.current = nextSkill;
    }
  }, [serverSkill?.skill, serverSkill?.skill_name, serverSkill?.proficiency, serverSkill?.rating]);

  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setShowMenu(false);
      if (perfRef.current && !perfRef.current.contains(e.target)) setShowPerfMenu(false);
      if (!e.target.closest?.(".Hrms-Skill-Wrap")) setShowSkillMenu(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => () => {
    if (flashTimerRef.current) window.clearTimeout(flashTimerRef.current);
  }, []);

  const markUpdated = (field) => {
    setUpdatedField(field);
    if (flashTimerRef.current) window.clearTimeout(flashTimerRef.current);
    flashTimerRef.current = window.setTimeout(() => setUpdatedField(""), 1200);
  };

  const saveRemark = useCallback(async () => {
    if (!remarkRef.current || saving) return;
    setSaving(true);
    const previousPayload = profilePayload;
    const nextPayload = { ...previousPayload, remarks: remarkRef.current.value };
    setProfilePayload(nextPayload);
    try {
      await apiPatch(`/Users/EmployeeProfiles/${employee.id}/`, {
        profile_payload: nextPayload,
      });
      if (reload) reload(["employees", "notifications"]);
    } catch {
      setProfilePayload(previousPayload);
    }
    setSaving(false);
  }, [employee.id, profilePayload, saving, reload]);

  const patchProfilePayload = async (patch) => {
    const previousPayload = profilePayload;
    const nextPayload = { ...previousPayload, ...patch };
    setProfilePayload(nextPayload);
    const response = await apiPatch(`/Users/EmployeeProfiles/${employee.id}/patch-payload/`, {
      profile_payload: nextPayload,
    });
    setProfilePayload(response?.profile_payload || nextPayload);
    return { previousPayload, nextPayload };
  };

  const changeEmployeeStatus = async (status) => {
    if (!employee.id) return;
    try {
      await apiPost(`/Users/EmployeeProfiles/${employee.id}/change-status/`, { status, reason: "" });
    } catch {
      // 
    }
  };

  const savePerformance = async (label) => {
    setSaving(true);
    try {
      markUpdated("performance");
      await patchProfilePayload({ performance_tag: label || "" });
      if (label === "On Bench") {
        if (employee.status !== "OnBench") {
          await changeEmployeeStatus("OnBench");
        }
      } else if (employee.status === "OnBench") {
        await changeEmployeeStatus("Active");
      }
      if (reload) reload(["employees", "notifications"]);
      setShowPerfMenu(false);
    } catch {
      setProfilePayload(employee.profile_payload || {});
    } finally {
      setSaving(false);
    }
  };

  const saveSkillLevel = async (proficiency) => {
    const skillId = skill?.skill || skillOptions[0]?.id;
    if (!skillId || saving) return;
    setSaving(true);
    const previousSkill = optimisticSkill;
    const nextSkill = {
      skill: skillId,
      skill_name: skillLabel,
      proficiency,
      rating: Math.min(proficiency * 3, 10),
    };
    setOptimisticSkill(nextSkill);
    markUpdated("skill");
    try {
      const response = await apiPost(`/Users/EmployeeProfiles/${employee.id}/assign-skill/`, {
        skill: skillId,
        proficiency,
        rating: Math.min(proficiency * 3, 10),
      });
      setOptimisticSkill(response || nextSkill);
      setShowSkillMenu(false);
      if (reload) reload(["employees", "userSkills", "notifications"]);
    } catch {
      setOptimisticSkill(previousSkill);
    } finally {
      setSaving(false);
    }
  };

  const assignGoal = () => {
    setShowGoalModal(employee.id);
    setShowMenu(false);
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
  const currentPerformance = profilePayload?.performance_tag || profilePayload?.performance || "";
  const perfMatch = PERF_OPTIONS.find((opt) => opt.label === currentPerformance);
  const perfColor = perfMatch?.color || "transparent";

  return (
    <tr className={`Hrms-Emp-Row${updatedField ? ` Hrms-Emp-Row-Updated Hrms-Emp-Row-Updated-${updatedField}` : ""}`} style={{ borderLeft: perfMatch ? `4px solid ${perfColor}` : "4px solid transparent" }}>
      {/* Name */}
      <td>
        <div className="Hrms-Name-Cell">
          <span className="Hrms-Avatar" style={{ background: ac }}>{ic}</span>
          <div className="Hrms-Name-Stack" ref={perfRef}>
            <button
              className="Hrms-Name-Btn"
              onClick={() => setShowPerfMenu(!showPerfMenu)}
            >
              {perfMatch && <span className="Hrms-Perf-Dot" style={{ background: perfMatch.color }} />}
              <strong>{employee.display_name}</strong>
              {showPerfMenu ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
            <small className="Hrms-Join-Date">Joined: {formatDate(employee.joined_on)}</small>
            <span className={`Hrms-Performance-Chip ${currentPerformance ? "" : "Empty"} ${updatedField === "performance" ? "Is-Updated" : ""}`}>
              {currentPerformance || "No Performance Tag"}
            </span>
            {showPerfMenu && (
              <div className="Hrms-Perf-Menu">
                <button
                  className="Hrms-Perf-Close"
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
                    <span className="Hrms-Perf-Dot" style={{ background: opt.color }} />
                    {opt.label}
                    {currentPerformance === opt.label && <CheckCircle size={14} />}
                  </button>
                ))}
                <button className="Hrms-Perf-Opt Muted" onClick={() => savePerformance("")} disabled={saving}>
                  {saving ? "Saving..." : "Unselect"}
                </button>
              </div>
            )}
          </div>
          <button className="Hrms-Info-Btn" title="View Profile">
            <Info size={14} />
          </button>
        </div>
      </td>

      {/* Skill */}
      <td>
        <div className="Hrms-Skill-Wrap">
          <button 
            className={`Hrms-Skill-Badge ${profCls} ${saving ? "saving" : ""} ${updatedField === "skill" ? "Is-Updated" : ""}`} 
            onClick={() => !saving && setShowSkillMenu(!showSkillMenu)} 
            title={skillLabel}
            disabled={saving}
            style={{ boxShadow: perfMatch ? `0 0 0 2px ${perfColor}33` : "none" }}
          >
            <AlertTriangle size={11} />
            {saving ? "Saving..." : profLabel}
            <ChevronDown size={11} />
          </button>
          <small className="Hrms-Skill-Caption">{skillLabel}</small>
          {showSkillMenu && (
            <div className="Hrms-Skill-Menu">
              <strong>{skillLabel}</strong>
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
        <div className="Hrms-Proj-Stack">
          {empProjects.length
            ? empProjects.slice(0, 3).map((name) => (
                <span key={name} className="Hrms-Proj-Tag">{name}</span>
              ))
            : <span className="Hrms-No-Proj">—</span>}
        </div>
      </td>

      {/* Remarks */}
      <td>
        <textarea
          ref={remarkRef}
          className="Hrms-Remark"
          defaultValue={employee.profile_payload?.remarks || ""}
          placeholder="Add Remarks…"
          onBlur={saveRemark}
        />
      </td>

      {/* BA / BC */}
      <td className="Hrms-Num">{ba}</td>
      <td className="Hrms-Num">{bc}</td>

      {/* EOD & Attendance */}
      <td>
        <div className="Hrms-Att-Cell">
          <div className="Hrms-Att-Strip">
            {days.map((day) => {
              const { type, entry: ds } = getAttendanceStatus(data.dailyStatus, data.leaveRequests, employee.id, day.iso);
              const isOpen = eodPopover === day.iso;
              const attClass = type === "leave" ? "leave" : ds ? "submitted" : "missing";
              return (
                <div key={day.iso} className="Hrms-Att-Wrap" onMouseLeave={() => setEodPopover(null)}>
                  <button
                    className={`Hrms-Att-Day ${attClass}`}
                    onClick={() => setEodPopover(isOpen ? null : day.iso)}
                    onMouseEnter={() => setEodPopover(day.iso)}
                    title={day.iso}
                  >
                    {day.label}
                  </button>
                  {isOpen && (
                    <div className="Hrms-Eod-Pop">
                      <button
                        className="Hrms-Eod-Pop-Close"
                        onClick={() => setEodPopover(null)}
                      >
                        <X size={13} />
                      </button>
                      <strong className="Hrms-Eod-Pop-Name">{employee.display_name}</strong>
                      <small className="Hrms-Eod-Pop-Date">{day.iso} · {type === "leave" ? "On Leave" : "EOD Report"}</small>
                      {type === "leave" ? (
                        <div className="Hrms-Eod-Pop-Project Leave">
                          <span>On Approved Leave</span>
                          <p>Employee Is On Approved Leave for this date.</p>
                        </div>
                      ) : ds ? (
                        <div className="Hrms-Eod-Pop-Project">
                          <span>{ds.metadata?.project || "Project"}</span>
                          <p>{ds.summary || "No Summary Provided."}</p>
                        </div>
                      ) : (
                        <div className="Hrms-Eod-Pop-Project Missing">
                          <span>No EOD Submitted</span>
                          <p>Use View More To Submit Or Review The Full EOD Calendar.</p>
                        </div>
                      )}
                      <div className={`Hrms-Eod-Pop-Status ${ds ? "" : type === "leave" ? "leave" : "missing"}`}>
                        <span className="dot" /> {type === "leave" ? "On Leave" : ds ? "Submitted" : "Missing"}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <button
            className="Hrms-View-More"
            onClick={() => setEodEmployee(employee)}
          >
            View More <ChevronDown size={14} />
          </button>
        </div>
      </td>

      {/* Actions */}
      <td>
        <div className="Hrms-Action-Wrap" ref={menuRef}>
          <button
            className="Icon-Button"
            onClick={() => setShowMenu(!showMenu)}
          >
            <MoreHorizontal size={16} />
          </button>
          {showMenu && (
            <div className="Hrms-Ctx-Menu">
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

function HrmsGoalsWorkspace({ data, setGoalEmployee, reload }) {
  const employees = data.employees || [];
  const employeeMap = indexById(employees);
  const feedback = data.goalFeedback || [];
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState(() => createGoalDraft());
  const [errors, setErrors] = useState({});
  const [goalRows, setGoalRows] = useState(data.goals || []);

  useEffect(() => {
    setGoalRows(data.goals || []);
  }, [data.goals]);

  const filteredGoals = goalRows.filter((goal) => {
    const employeeName = employeeMap.get(String(goal.employee))?.display_name || "";
    const haystack = `${goal.title || ""} ${goal.description || ""} ${goal.status || ""} ${employeeName}`.toLowerCase();
    return haystack.includes(query.toLowerCase());
  });
  const totalGoals = goalRows.length;
  const inProgressGoals = goalRows.filter((goal) => String(goal.status || "").toLowerCase().includes("progress") || String(goal.status || "").toLowerCase().includes("review")).length;
  const completedGoals = goalRows.filter((goal) => isCompleted(goal.status)).length;
  const overdueGoals = goalRows.filter(isGoalOverdue).length;

  const handleChange = (field, value) => {
    setFormData((current) => ({ ...current, [field]: value }));
    if (errors[field]) {
      setErrors((current) => ({ ...current, [field]: "" }));
    }
  };

  const handleSubmit = async () => {
    const nextErrors = validateGoalDraft(formData);
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }

    setSubmitting(true);
    try {
      const createdGoal = await apiPost("/Users/Goals/", {
        employee: formData.employee,
        title: formData.title,
        description: formData.description,
        due_on: formData.due_on,
        status: formData.status,
        metadata: { source: "Hrms Goals Workspace" },
      });
      setGoalRows((current) => [createdGoal, ...current.filter((goal) => String(goal.id) !== String(createdGoal?.id))]);
      setFormData(createGoalDraft(formData.employee));
      setErrors({});
      if (reload) reload(["goals", "goalFeedback", "employees", "notifications"]);
    } catch (error) {
      setErrors({ submit: error.message || "Failed To Create Goal" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="Hrms-Body">
      <div className="Hrms-Goal-Kpis">
        {[
          { label: "Total Goals", value: totalGoals, tone: "blue" },
          { label: "In Progress", value: inProgressGoals, tone: "gold" },
          { label: "Completed", value: completedGoals, tone: "green" },
          { label: "Overdue", value: overdueGoals, tone: overdueGoals ? "red" : "slate" },
        ].map((item) => (
          <article key={item.label} className={`hrms-goal-kpi ${item.tone}`}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </article>
        ))}
      </div>

      <div className="Hrms-Goals-Grid">
        <Panel title="Create And Assign Goal">
          <div className="Hrms-Goal-Form">
            <label>
              <span>Employee</span>
              <select className={`form-input ${errors.employee ? "error" : ""}`} value={formData.employee} onChange={(event) => handleChange("employee", event.target.value)}>
                <option value="">Select Employee</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>{emp.display_name} ({emp.department_name || "No Department"})</option>
                ))}
              </select>
              {errors.employee && <small className="Error-Text">{errors.employee}</small>}
            </label>
            <label>
              <span>Goal Title</span>
              <input className={`form-input ${errors.title ? "error" : ""}`} value={formData.title} onChange={(event) => handleChange("title", event.target.value)} placeholder="Enter Goal Title" />
              {errors.title && <small className="Error-Text">{errors.title}</small>}
            </label>
            <label>
              <span>Description</span>
              <textarea className={`form-input ${errors.description ? "error" : ""}`} value={formData.description} onChange={(event) => handleChange("description", event.target.value)} rows={5} placeholder="Describe The Goal, Expected Output, And Follow-Up Notes" />
              {errors.description && <small className="Error-Text">{errors.description}</small>}
            </label>
            <div className="Hrms-Goal-Form-Row">
              <label>
                <span>Due Date</span>
                <input type="date" className={`form-input ${errors.due_on ? "error" : ""}`} value={formData.due_on} onChange={(event) => handleChange("due_on", event.target.value)} min={isoDate(new Date())} />
                {errors.due_on && <small className="Error-Text">{errors.due_on}</small>}
              </label>
              <label>
                <span>Status</span>
                <select className="Form-Input" value={formData.status} onChange={(event) => handleChange("status", event.target.value)}>
                  <option value="Open">Open</option>
                  <option value="InProgress">In Progress</option>
                  <option value="Completed">Completed</option>
                  <option value="Cancelled">Cancelled</option>
                </select>
              </label>
            </div>
            {errors.submit && (
              <div className="Error-Banner">
                <AlertTriangle size={14} />
                <span>{errors.submit}</span>
              </div>
            )}
            <div className="Hrms-Goal-Actions-Row">
              <button className="Outline-Button" onClick={() => { setFormData(createGoalDraft()); setErrors({}); }} disabled={submitting}>Reset</button>
              <button className="Primary-Button" onClick={handleSubmit} disabled={submitting}>{submitting ? "Assigning..." : "Assign Goal"}</button>
            </div>
          </div>
        </Panel>

        <Panel
          title="Assigned Goals"
          right={
            <div className="Hrms-Goal-Toolbar">
              <div className="Hrms-Search Hrms-Goal-Search">
                <Search size={16} />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search By Goal, Employee, Or Status" />
              </div>
            </div>
          }
        >
          {filteredGoals.length ? (
            <SimpleTable
              columns={["Goal", "Employee", "Status", "Progress", "Due", "Feedback", "Action"]}
              rows={filteredGoals.map((goal) => {
                const employee = employeeMap.get(String(goal.employee));
                const meta = goalStatusMeta(goal.status);
                const overdue = isGoalOverdue(goal);
                const feedbackCount = feedback.filter((item) => String(item.goal) === String(goal.id)).length;
                return [
                  <div key={`goal-${goal.id}`} className="Hrms-Goal-Summary">
                    <strong>{goal.title}</strong>
                    <small>{goal.description || "No Description Provided."}</small>
                  </div>,
                  employee?.display_name || "—",
                  <span key={`status-${goal.id}`} className={`hrms-goal-status ${overdue ? "red" : meta.tone}`}>{overdue ? "Overdue" : meta.label}</span>,
                  <span key={`progress-${goal.id}`} className="Hrms-Goal-Progress"><Progress value={overdue ? Math.max(meta.progress - 10, 5) : meta.progress} /><small>{overdue ? Math.max(meta.progress - 10, 5) : meta.progress}%</small></span>,
                  formatDate(goal.due_on),
                  feedbackCount,
                  <span key={`action-${goal.id}`} className="Table-Actions">
                    <button className="Soft-Button Small" onClick={async () => { await apiPost(`/Users/Goals/${goal.id}/`, { ...goal, status: "InProgress" }); if (reload) reload(["goals", "goalFeedback"]); }}>Start</button>
                    <button className="Soft-Button Small" onClick={async () => { await apiPost("/Users/GoalFeedback/", { goal: goal.id, feedback_type: "ManagerApproval", rating: 5, note: "Goal Approved." }); if (reload) reload(["goals", "goalFeedback"]); }}>Approve</button>
                    <button className="Soft-Button Small" onClick={() => employee && setGoalEmployee(employee)}>View</button>
                  </span>,
                ];
              })}
            />
          ) : (
            <EmptyState label="No Goals Match The Current Search." />
          )}
        </Panel>
      </div>
    </div>
  );
}

function GoalOverviewModal({ employee, data, onClose }) {
  const goals = (data.goals || []).filter((goal) => String(goal.employee) === String(employee.id));
  const feedback = data.goalFeedback || [];

  return (
    <Modal onClose={onClose} wide title={`${employee.display_name} Goals`}>
      <div className="Eod-Tab-Body">
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
function GoalAssignModal({ data, defaultEmployeeId, onClose, reload }) {
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState(() => createGoalDraft(defaultEmployeeId || ""));
  const [errors, setErrors] = useState({});

  const employees = data.employees || [];
  const today = isoDate(new Date());

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const validate = () => {
    return validateGoalDraft(formData);
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
        metadata: { source: "Hrms Goal Modal" },
      });
      if (reload) reload(["goals", "employees", "notifications"]);
      onClose();
    } catch (error) {
      setErrors({ submit: error.message || "Failed To Create Goal" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal onClose={onClose} title="Assign Goal">
      <div style={{ display: "grid", gap: "16px", padding: "8px 0" }}>
        {/* Employee Selector */}
        <div>
          <label className="Form-Label">
            Employee <span style={{ color: "var(--red)" }}>*</span>
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
          {errors.employee && <small className="Error-Text">{errors.employee}</small>}
        </div>

        {/* Goal Title */}
        <div>
          <label className="Form-Label">
            Goal Title <span style={{ color: "var(--red)" }}>*</span>
          </label>
          <input
            type="text"
            className={`form-input ${errors.title ? "error" : ""}`}
            placeholder="Enter Goal Title"
            value={formData.title}
            onChange={(e) => handleChange("title", e.target.value)}
          />
          {errors.title && <small className="Error-Text">{errors.title}</small>}
        </div>

        {/* Goal Description */}
        <div>
          <label className="Form-Label">
            Goal Description <span style={{ color: "var(--red)" }}>*</span>
          </label>
          <textarea
            className={`form-input ${errors.description ? "error" : ""}`}
            placeholder="Enter Goal Description"
            value={formData.description}
            onChange={(e) => handleChange("description", e.target.value)}
            rows={4}
            style={{ resize: "vertical", minHeight: "80px" }}
          />
          {errors.description && <small className="Error-Text">{errors.description}</small>}
        </div>

        {/* Due Date And Status Row */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <label className="Form-Label">
              Due Date <span style={{ color: "var(--red)" }}>*</span>
            </label>
            <input
              type="date"
              className={`form-input ${errors.due_on ? "error" : ""}`}
              value={formData.due_on}
              onChange={(e) => handleChange("due_on", e.target.value)}
              min={today}
            />
            {errors.due_on && <small className="Error-Text">{errors.due_on}</small>}
          </div>

          <div>
            <label className="Form-Label">Status</label>
            <select
              className="Form-Input"
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
          <div className="Error-Banner">
            <AlertTriangle size={14} />
            <span>{errors.submit}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "8px" }}>
          <button className="Outline-Button" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button className="Primary-Button" onClick={handleSubmit} disabled={submitting}>
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
  const todayStr     = isoDate(new Date());
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
        status_date: todayStr,
        summary: eodText.trim(),
      });
      setEodText("");
      if (reload) reload(["dailyStatus"]);
    } catch { /* Silent */ }
    setSubmitting(false);
  };

  const ic = initials(employee.display_name);
  const ac = avatarColor(employee.display_name);
  const todayStatus = findDailyStatus(statuses, employee.id, todayStr);

  return (
    <Modal onClose={onClose} wide title="">
      <div className="Eod-Modal-Hero">
        <span className="Eod-Modal-Avatar" style={{ background: ac }}>{ic}</span>
        <div>
          <h2 className="Eod-Modal-Name">{employee.display_name}</h2>
          <p className="Eod-Modal-Sub">
            {employee.department_name || "—"} · Joined {formatDate(employee.joined_on)}
          </p>
        </div>
        <div className="Eod-Modal-Today">
          {todayStatus
            ? <span className="Hrms-Pill Green"><CheckCircle size={12} /> EOD Submitted Today</span>
            : <span className="Hrms-Pill Red">No EOD Today</span>}
        </div>
      </div>

      <div className="Eod-Kpi-Grid">
        <article className="Eod-Kpi-Card">
          <span>Assigned Tasks</span>
          <strong>{orderedTasks.length}</strong>
          <small>Current Workload</small>
        </article>
        <article className="Eod-Kpi-Card">
          <span>Completed</span>
          <strong>{completedTasks}</strong>
          <small>Finished Bounties</small>
        </article>
        <article className="Eod-Kpi-Card">
          <span>Average Progress</span>
          <strong>{averageProgress}%</strong>
          <small>Status And Task Metadata</small>
        </article>
        <article className="Eod-Kpi-Card">
          <span>Total Bounty Count</span>
          <strong>{totalBountyCount}</strong>
          <small>Numbered Bounties</small>
        </article>
        <article className="Eod-Credential-Card">
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
        <div className="Eod-Cal-Wrap">
          <div className="Eod-Cal-Nav">
            <button className="Outline-Button" onClick={prevMonth}>← Previous</button>
            <h3>{monthLabel}</h3>
            <button className="Outline-Button" onClick={nextMonth}>Next →</button>
          </div>
          <div className="Eod-Cal-Grid">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
              <strong key={d} className="Eod-Cal-Hdr">{d}</strong>
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
                  <small>{day.iso === todayStr ? "Today" : ""}</small>
                </button>
              ),
            )}
          </div>
        </div>
      )}

      {/* Submit EOD */}
      {tab === "submit" && (
        <div className="Eod-Submit-Wrap">
          <div className="Eod-Submit-Card">
            <h3>Submit EOD Report For Today ({todayStr})</h3>
            {todayStatus ? (
              <div className="Eod-Already-Submitted">
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
                  className="Eod-Text-Input"
                />
                <button
                  className="Primary-Button"
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
        <div className="Eod-Tab-Body">
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
                  <span key={`progress-${task.id}`} className="Eod-Progress-Cell"><Progress value={progress} /><small>{progress}%</small></span>,
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
        <div className="Eod-Tab-Body">
          <div className="Eod-Summary-List">
            {lastDays(14).reverse().map((day) => {
              const ds = findDailyStatus(statuses, employee.id, day.iso);
              return (
                <div key={day.iso} className={`eod-summary-row ${ds ? "has" : "no"}`}>
                  <div className="Eod-Sum-Date"><strong>{day.iso}</strong></div>
                  {ds ? (
                    <div className="Eod-Sum-Content">
                      <span className="Eod-Sum-Proj">{ds.metadata?.project || "—"}</span>
                      <p>{ds.summary || "No Summary Text."}</p>
                    </div>
                  ) : (
                    <div className="Eod-Sum-Content Empty">No EOD Submitted</div>
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

/* ─── Project Sanity ──────────────────────────────────────────── */
function ProjectSanity({ data }) {
  const byProject = groupBy(data.milestones || [], (m) => String(m.project));
  return (
    <div className="HS">
      {(data.projects || []).map((project) => {
        const milestones = byProject.get(String(project.id)) || [];
        const done = milestones.filter((m) => isCompleted(m.status)).length;
        const pct  = milestones.length
          ? Math.round((done / milestones.length) * 100)
          : 0;
        return (
          <div className="HS-Card" key={project.id}>
            <div className="HS-Left">
              <span className="HS-Priority">P{project.priority}</span>
              <div className="HS-Meta">
                <strong>{project.name}</strong>
                <small>{project.project_type || project.status || "—"}</small>
              </div>
            </div>
            <div className="HS-Mid">
              <MilestoneRail milestones={milestones} />
              <span className="HS-Count">{done}/{milestones.length} Milestones</span>
            </div>
            <div className="HS-Right">
              <span className="HS-Pct">{pct}%</span>
              <span className={`HS-Health ${
                project.health === "Escalated" ? "danger" :
                project.health === "On Track"  ? "ok"     : "null"
              }`}>
                {project.health || "Null"}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Project Finance ─────────────────────────────────────────── */
function ProjectFinance({ data }) {
  const totalBounty = (data.tasks || []).reduce(
    (sum, t) => sum + Number(t.bounty || 0), 0,
  );
  return (
    <div className="HF">
      <div className="HF-Kpis">
        {[
          { icon: <Briefcase size={20} />, label: "Total Projects",    value: (data.projects || []).length },
          { icon: <CheckCircle size={20} />, label: "Total Tasks",     value: (data.tasks || []).length },
          { icon: <TrendingUp size={20} />, label: "Total Bounty",     value: Math.round(totalBounty) },
          { icon: <Users size={20} />,      label: "Team Assignments", value: (data.teamAssignments || []).length },
        ].map(({ icon, label, value }) => (
          <div key={label} className="HF-Kpi">
            <div className="HF-KpiIcon">{icon}</div>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <div className="HF-TableWrap">
        <div className="HF-TableHead"><h2>Project Finance Breakdown</h2></div>
        <table className="HF-Table">
          <thead>
            <tr>
              <th>Project</th><th>Health</th><th>Team Size</th><th>Tasks</th><th>Bounty Pool</th>
            </tr>
          </thead>
          <tbody>
            {(data.projects || []).map((project) => (
              <tr key={project.id}>
                <td>{project.name}</td>
                <td>{project.health || "—"}</td>
                <td>{(data.teamAssignments || []).filter((a) => a.project === project.id).length}</td>
                <td>{(data.tasks || []).filter((t) => t.project === project.id).length}</td>
                <td>{"₹" + money(
                  (data.tasks || [])
                    .filter((t) => t.project === project.id)
                    .reduce((sum, t) => sum + Number(t.bounty || 0), 0),
                )}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

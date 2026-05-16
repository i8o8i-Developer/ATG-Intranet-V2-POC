import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle, Briefcase, CheckCircle, ChevronDown, ChevronUp,
  Clock, FileText, Info, Menu, MoreHorizontal, Search, Target,
  TrendingUp, Users, X, Zap,
} from "lucide-react";

import { EmptyState, MilestoneRail, Modal, Panel, Progress, SimpleTable, Tabs } from "./Shared/ScreenComponents.jsx";
import { apiPatch, apiPost } from "../Api/Client.js";
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
          items={[["team", "Team"], ["goals", "Goals"], ["org", "Org Chart"], ["sanity", "Project Sanity"], ["finance", "Project Finance"]]}
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
                      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <strong>{deptName}</strong>
                        {(() => {
                          const lead = rows.find((e) => !e.manager) || rows.find((e) => e.manager && (data.employees || []).some((m) => String(m.id) === String(e.manager) && rows.some((r) => String(r.id) === String(m.id)))) || rows[0];
                          return lead ? <span className="Hrms-Dept-Lead" style={{ fontSize: 11, color: "#64748b" }}>Lead: {employeeName(data, lead.id)}</span> : null;
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
      {tab === "org"     && <OrgChartView data={data} employeeName={employeeName} />}
      {tab === "sanity"  && <ProjectSanity  data={data} />}
      {tab === "finance" && <ProjectFinance data={data} reload={reload} />}

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
    } catch {}
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
      setShowSkillMenu(false);
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
                    {goal.status !== "InProgress" && goal.status !== "Completed" && goal.status !== "Approved" && <button className="Soft-Button Small" onClick={async () => { await apiPatch(`/Users/Goals/${goal.id}/`, { status: "InProgress" }); if (reload) reload(["goals", "goalFeedback"]); }}>Start</button>}
                    {goal.status === "InProgress" && <button className="Soft-Button Small" onClick={async () => { await apiPatch(`/Users/Goals/${goal.id}/`, { status: "Completed" }); if (reload) reload(["goals", "goalFeedback"]); }}>Complete</button>}
                    {goal.status === "Completed" && <button className="Soft-Button Small" onClick={async () => { await apiPost("/Users/GoalFeedback/", { goal: goal.id, feedback_type: "ManagerApproval", rating: 5, note: "Goal Approved." }); await apiPatch(`/Users/Goals/${goal.id}/`, { status: "Approved" }); if (reload) reload(["goals", "goalFeedback"]); }}>Approve</button>}
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
  const [expandedGoal, setExpandedGoal] = useState(null);

  return (
    <Modal onClose={onClose} wide title={`${employee.display_name} Goals`}>
      <div className="Eod-Tab-Body">
        {goals.length ? (
          <div style={{ display: "grid", gap: 8 }}>
            {goals.map((goal) => {
              const progress = goal.metadata?.progress ?? 0;
              const goalFeedback = feedback.filter((item) => String(item.goal) === String(goal.id));
              const progressUpdates = goalFeedback.filter((f) => f.feedback_type === "ProgressUpdate");
              const isOpen = expandedGoal === goal.id;
              return (
                <div key={goal.id} style={{ border: "1px solid #e2e8f0", borderRadius: 8, overflow: "hidden" }}>
                  <button onClick={() => setExpandedGoal(isOpen ? null : goal.id)} style={{ width: "100%", textAlign: "left", padding: "10px 14px", background: "#f8fafc", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 13 }}>
                    <div style={{ flex: 1 }}>
                      <strong>{goal.title}</strong>
                      <span style={{ marginLeft: 8, color: "#64748b" }}>{goal.status} · Due {formatDate(goal.due_on)}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: progress >= 100 ? "#10b981" : "#3b82f6" }}>{progress}%</span>
                      <span style={{ fontSize: 11, color: "#94a3b8" }}>{goalFeedback.length} feedback</span>
                      {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </button>
                  {isOpen && (
                    <div style={{ padding: "10px 14px" }}>
                      <div style={{ marginBottom: 8, height: 6, background: "#e2e8f0", borderRadius: 3, overflow: "hidden" }}>
                        <div style={{ width: `${progress}%`, height: "100%", background: progress >= 100 ? "#10b981" : "#3b82f6", borderRadius: 3 }} />
                      </div>
                      {goal.description && <p style={{ fontSize: 12, color: "#64748b", marginBottom: 8 }}>{goal.description}</p>}
                      {progressUpdates.length > 0 && (
                        <div>
                          <strong style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase" }}>Progress Updates</strong>
                          {progressUpdates.slice().reverse().map((fb) => (
                            <div key={fb.id} style={{ fontSize: 12, padding: "6px 0", borderBottom: "1px solid #f1f5f9" }}>
                              <p style={{ margin: 0 }}>{fb.note}</p>
                              <small style={{ color: "#94a3b8" }}>{formatDate(fb.created_at)}</small>
                            </div>
                          ))}
                        </div>
                      )}
                      {!progressUpdates.length && <small style={{ color: "#94a3b8" }}>No progress notes yet.</small>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
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
    } catch {}
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

/* ─── Org Chart View ─────────────────────────────────────────── */
function OrgChartView({ data, employeeName }) {
  const employees = data.employees || [];
  const grouped = {};
  employees.forEach((emp) => {
    const deptName = emp.department_name || "Unknown";
    if (!grouped[deptName]) grouped[deptName] = { name: deptName, members: [] };
    grouped[deptName].members.push(emp);
  });
  const sortedDepts = Object.values(grouped).sort((a, b) => a.name.localeCompare(b.name));
  const totalCount = employees.length;
  const deptCount = sortedDepts.length;
  const managerCount = employees.filter((e) => employees.some((sub) => String(sub.manager) === String(e.id))).length;

  return (
    <div style={{ padding: "20px 0" }}>
      {/* KPI Summary */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Employees", value: totalCount, color: "#3b82f6" },
          { label: "Departments", value: deptCount, color: "#8b5cf6" },
          { label: "Managers", value: managerCount, color: "#10b981" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, padding: "14px 18px", display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: `${color}15`, display: "flex", alignItems: "center", justifyContent: "center", color, fontWeight: 700, fontSize: 18 }}>{value}</div>
            <span style={{ fontSize: 13, color: "#64748b", fontWeight: 500 }}>{label}</span>
          </div>
        ))}
      </div>

      {/* Department Cards */}
      {sortedDepts.map((dept) => {
        const leads = dept.members.filter((e) => dept.members.some((sub) => String(sub.manager) === String(e.id)));
        const nonLeads = dept.members.filter((e) => !leads.some((l) => String(l.id) === String(e.id)));
        return (
          <div key={dept.name} style={{ marginBottom: 16, border: "1px solid #e2e8f0", borderRadius: 12, overflow: "hidden", background: "#fff" }}>
            <div style={{ padding: "14px 18px", background: "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)", borderBottom: "1px solid #e2e8f0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: "#3b82f615", display: "flex", alignItems: "center", justifyContent: "center", color: "#3b82f6", fontWeight: 700, fontSize: 14 }}>{dept.members.length}</div>
                <strong style={{ fontSize: 15, color: "#0f172a" }}>{dept.name}</strong>
              </div>
              {leads.length > 0 && (
                <div style={{ fontSize: 12, color: "#64748b", display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#f59e0b" }} />
                  Lead: {leads.map((l) => l.display_name).join(", ")}
                </div>
              )}
            </div>
            <div style={{ padding: "14px 18px", display: "flex", flexWrap: "wrap", gap: 10 }}>
              {dept.members.map((emp) => {
                const isLead = leads.some((l) => String(l.id) === String(emp.id));
                const managerName = emp.manager ? employeeName(data, emp.manager) : null;
                const ic = (emp.display_name || "?").split(" ").map((p) => p[0]).join("").slice(0, 2).toUpperCase();
                const colors = ["#6366f1","#0ea5e9","#10b981","#f59e0b","#ec4899","#8b5cf6","#14b8a6","#f97316"];
                const ac = colors[emp.id ? emp.id % colors.length : 0];
                return (
                  <div key={emp.id} style={{ padding: "12px 14px", background: "#f8fafc", border: isLead ? "1.5px solid #f59e0b" : "1px solid #e2e8f0", borderRadius: 10, minWidth: 180, flex: "1 0 auto", maxWidth: 240, position: "relative" }}>
                    {isLead && <span style={{ position: "absolute", top: -1, right: 12, fontSize: 10, fontWeight: 600, color: "#f59e0b", background: "#fff", padding: "0 4px" }}>LEAD</span>}
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                      <span style={{ width: 32, height: 32, borderRadius: "50%", background: ac, color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, flexShrink: 0 }}>{ic}</span>
                      <div style={{ minWidth: 0 }}>
                        <strong style={{ display: "block", fontSize: 13, color: "#0f172a", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{emp.display_name}</strong>
                        <span style={{ fontSize: 11, color: "#64748b" }}>{emp.position_title || emp.employment_type || "—"}</span>
                      </div>
                    </div>
                    {emp.joined_on && <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 4 }}>Joined {formatDate(emp.joined_on)}</div>}
                    {managerName && !isLead && <div style={{ fontSize: 11, color: "#94a3b8" }}>Reports to: <span style={{ color: "#64748b" }}>{managerName}</span></div>}
                    {emp.employee_code && <div style={{ fontSize: 10, color: "#cbd5e1", marginTop: 4 }}>{emp.employee_code}</div>}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
      {!employees.length && <div style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>No Employees Found.</div>}
    </div>
  );
}

/* ─── Project Sanity ──────────────────────────────────────────── */
function ProjectSanity({ data }) {
  const byProject = groupBy(data.milestones || [], (m) => String(m.project));
  const byTaskProject = groupBy(data.tasks || [], (t) => String(t.project));
  return (
    <div className="HS" style={{ display: "grid", gap: 16 }}>
      {/* Summary KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {[
          { label: "Total Projects", value: (data.projects || []).length, color: "#3b82f6" },
          { label: "Active Milestones", value: (data.milestones || []).filter((m) => !isCompleted(m.status)).length, color: "#f59e0b" },
          { label: "Completed Milestones", value: (data.milestones || []).filter((m) => isCompleted(m.status)).length, color: "#10b981" },
          { label: "Open Alerts", value: (data.alerts || []).filter((a) => a.status !== "Resolved").length, color: "#ef4444" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: `${color}15`, display: "flex", alignItems: "center", justifyContent: "center", color, fontWeight: 700, fontSize: 16 }}>{value}</div>
            <div><span style={{ fontSize: 12, color: "#64748b" }}>{label}</span></div>
          </div>
        ))}
      </div>

      {/* Project Cards */}
      {(data.projects || []).map((project) => {
        const milestones = byProject.get(String(project.id)) || [];
        const tasks = byTaskProject.get(String(project.id)) || [];
        const done = milestones.filter((m) => isCompleted(m.status)).length;
        const taskDone = tasks.filter((t) => isCompleted(t.status)).length;
        const pct = milestones.length ? Math.round((done / milestones.length) * 100) : 0;
        const taskPct = tasks.length ? Math.round((taskDone / tasks.length) * 100) : 0;
        const alerts = (data.alerts || []).filter((a) => String(a.project) === String(project.id));
        const delays = (data.delays || []).filter((d) => String(d.item_id) === String(project.id));
        return (
          <div key={project.id} style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, overflow: "hidden" }}>
            {/* Project Header */}
            <div style={{ padding: "14px 18px", background: "#f8fafc", borderBottom: "1px solid #e2e8f0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ padding: "3px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600, background: project.priority === "P1" ? "#fef2f2" : "#f8fafc", color: project.priority === "P1" ? "#dc2626" : "#64748b" }}>{project.priority || "P3"}</span>
                <strong style={{ fontSize: 15 }}>{project.name}</strong>
                <span style={{ fontSize: 12, color: "#64748b" }}>{project.project_type || "—"}</span>
                <span style={{ padding: "2px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600, background: project.health === "Good" || project.health === "OnTrack" ? "#f0fdf4" : project.health === "Watch" || project.health === "Escalated" ? "#fef2f2" : "#f8fafc", color: project.health === "Good" || project.health === "OnTrack" ? "#16a34a" : project.health === "Watch" || project.health === "Escalated" ? "#dc2626" : "#64748b" }}>{project.health || "Unknown"}</span>
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                {project.starts_on && <span style={{ fontSize: 11, color: "#94a3b8" }}>{formatDate(project.starts_on)} → {formatDate(project.ends_on)}</span>}
              </div>
            </div>

            {/* Progress Bars */}
            <div style={{ padding: "12px 18px", borderBottom: "1px solid #e2e8f0", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}><span style={{ color: "#64748b" }}>Milestones ({done}/{milestones.length})</span><strong>{pct}%</strong></div>
                <div style={{ height: 6, background: "#e2e8f0", borderRadius: 3, overflow: "hidden" }}><div style={{ width: `${pct}%`, height: "100%", background: pct === 100 ? "#10b981" : "#3b82f6", borderRadius: 3 }} /></div>
              </div>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}><span style={{ color: "#64748b" }}>Tasks ({taskDone}/{tasks.length})</span><strong>{taskPct}%</strong></div>
                <div style={{ height: 6, background: "#e2e8f0", borderRadius: 3, overflow: "hidden" }}><div style={{ width: `${taskPct}%`, height: "100%", background: taskPct === 100 ? "#10b981" : "#8b5cf6", borderRadius: 3 }} /></div>
              </div>
            </div>

            {/* Details Row */}
            <div style={{ padding: "12px 18px", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              <div style={{ textAlign: "center" }}><span style={{ display: "block", fontSize: 18, fontWeight: 700, color: "#0f172a" }}>{(data.teamAssignments || []).filter((a) => String(a.project) === String(project.id)).length}</span><span style={{ fontSize: 11, color: "#94a3b8" }}>Team</span></div>
              <div style={{ textAlign: "center" }}><span style={{ display: "block", fontSize: 18, fontWeight: 700, color: "#0f172a" }}>{tasks.reduce((s, t) => s + Math.max(0, Number(t.bounty || 0)), 0)}</span><span style={{ fontSize: 11, color: "#94a3b8" }}>Bounty</span></div>
              <div style={{ textAlign: "center" }}><span style={{ display: "block", fontSize: 18, fontWeight: 700, color: alerts.length > 0 ? "#ef4444" : "#10b981" }}>{alerts.length}</span><span style={{ fontSize: 11, color: "#94a3b8" }}>Alerts</span></div>
              <div style={{ textAlign: "center" }}><span style={{ display: "block", fontSize: 18, fontWeight: 700, color: delays.length > 0 ? "#f59e0b" : "#10b981" }}>{delays.length}</span><span style={{ fontSize: 11, color: "#94a3b8" }}>Delays</span></div>
            </div>

            {/* Alerts List */}
            {alerts.length > 0 && <div style={{ padding: "8px 18px 12px", borderTop: "1px solid #e2e8f0" }}>
              <span style={{ fontSize: 11, color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>Recent Alerts</span>
              {alerts.slice(0, 3).map((a) => (
                <div key={a.id} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, padding: "4px 0" }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: a.severity === "High" || a.severity === "Critical" ? "#ef4444" : a.severity === "Warning" ? "#f59e0b" : "#10b981" }} />
                  <span>{a.title}</span>
                  <span style={{ marginLeft: "auto", color: "#94a3b8" }}>{a.severity}</span>
                </div>
              ))}
            </div>}
          </div>
        );
      })}
      {!(data.projects || []).length && <div style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>No Projects Found.</div>}
    </div>
  );
}

/* ─── Project Finance ─────────────────────────────────────────── */
function ProjectFinance({ data, reload }) {
  const [expandedRows, setExpandedRows] = useState({});
  const [financeBonus, setFinanceBonus] = useState({});
  const [financeError, setFinanceError] = useState("");
  const [selectedDept, setSelectedDept] = useState("all");
  const employees = data.employees || [];
  const tasks = data.tasks || [];
  const payProfiles = data.payProfiles || [];
  const bankAccounts = data.bankAccounts || [];
  const assignMap = indexById(data.teamAssignments || []);

  const toggleExpand = (id) => setExpandedRows((prev) => ({ ...prev, [id]: !prev[id] }));

  const rows = [];
  const seen = new Set();
  (data.teamAssignments || []).forEach((ta) => {
    const emp = employees.find((e) => String(e.id) === String(ta.employee));
    if (!emp || seen.has(String(emp.id))) return;
    seen.add(String(emp.id));
    const pay = payProfiles.find((p) => String(p.employee) === String(emp.id));
    const empTasks = tasks.filter((t) => String(t.owner || t.owner_id) === String(emp.id));
    const totalBounty = empTasks.reduce((s, t) => s + Math.max(0, Number(t.bounty || 0)), 0);
    const completedBounty = empTasks.filter((t) => isCompleted(t.status)).reduce((s, t) => s + Math.max(0, Number(t.bounty || 0)), 0);
    const hasBank = bankAccounts.some((b) => String(b.employee) === String(emp.id) && b.verification_status === "Verified");
    const assign = assignMap.get(String(emp.id));
    rows.push({
      id: emp.id,
      name: emp.display_name || "-",
      dept: emp.department_name || "-",
      basePay: Number(pay?.base_pay || 0),
      payPerTask: Number(pay?.pay_per_task || 0),
      payType: pay?.pay_type || "N/A",
      bounty: totalBounty,
      completedBounty,
      taskCount: empTasks.length,
      hasBank,
      empType: emp.employment_type || "-",
      role: assign?.role || "Member",
    });
  });

  const departments = ["all", ...new Set(rows.map((r) => r.dept).filter(Boolean))];
  const filteredRows = selectedDept === "all" ? rows : rows.filter((r) => r.dept === selectedDept);

  const totalBase = filteredRows.reduce((s, r) => s + r.basePay, 0);
  const totalBountyAll = filteredRows.reduce((s, r) => s + r.bounty, 0);
  const totalBonusAll = Object.values(financeBonus).reduce((s, v) => s + (Number(v) || 0), 0);

  return (
    <div className="HF">
      {financeError && <div style={{ fontSize: 13, padding: "8px 14px", marginBottom: 12, borderRadius: 6, background: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca" }}>{financeError}</div>}

      {/* Department Dropdown */}
      <div style={{ marginBottom: 16, display: "flex", alignItems: "center", gap: 10 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: "#475569", whiteSpace: "nowrap" }}>Department:</label>
        <select value={selectedDept} onChange={(e) => setSelectedDept(e.target.value)}
          style={{ minWidth: 180, padding: "6px 10px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 13, background: "#fff" }}>
          {departments.map((d) => (
            <option key={d} value={d}>{d === "all" ? "All Departments" : d}</option>
          ))}
        </select>
      </div>

      {/* KPI Summary */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
        {[
          { label: "Total Employees", value: filteredRows.length, color: "#3b82f6" },
          { label: "Total Base Pay", value: `₹${totalBase.toLocaleString()}`, color: "#10b981" },
          { label: "Total Bounty Pool", value: `₹${totalBountyAll.toLocaleString()}`, color: "#f59e0b" },
          { label: "Total With Bonus", value: `₹${(totalBase + totalBountyAll + totalBonusAll).toLocaleString()}`, color: "#8b5cf6" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, padding: 12, display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: `${color}15`, display: "flex", alignItems: "center", justifyContent: "center", color, fontWeight: 700 }}>{typeof value === "number" ? value : "₹"}</div>
            <div><div style={{ fontSize: 16, fontWeight: 700, color: "#0f172a" }}>{value}</div><div style={{ fontSize: 11, color: "#64748b" }}>{label}</div></div>
          </div>
        ))}
      </div>

      {/* Employee Finance Table */}
      <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
              <th style={{ padding: "10px 12px", textAlign: "left", fontWeight: 600, color: "#475569" }}>Name</th>
              <th style={{ padding: "10px 12px", textAlign: "left", fontWeight: 600, color: "#475569" }}>Department</th>
              <th style={{ padding: "10px 12px", textAlign: "left", fontWeight: 600, color: "#475569" }}>Type</th>
              <th style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: "#475569" }}>Base Pay</th>
              <th style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: "#475569" }}>Per Task Pay</th>
              <th style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: "#475569" }}>Bounty</th>
              <th style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: "#475569" }}>Bonus</th>
              <th style={{ padding: "10px 12px", textAlign: "right", fontWeight: 600, color: "#475569" }}>Total</th>
              <th style={{ padding: "10px 12px", textAlign: "center", fontWeight: 600, color: "#475569" }}>Bank</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row, i) => {
              const bonus = Number(financeBonus[row.id] || 0);
              const total = row.basePay + row.bounty + bonus;
              return (
                <React.Fragment key={row.id}>
                  <tr style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "#fff" : "#fafafa", cursor: "pointer" }} onClick={() => toggleExpand(row.id)}>
                    <td style={{ padding: "8px 12px", fontWeight: 500 }}>{row.name}</td>
                    <td style={{ padding: "8px 12px", color: "#64748b" }}>{row.dept}</td>
                    <td style={{ padding: "8px 12px" }}><span style={{ padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600, background: row.empType === "Intern" ? "#eef2ff" : row.empType === "Full-Time" ? "#f0fdf4" : "#fefce8", color: row.empType === "Intern" ? "#3b82f6" : row.empType === "Full-Time" ? "#16a34a" : "#ca8a04" }}>{row.empType}</span></td>
                    <td style={{ padding: "8px 12px", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>₹{row.basePay.toLocaleString()}</td>
                    <td style={{ padding: "8px 12px", textAlign: "right", color: "#64748b" }}>₹{row.payPerTask.toLocaleString()}</td>
                    <td style={{ padding: "8px 12px", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>₹{row.bounty.toLocaleString()}</td>
                    <td style={{ padding: "8px 12px", textAlign: "right" }}>
                      <input type="number" min="0" value={financeBonus[row.id] || 0} onClick={(e) => e.stopPropagation()} onChange={(e) => setFinanceBonus({ ...financeBonus, [row.id]: e.target.value })} style={{ width: 70, padding: "4px 6px", border: "1px solid #e2e8f0", borderRadius: 4, fontSize: 12, textAlign: "right" }} />
                    </td>
                    <td style={{ padding: "8px 12px", textAlign: "right", fontWeight: 600, color: "#059669" }}>₹{total.toLocaleString()}</td>
                    <td style={{ padding: "8px 12px", textAlign: "center" }}>{row.hasBank ? <span style={{ color: "#10b981" }}>✓</span> : <span style={{ color: "#ef4444" }}>✗</span>}</td>
                  </tr>
                  {expandedRows[row.id] && (
                    <tr><td colSpan="9" style={{ padding: "12px 16px", background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                        <div><strong style={{ fontSize: 12, color: "#64748b", textTransform: "uppercase" }}>Payment Details</strong>
                          <div style={{ marginTop: 6, display: "grid", gap: 4, fontSize: 13 }}>
                            <div><span style={{ color: "#64748b" }}>Role: </span>{row.role}</div>
                            <div><span style={{ color: "#64748b" }}>Pay Type: </span>{row.payType}</div>
                            <div><span style={{ color: "#64748b" }}>Base Pay: </span>₹{row.basePay.toLocaleString()}</div>
                            <div><span style={{ color: "#64748b" }}>Per Task Pay: </span>₹{row.payPerTask}</div>
                            <div><span style={{ color: "#64748b" }}>Bounty Tasks: </span>{row.taskCount} ({row.completedBounty} completed)</div>
                          </div>
                        </div>
                        <div><strong style={{ fontSize: 12, color: "#64748b", textTransform: "uppercase" }}>Payment History</strong>
                          <div style={{ marginTop: 6, fontSize: 13, color: "#94a3b8" }}>No Previous Payment Data Available.</div>
                        </div>
                      </div>
                    </td></tr>
                  )}
                </React.Fragment>
              );
            })}
            {!filteredRows.length && <tr><td colSpan="9" style={{ padding: 24, textAlign: "center", color: "#94a3b8" }}>No Employees Found For Selected Department.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import React, { useEffect, useMemo, useState } from "react";
import {
  Bell,
  CalendarDays,
  ClipboardCheck,
  ChevronDown,
  ChevronRight,
  CircleAlert,
  ClipboardList,
  Clock3,
  Check,
} from "lucide-react";


import { apiPatch, apiPost } from "../Api/Client.js";
import "../Styles/HomeScreen.css";
import { Modal } from "./Shared/ScreenComponents.jsx";
import {
  avatar,
  employeeName,
  filterForEmployee,
  findById,
  findDailyStatus,
  formatDate,
  getAttendanceStatus,
  groupBy,
  indexById,
  isCompleted,
  isoDate,
  lastDays,
  money,
  resolveActiveEmployee,
} from "./Shared/ScreenUtils.jsx";

export function HomeScreen({ data, selectedEmployeeId, reload, navigate }) {
  const user = data.me?.user || data.me?.account || data.me || {};
  const linkedEmployee = resolveActiveEmployee(data);
  const employee = findById(data.employees, linkedEmployee?.id || selectedEmployeeId) || linkedEmployee || data.employees?.[0];
  const useWorkspaceScope = !linkedEmployee?.id;
  const employeeTasks = useMemo(() => (useWorkspaceScope ? data.tasks || [] : filterForEmployee(data.tasks, employee?.id)), [useWorkspaceScope, data.tasks, employee?.id]);
  const pendingTasks = useMemo(() => employeeTasks.filter((task) => !isCompleted(task.status)), [employeeTasks]);
  const completedTasks = useMemo(() => employeeTasks.filter((task) => isCompleted(task.status)), [employeeTasks]);
  const pendingCompliance = (data.assessmentAssignments || []).filter((item) => (useWorkspaceScope || String(item.employee) === String(employee?.id)) && !isCompleted(item.status));
  const unread = (data.notifications || []).filter((item) => !item.is_read);
  const [expandedTaskId, setExpandedTaskId] = useState("");
  const [taskFilter, setTaskFilter] = useState("pending");
  const [collapsedProjects, setCollapsedProjects] = useState({});
  const [summary, setSummary] = useState("");
  const [goalNotes, setGoalNotes] = useState({});
  const [goalNotesOpen, setGoalNotesOpen] = useState({});
  const [delayTask, setDelayTask] = useState(null);
  const projectMap = useMemo(() => indexById(data.projects), [data.projects]);
  const days = useMemo(() => lastDays(15), []);
  const filteredTasks = taskFilter === "completed" ? completedTasks : pendingTasks;
  const expandedTask = filteredTasks.find((task) => String(task.id) === String(expandedTaskId));
  const visibleGroups = useMemo(() => groupBy(filteredTasks, (task) => projectMap.get(String(task.project))?.name || "Intranet"), [filteredTasks, projectMap]);
  const primaryNotification = unread[0] || data.notifications?.[0];
  const totalTasks = employeeTasks.length;
  const myEmployeeId = linkedEmployee?.id || selectedEmployeeId;
  const overdueTasks = employeeTasks.filter((task) => {
    if (isCompleted(task.status) || !task.due_at) return false;
    if (useWorkspaceScope && String(task.owner || task.owner_id) !== String(myEmployeeId)) return false;
    const dueDate = new Date(task.due_at);
    return !Number.isNaN(dueDate.getTime()) && dueDate < new Date();
  }).length;

  useEffect(() => {
    if (!filteredTasks.length) {
      setExpandedTaskId("");
      return;
    }
    if (!filteredTasks.some((task) => String(task.id) === String(expandedTaskId))) {
      setExpandedTaskId(String(filteredTasks[0].id));
    }
  }, [filteredTasks]);

  const submitEod = async () => {
    const employeeId = expandedTask?.owner || expandedTask?.owner_id || employee?.id;
    if (!employeeId || !summary.trim()) return;
    await apiPost("/TasksDashboard/DailyStatusEntries/submit/", {
      employee: employeeId,
      summary,
      status_date: isoDate(new Date()),
      metadata: { source: "React Home", task_id: expandedTaskId },
    });
    setSummary("");
    setExpandedTaskId("");
    reload(["dailyStatus", "tasks", "notifications", "employees"]);
  };

  const quickLinks = [
    { label: "Getting Started", onClick: () => navigate("/docs/") },
  ];

  const statusTone = (status = "") => {
    const normalized = String(status).toLowerCase();
    if (isCompleted(normalized)) return "green";
    if (normalized.includes("progress") || normalized.includes("review") || normalized.includes("working")) return "blue";
    if (normalized.includes("overdue") || normalized.includes("blocked") || normalized.includes("hold")) return "red";
    return "slate";
  };

  const attendanceTone = (entry) => {
    const raw = String(entry?.status || entry?.attendance_status || entry?.metadata?.status || "").toLowerCase();
    if (raw.includes("leave")) return "leave";
    if (entry) return "present";
    return "absent";
  };

  const attendanceLabel = (entry) => {
    const tone = attendanceTone(entry);
    if (tone === "leave") return "On Leave";
    if (tone === "present") return "Present";
    return "Absent";
  };

  const toggleProject = (name) => {
    setCollapsedProjects((current) => ({ ...current, [name]: !current[name] }));
  };

  return (
    <section className="HomeR">
      <div className="HomeR-NotifCard">
        <div className="HomeR-NotifCard-header">
          <span className="HomeR-NotifCard-title"><Bell size={18} /> Notifications</span>
          <ChevronDown size={18} />
        </div>
        <div className="HomeR-NotifBanner">
          <span>{primaryNotification?.title || primaryNotification?.message || ""}</span>
          <button type="button" onClick={() => navigate("/notifications/")}>Review</button>
        </div>
      </div>

      <div className="HomeR-DashGrid">
        <div className="HomeR-Card">
          <div className="HomeR-Card-header">
            <span className="HomeR-Card-title">Attendance Overview <small>(Last 15 Days)</small></span>
          </div>
          <div className="HomeR-AttGrid">
            {days.map((day) => {
              const { type, entry } = getAttendanceStatus(data.dailyStatus, data.leaveRequests, employee?.id, day.iso);
              return (
                <span key={day.iso} className={`HomeR-AttDay ${type}`} title={`${day.iso} · ${type === "present" ? "Present" : type === "leave" ? "On Leave" : "Absent"}`}>
                  {day.label}
                </span>
              );
            })}
          </div>
          <div className="HomeR-AttLegend">
            <span><i className="present" /> Present</span>
            <span><i className="absent" /> Absent</span>
            <span><i className="leave" /> On Leave</span>
          </div>
        </div>

        <div className="HomeR-SideStack">
          <div className="HomeR-Card">
            <div className="HomeR-Card-header">
              <span className="HomeR-Card-title">Quick Links</span>
            </div>
            <div className="HomeR-QuickLinks">
              {quickLinks.map((link) => (
                <button key={link.label} type="button" className="HomeR-QuickLink" onClick={link.onClick}>
                  <span>{link.label}</span>
                  <ChevronRight size={18} />
                </button>
              ))}
            </div>
          </div>

          <div className="HomeR-SummaryGrid">
            <article className="HomeR-SummaryCard">
              <div className="HomeR-SummaryIcon Blue"><ClipboardList size={20} /></div>
              <div>
                <small>Total Tasks</small>
                <strong>{totalTasks}</strong>
              </div>
            </article>
            <article className="HomeR-SummaryCard">
              <div className="HomeR-SummaryIcon Green"><ClipboardCheck size={20} /></div>
              <div>
                <small>Completed</small>
                <strong>{completedTasks.length}</strong>
              </div>
            </article>
            <article className="HomeR-SummaryCard">
              <div className="HomeR-SummaryIcon Red"><Clock3 size={20} /></div>
              <div>
                <small>Overdue</small>
                <strong>{overdueTasks}</strong>
              </div>
            </article>
          </div>
        </div>
      </div>

      {/* Upcoming Leaves & Work Anniversaries */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        {/* My Upcoming Approved Leaves */}
        {(() => {
          const myEmpId = linkedEmployee?.id || selectedEmployeeId;
          const upcoming = (data.leaveRequests || []).filter((lr) => String(lr.status).toLowerCase() === "approved" && lr.starts_on && String(lr.employee) === String(myEmpId)).sort((a, b) => new Date(a.starts_on) - new Date(b.starts_on)).slice(0, 4);
          if (!upcoming.length) return null;
          return (
            <div className="HomeR-Card">
              <div className="HomeR-Card-header"><span className="HomeR-Card-title">My Upcoming Leaves</span></div>
              <div style={{ padding: "8px 14px 14px" }}>
                {upcoming.map((lr) => (
                  <div key={lr.id} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, padding: "4px 0" }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#f59e0b" }} />
                    <span style={{ flex: 1 }}>{formatDate(lr.starts_on)} - {formatDate(lr.ends_on)}</span>
                    <span style={{ color: "#64748b", fontSize: 11 }}>{lr.leave_type || "Leave"}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}
      </div>

      {/* My Goals */}
      {(() => {
        const empId = linkedEmployee?.id || selectedEmployeeId;
        const myGoals = (data.goals || []).filter((g) => String(g.employee) === String(empId) && !isCompleted(g.status)).slice(0, 5);
        if (!myGoals.length) return null;
        return (
          <div className="HomeR-Card" style={{ marginBottom: 16 }}>
            <div className="HomeR-Card-header"><span className="HomeR-Card-title">My Goals</span></div>
            <div style={{ display: "grid", gap: 6, padding: "8px 14px 14px" }}>
              {myGoals.map((goal) => {
                const noteOpen = goalNotesOpen[goal.id];
                return (
                  <div key={goal.id} style={{ display: "flex", flexDirection: "column", padding: "10px 12px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <div style={{ flex: 1 }}>
                        <strong style={{ fontSize: 13 }}>{goal.title}</strong>
                        <span style={{ fontSize: 11, color: "#64748b", marginLeft: 8 }}>{goal.status} · Due {formatDate(goal.due_on)}</span>
                      </div>
                      <button className="Soft-Button Small" onClick={() => setGoalNotesOpen((prev) => ({ ...prev, [goal.id]: !prev[goal.id] }))} style={{ fontSize: 10, padding: "2px 6px" }} title="Add Progress Note">{noteOpen ? "✕" : "📝"}</button>
                    </div>
                    {noteOpen && (
                      <div style={{ marginTop: 8, display: "flex", gap: 6, alignItems: "flex-start" }}>
                        <textarea value={goalNotes[goal.id] || ""} onChange={(e) => setGoalNotes((prev) => ({ ...prev, [goal.id]: e.target.value }))} placeholder="Describe This Progress Update..." rows={2} style={{ flex: 1, fontSize: 12, padding: "6px 8px", borderRadius: 6, border: "1px solid #e2e8f0", resize: "vertical", minHeight: 40 }} />
                        <button className="Primary-Button Small" onClick={async () => { const txt = (goalNotes[goal.id] || "").trim(); if (!txt) return; await apiPost("/Users/GoalFeedback/", { goal: goal.id, feedback_type: "ProgressUpdate", note: txt }); setGoalNotes((prev) => ({ ...prev, [goal.id]: "" })); setGoalNotesOpen((prev) => ({ ...prev, [goal.id]: false })); reload(["goalFeedback"]); }} style={{ whiteSpace: "nowrap" }}>Save</button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* Pending Assessments */}
      {(() => {
        const empId = linkedEmployee?.id || selectedEmployeeId;
        const myAssessments = (data.assessmentAssignments || []).filter((a) => String(a.employee) === String(empId) && !isCompleted(a.status)).slice(0, 5);
        if (!myAssessments.length) return null;
        return (
          <div className="HomeR-Card" style={{ marginBottom: 16 }}>
            <div className="HomeR-Card-header"><span className="HomeR-Card-title">Pending Assessments</span></div>
            <div style={{ display: "grid", gap: 6, padding: "8px 14px 14px" }}>
              {myAssessments.map((a) => (
                <div key={a.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0" }}>
                  <div style={{ flex: 1 }}>
                    <strong style={{ fontSize: 13 }}>{a.assessment_title || "Assessment"}</strong>
                    <span style={{ fontSize: 11, color: "#64748b", marginLeft: 8 }}>{a.status} · Due {formatDate(a.due_at)}</span>
                  </div>
                  <span className="Table-Actions">
                    <button className="Soft-Button Small" onClick={() => navigate("/assessment/")}>View</button>
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      <div className="HomeR-Toolbar">
        <label>
          <span>Filter By Status</span>
          <select value={taskFilter} onChange={(event) => setTaskFilter(event.target.value)}>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
          </select>
        </label>
        <div className="HomeR-ToolbarMeta">
          <span><CircleAlert size={15} /> {unread.length} Unread Notifications</span>
          <span><ClipboardList size={15} /> {pendingCompliance.length} Pending Compliance</span>
        </div>
      </div>

      <div className="HomeR-Card HomeR-TaskCard">
        <table className="HomeR-Table">
          <thead>
            <tr>
              <th>Assigned Task</th>
              <th>Bounty</th>
              <th>Status</th>
              <th>Due Date</th>
              <th>Assignee</th>
              <th>Delay</th>
            </tr>
          </thead>
          <tbody>
            {Array.from(visibleGroups.entries()).map(([name, tasks]) => {
              const isCollapsed = Boolean(collapsedProjects[name]);
              return (
                <React.Fragment key={name}>
                  <tr className="HomeR-ProjectRow">
                    <td colSpan="6">
                      <button type="button" className="HomeR-ProjectToggle" onClick={() => toggleProject(name)}>
                        {isCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                        <strong>{name}</strong>
                      </button>
                    </td>
                  </tr>
                  {!isCollapsed && tasks.map((task) => {
                    const selected = String(expandedTaskId) === String(task.id);
                    const completed = isCompleted(task.status);
                    return (
                      <React.Fragment key={task.id}>
                        <tr className={selected ? "HomeR-TaskRow active" : "HomeR-TaskRow"}>
                          <td>
                            <button className={selected ? "HomeR-TaskCheck active" : completed ? "HomeR-TaskCheck active done" : "HomeR-TaskCheck"} onClick={() => setExpandedTaskId(selected ? "" : String(task.id))}>
                              <Check size={14} />
                            </button>
                            <span className="HomeR-TaskName">{task.title}</span>
                          </td>
                          <td>{money(task.bounty)}</td>
                          <td><span className={`status-pill ${statusTone(task.status)}`}>{task.status || "Not Started"}</span></td>
                          <td><span className="HomeR-DateCell"><CalendarDays size={15} /> {task.due_at ? formatDate(task.due_at) : "Not Set"}</span></td>
                          <td>{avatar(employeeName(data, task.owner || task.owner_id) || employee?.display_name)}</td>
                          <td><button className="Soft-Button Small" onClick={() => setDelayTask(task)} title="Report Delay"><Clock3 size={14} /></button></td>
                        </tr>
                        {selected && !completed && (
                          <tr className="HomeR-InlineEditor">
                            <td colSpan="6">
                              <div className="HomeR-EditorShell">
                                <strong>Update EOD Report For This Task</strong>
                                <textarea value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="What Did You Do Today On This Task?" />
                                <div className="HomeR-EditorActions">
                                  <button className="Primary-Button" onClick={submitEod}>Update EOD Report</button>
                                  <button className="Outline-Button" onClick={() => { setExpandedTaskId(""); setSummary(""); }}>Cancel</button>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
        {!filteredTasks.length && <div className="HomeR-Empty">No Tasks Found For This Filter.</div>}
      </div>
      {delayTask && (
        <Modal title="Report Delay" onClose={() => setDelayTask(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const me = data.me?.user || data.me?.account || data.me || {};
            const myProfile = (data.employees || []).find((emp) => String(emp.user) === String(me.id));
            if (!myProfile) return;
            const days = Number(e.target.delay_days.value);
            const reason = e.target.reason.value;
            await apiPost("/Project/ProjectDelays/", {
              delay_type: "Task",
              item_id: delayTask.id,
              project: delayTask.project,
              task: delayTask.id,
              delay_days: days,
              reason,
              reported_by: myProfile.id,
            });
            setDelayTask(null);
            reload(["projectDelays"]);
          }}>
            <p style={{ fontSize: 14, marginBottom: 12, color: "#374151" }}>Task: <strong>{delayTask.title}</strong></p>
            <div className="Form-Grid Two" style={{ marginBottom: 12 }}>
              <label>Delay Days<input type="number" name="delay_days" min="1" defaultValue={1} required /></label>
            </div>
            <label>Reason<textarea name="reason" rows={3} required /></label>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="Primary-Button" type="submit">Submit Delay</button>
              <button className="Outline-Button" type="button" onClick={() => setDelayTask(null)}>Cancel</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}

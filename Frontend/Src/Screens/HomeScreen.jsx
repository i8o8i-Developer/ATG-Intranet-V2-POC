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
  EllipsisVertical,
} from "lucide-react";


import { apiPost } from "../Api/Client.js";
import {
  avatar,
  employeeName,
  filterForEmployee,
  findById,
  findDailyStatus,
  formatDate,
  groupBy,
  indexById,
  isCompleted,
  isoDate,
  lastDays,
  money,
} from "./Shared/ScreenUtils.jsx";
import { AlarmIcon, TaskListIcon } from "../Components/icons/icons.jsx";

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
  const projectMap = useMemo(() => indexById(data.projects), [data.projects]);
  const days = useMemo(() => lastDays(15), []);
  const filteredTasks = taskFilter === "completed" ? completedTasks : pendingTasks;
  const expandedTask = filteredTasks.find((task) => String(task.id) === String(expandedTaskId));
  const visibleGroups = useMemo(() => groupBy(filteredTasks, (task) => projectMap.get(String(task.project))?.name || "Intranet"), [filteredTasks, projectMap]);
  const primaryNotification = unread[0] || data.notifications?.[0];
  const totalTasks = employeeTasks.length;
  const overdueTasks = employeeTasks.filter((task) => {
    if (isCompleted(task.status) || !task.due_at) return false;
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
  }, [filteredTasks, expandedTaskId]);

  const submitEod = async () => {
    const employeeId = expandedTask?.owner || expandedTask?.owner_id || employee?.id;
    if (!employeeId || !summary.trim()) return;
    await apiPost("/TasksDashboard/DailyStatusEntries/submit/", {
      employee: employeeId,
      summary,
      status_date: isoDate(new Date()),
      metadata: { source: "react-home", task_id: expandedTaskId },
    });
    setSummary("");
    reload();
  };

  const quickLinks = [
    { label: "Getting started", onClick: () => navigate("/docs/") },
    { label: "Onboarding", onClick: () => navigate("/Project/onboarding/") },
    { label: "Workflow reports", onClick: () => navigate("/workflow/") },
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
    if (tone === "leave") return "On leave";
    if (tone === "present") return "Present";
    return "Absent";
  };

  const toggleProject = (name) => {
    setCollapsedProjects((current) => ({ ...current, [name]: !current[name] }));
  };

  return (
    <section className="screen-stack home-screen-redesign">
      {/* <section className="home-shell-card">
        <div className="home-page-title">
          <h1>Home</h1>
          <p>{useWorkspaceScope ? "Workspace overview" : employee?.display_name || "Employee dashboard"}</p>
        </div>
      </section> */}

      <section className="home-mock-panel">
        <div className="home-card home-notification-card">
          <div className="home-card-header">
            <span className="home-card-title"><Bell size={18} /> Notifications</span>
            <ChevronDown size={18} />
          </div>
          <div className="home-notification-banner">
            <span>{primaryNotification?.title || primaryNotification?.message || "You have been added to a new project ( Intranet )"}</span>
            <button type="button" onClick={() => navigate("/notifications/")}>Review</button>
          </div>
        </div>

        <div className="home-dashboard-grid">
          <div className="home-card">
            <div className="home-card-header">
              <span className="home-card-title">Attendance Overview <small>(last 15 days)</small></span>
            </div>
            <div className="home-attendance-grid">
              {days.map((day) => {
                const status = findDailyStatus(data.dailyStatus, employee?.id, day.iso);
                const tone = attendanceTone(status);
                return (
                  <span key={day.iso} className={`home-attendance-day ${tone}`} title={`${day.iso} · ${attendanceLabel(status)}`}>
                    {day.label}
                  </span>
                );
              })}
            </div>
            <div className="home-attendance-legend">
              <span><i className="present" /> Present</span>
              <span><i className="absent" /> Absent</span>
              <span><i className="leave" /> On leave</span>
            </div>
          </div>

          <div className="home-side-stack">
            <div className="home-card">
              <div className="home-card-header">
                <span className="home-card-title">Quick links</span>
              </div>
              <div className="home-quick-links-list">
                {quickLinks.map((link) => (
                  <button key={link.label} type="button" className="home-quick-link" onClick={link.onClick}>
                    <span>{link.label}</span>
                    <ChevronRight size={18} />
                  </button>
                ))}
              </div>
            </div>

            <div className="home-summary-grid">
              <article className="home-summary-card">
                <span className="home-summary-icon blue"><ClipboardList size={18} /></span>
                <div>
                  <small>Total tasks</small>
                  <strong>{totalTasks}</strong>
                </div>
              </article>
              <article className="home-summary-card">
                <span className="home-summary-icon green"><ClipboardCheck size={18} /></span>
                <div>
                  <small>Completed</small>
                  <strong>{completedTasks.length}</strong>
                </div>
              </article>
              <article className="home-summary-card">
                <span className="home-summary-icon red"><Clock3 size={18} /></span>
                <div>
                  <small>Overdue</small>
                  <strong>{overdueTasks}</strong>
                </div>
              </article>
            </div>
          </div>
        </div>

        <div className="home-task-toolbar">
          <label>
            <span>Filter by status</span>
            <select value={taskFilter} onChange={(event) => setTaskFilter(event.target.value)}>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
            </select>
          </label>
          <div className="home-toolbar-meta">
            <span><CircleAlert size={15} /> {unread.length} unread notifications</span>
            <span><ClipboardList size={15} /> {pendingCompliance.length} pending compliance</span>
          </div>
        </div>

        <div className="home-card home-task-table-card">
          <table className="erp-table home-task-table">
            <thead>
              <tr>
                <th>Assigned Task</th>
                <th>Bounty</th>
                <th>Status</th>
                <th>Due date</th>
                <th>Assignee</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {Array.from(visibleGroups.entries()).map(([name, tasks]) => {
                const isCollapsed = Boolean(collapsedProjects[name]);
                return (
                  <React.Fragment key={name}>
                    <tr className="home-project-row">
                      <td colSpan="6">
                        <button type="button" className="home-project-toggle" onClick={() => toggleProject(name)}>
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
                          <tr className={selected ? "home-task-row active" : "home-task-row"}>
                            <td>
                              <button className={selected ? "check active home-task-check" : completed ? "check active done home-task-check" : "check home-task-check"} onClick={() => setExpandedTaskId(String(task.id))}>
                                <Check size={16} />
                              </button>
                              <span className="home-task-name">{task.title}</span>
                            </td>
                            <td>{money(task.bounty)}</td>
                            <td><span className={`status-pill ${statusTone(task.status)}`}>{task.status || "Not started"}</span></td>
                            <td><span className="home-date-cell"><CalendarDays size={15} /> {task.due_at ? formatDate(task.due_at) : "Not set"}</span></td>
                            <td>{avatar(employeeName(data, task.owner || task.owner_id) || employee?.display_name)}</td>
                            <td><button type="button" className="home-more-button" onClick={() => setExpandedTaskId(String(task.id))}><EllipsisVertical size={16} /></button></td>
                          </tr>
                          {selected && !completed && (
                            <tr className="inline-editor home-inline-editor">
                              <td colSpan="6">
                                <div className="home-editor-shell">
                                  <strong>Update EOD report for this task</strong>
                                  <textarea value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="What did you do today on this task?" />
                                  <div className="home-editor-actions">
                                    <button className="primary-button" onClick={submitEod}>Update EOD Report</button>
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
          {!filteredTasks.length && <div className="empty-state">No tasks found for this filter.</div>}
        </div>
      </section>
    </section>
  );
}

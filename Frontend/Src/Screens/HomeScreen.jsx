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
  Check,
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
      metadata: { source: "React Home", task_id: expandedTaskId },
    });
    setSummary("");
    reload();
  };

  const quickLinks = [
    { label: "Getting Started", onClick: () => navigate("/docs/") },
    { label: "Onboarding", onClick: () => navigate("/Project/onboarding/") },
    { label: "Workflow Reports", onClick: () => navigate("/workflow/") },
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
    <section className="Screen-Stack Home-Screen-Redesign">
      <section className="Home-Mock-Panel">
        <div className="Home-Card Home-Notification-Card">
          <div className="Home-Card-Header">
            <span className="Home-Card-Title"><Bell size={18} /> Notifications</span>
            <ChevronDown size={18} />
          </div>
          <div className="Home-Notification-Banner">
            <span>{primaryNotification?.title || primaryNotification?.message || "You Have Been Added To A New Project ( Intranet )"}</span>
            <button type="button" onClick={() => navigate("/notifications/")}>Review</button>
          </div>
        </div>

        <div className="Home-Dashboard-Grid">
          <div className="Home-Card">
            <div className="Home-Card-Header">
              <span className="Home-Card-Title">Attendance Overview <small>(Last 15 Days)</small></span>
            </div>
            <div className="Home-Attendance-Grid">
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
            <div className="Home-Attendance-Legend">
              <span><i className="present" /> Present</span>
              <span><i className="absent" /> Absent</span>
              <span><i className="leave" /> On Leave</span>
            </div>
          </div>

          <div className="Home-Side-Stack">
            <div className="Home-Card">
              <div className="Home-Card-Header">
                <span className="Home-Card-Title">Quick Links</span>
              </div>
              <div className="Home-Quick-Links-List">
                {quickLinks.map((link) => (
                  <button key={link.label} type="button" className="Home-Quick-Link" onClick={link.onClick}>
                    <span>{link.label}</span>
                    <ChevronRight size={18} />
                  </button>
                ))}
              </div>
            </div>

            <div className="Home-Summary-Grid">
              <article className="Home-Summary-Card">
                <span className="Home-Summary-Icon Blue"><ClipboardList size={18} /></span>
                <div>
                  <small>Total Tasks</small>
                  <strong>{totalTasks}</strong>
                </div>
              </article>
              <article className="Home-Summary-Card">
                <span className="Home-Summary-Icon Green"><ClipboardCheck size={18} /></span>
                <div>
                  <small>Completed</small>
                  <strong>{completedTasks.length}</strong>
                </div>
              </article>
              <article className="Home-Summary-Card">
                <span className="Home-Summary-Icon Red"><Clock3 size={18} /></span>
                <div>
                  <small>Overdue</small>
                  <strong>{overdueTasks}</strong>
                </div>
              </article>
            </div>
          </div>
        </div>

        <div className="Home-Task-Toolbar">
          <label>
            <span>Filter By Status</span>
            <select value={taskFilter} onChange={(event) => setTaskFilter(event.target.value)}>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
            </select>
          </label>
          <div className="Home-Toolbar-Meta">
            <span><CircleAlert size={15} /> {unread.length} Unread Notifications</span>
            <span><ClipboardList size={15} /> {pendingCompliance.length} Pending Compliance</span>
          </div>
        </div>

        <div className="Home-Card Home-Task-Table-Card">
          <table className="Erp-Table Home-Task-Table">
            <thead>
              <tr>
                <th>Assigned Task</th>
                <th>Bounty</th>
                <th>Status</th>
                <th>Due Date</th>
                <th>Assignee</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {Array.from(visibleGroups.entries()).map(([name, tasks]) => {
                const isCollapsed = Boolean(collapsedProjects[name]);
                return (
                  <React.Fragment key={name}>
                    <tr className="Home-Project-Row">
                      <td colSpan="6">
                        <button type="button" className="Home-Project-Toggle" onClick={() => toggleProject(name)}>
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
                          <tr className={selected ? "Home-Task-Row Active" : "Home-Task-Row"}>
                            <td>
                              <button className={selected ? "Check Active Home-Task-Check" : completed ? "Check Active Done Home-Task-Check" : "Check Home-Task-Check"} onClick={() => setExpandedTaskId(String(task.id))}>
                                <Check size={16} />
                              </button>
                              <span className="Home-Task-Name">{task.title}</span>
                            </td>
                            <td>{money(task.bounty)}</td>
                            <td><span className={`status-pill ${statusTone(task.status)}`}>{task.status || "Not Started"}</span></td>
                            <td><span className="Home-Date-Cell"><CalendarDays size={15} /> {task.due_at ? formatDate(task.due_at) : "Not Set"}</span></td>
                            <td>{avatar(employeeName(data, task.owner || task.owner_id) || employee?.display_name)}</td>
                            <td><button type="button" className="Home-More-Button" onClick={() => setExpandedTaskId(String(task.id))}><EllipsisVertical size={16} /></button></td>
                          </tr>
                          {selected && !completed && (
                            <tr className="Inline-Editor Home-Inline-Editor">
                              <td colSpan="6">
                                <div className="Home-Editor-Shell">
                                  <strong>Update EOD Report For This Task</strong>
                                  <textarea value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="What Did You Do Today On This Task?" />
                                  <div className="Home-Editor-Actions">
                                    <button className="Primary-Button" onClick={submitEod}>Update EOD Report</button>
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
          {!filteredTasks.length && <div className="Empty-State">No Tasks Found For This Filter.</div>}
        </div>
      </section>
    </section>
  );
}

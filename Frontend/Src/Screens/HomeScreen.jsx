import React, { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

import { apiPost } from "../Api/Client.js";
import { Disclosure, EmptyState, Panel, StatCard } from "./Shared/ScreenComponents.jsx";
import {
  avatar,
  employeeName,
  filterForEmployee,
  findById,
  findDailyStatus,
  groupBy,
  humanDate,
  indexById,
  isCompleted,
  isoDate,
  lastDays,
  money,
  projectName,
} from "./Shared/ScreenUtils.jsx";

export function HomeScreen({ data, selectedEmployeeId, reload, navigate }) {
  const user = data.me?.user || data.me?.account || data.me || {};
  const linkedEmployee = data.me?.employees?.[0] || (data.employees || []).find((item) => String(item.user) === String(user.id));
  const employee = findById(data.employees, linkedEmployee?.id || selectedEmployeeId) || linkedEmployee || data.employees?.[0];
  const useWorkspaceScope = !linkedEmployee?.id;
  const employeeTasks = useWorkspaceScope ? data.tasks || [] : filterForEmployee(data.tasks, employee?.id);
  const pendingTasks = employeeTasks.filter((task) => !isCompleted(task.status));
  const pendingCompliance = (data.assessmentAssignments || []).filter((item) => (useWorkspaceScope || String(item.employee) === String(employee?.id)) && !isCompleted(item.status));
  const unread = (data.notifications || []).filter((item) => !item.is_read);
  const [expandedTaskId, setExpandedTaskId] = useState("");
  const [summary, setSummary] = useState("");
  const projectMap = useMemo(() => indexById(data.projects), [data.projects]);
  const days = useMemo(() => lastDays(15), []);
  const expandedTask = pendingTasks.find((task) => String(task.id) === String(expandedTaskId));
  const greetingName = linkedEmployee?.display_name || user.username || employee?.display_name || "Intranet";
  const headingTag = linkedEmployee ? "Employee Home" : "Live Workspace Overview";
  const attendanceSubtitle = useWorkspaceScope ? `Snapshot For ${employee?.display_name || "Connected Employee"}` : "Last 15 Days";
  const taskSubtitle = useWorkspaceScope ? "Showing Live Tasks From The Connected Backend." : `Showing Work For ${employee?.display_name || "Connected Employee"}`;

  useEffect(() => {
    if (!expandedTaskId && pendingTasks.length) setExpandedTaskId(String(pendingTasks[0].id));
  }, [pendingTasks, expandedTaskId]);

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

  const grouped = groupBy(pendingTasks, (task) => projectMap.get(String(task.project))?.name || "Intranet");

  return (
    <section className="screen-stack">
      <section className="hero-panel">
        <div>
          <h1>Hello, {greetingName}</h1>
          <strong>{headingTag}</strong>
          <p>{humanDate(new Date())}</p>
        </div>
      </section>
      <div className="stat-grid four">
        <StatCard label="Unread Notifications" value={unread.length} />
        <StatCard label="Pending Tasks" value={pendingTasks.length} />
        <StatCard label="Pending Compliance" value={pendingCompliance.length} />
        <StatCard label="Open Assessments" value={useWorkspaceScope ? (data.assessmentAssignments || []).filter((item) => !isCompleted(item.status)).length : pendingCompliance.length} />
      </div>
      <Disclosure title="Notifications" subtitle={unread.length ? `${unread.length} Unread` : "No Unread Notifications"} defaultOpen>
        {(data.notifications || []).slice(0, 6).map((item) => (
          <div className="notice-row" key={item.id}>
            <div><strong>{item.title}</strong><p>{item.message}</p><span>{item.created_at}</span></div>
            <button className="soft-button">Review</button>
          </div>
        ))}
        {!data.notifications?.length && <EmptyState label="No Notifications Loaded From Backend." />}
      </Disclosure>
      <Panel title="Attendance Overview" subtitle={attendanceSubtitle}>
        <div className="attendance-strip">
          {days.map((day) => {
            const status = findDailyStatus(data.dailyStatus, employee?.id, day.iso);
            return <span key={day.iso} className={status ? "att present" : "att missing"}>{day.label}</span>;
          })}
        </div>
      </Panel>
      <section className="action-links"><button onClick={() => navigate("/workflow/")}>Workflow Reports</button><button onClick={() => navigate("/Project/onboarding/")}>Onboarding</button><button onClick={() => navigate("/docs/")}>Getting Started</button></section>
      <Panel title="Assigned Tasks" subtitle={taskSubtitle} right={<select><option>Pending</option><option>Completed</option></select>}>
        <table className="erp-table task-table">
          <thead><tr><th>Select</th><th>Assigned Task</th><th>Bounty</th><th>Status</th><th>Due Date</th><th>Assignee</th></tr></thead>
          <tbody>
            {Array.from(grouped.entries()).map(([name, tasks]) => (
              <React.Fragment key={name}>
                <tr className="group-row"><td><ChevronDown size={15} /></td><td colSpan="5"><strong>{name}</strong></td></tr>
                {tasks.map((task) => (
                  <React.Fragment key={task.id}>
                    <tr>
                      <td><button className={String(expandedTaskId) === String(task.id) ? "check active" : "check"} onClick={() => setExpandedTaskId(String(task.id))}><Check size={17} /></button></td>
                      <td>{task.title}</td><td>{money(task.bounty)}</td><td>{task.status}</td><td>{task.due_at ? task.due_at : "None"}</td><td>{avatar(employeeName(data, task.owner || task.owner_id) || employee?.display_name)}</td>
                    </tr>
                    {String(expandedTaskId) === String(task.id) && (
                      <tr className="inline-editor"><td />
                        <td colSpan="5"><textarea value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="What Did You Do Today On This Task?" /><button className="primary-button" onClick={submitEod}>Update EOD Report</button></td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        {!pendingTasks.length && <EmptyState label="No Assigned Pending Tasks Returned By The Backend." />}
      </Panel>
    </section>
  );
}